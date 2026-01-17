"""
Granada v2 Search Module
Full-text search with FTS5 and Arabic text normalization
"""
import re
import sqlite3
from typing import List, Dict, Any, Optional


def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text for search indexing and querying.

    Performs:
    - Remove tashkeel (diacritics/harakat)
    - Normalize alef variants (أإآا → ا)
    - Normalize alef maqsura (ى → ي)
    - Normalize ta marbuta for search (ة → ه)
    - Normalize hamza variants
    """
    if not text:
        return ''

    # Remove tashkeel (Arabic diacritics)
    # Unicode range for Arabic diacritics: U+064B to U+065F
    tashkeel_pattern = re.compile(r'[\u064B-\u065F\u0670]')
    text = tashkeel_pattern.sub('', text)

    # Remove tatweel (kashida)
    text = text.replace('\u0640', '')

    # Normalize alef variants to bare alef
    alef_variants = {
        '\u0623': '\u0627',  # أ → ا (alef with hamza above)
        '\u0625': '\u0627',  # إ → ا (alef with hamza below)
        '\u0622': '\u0627',  # آ → ا (alef with madda)
        '\u0671': '\u0627',  # ٱ → ا (alef wasla)
    }
    for variant, replacement in alef_variants.items():
        text = text.replace(variant, replacement)

    # Normalize alef maqsura to ya
    text = text.replace('\u0649', '\u064A')  # ى → ي

    # Normalize ta marbuta to ha (for search matching)
    text = text.replace('\u0629', '\u0647')  # ة → ه

    # Normalize hamza variants
    hamza_variants = {
        '\u0624': '\u0648',  # ؤ → و (waw with hamza)
        '\u0626': '\u064A',  # ئ → ي (ya with hamza)
    }
    for variant, replacement in hamza_variants.items():
        text = text.replace(variant, replacement)

    return text


def highlight_matches(text: str, query: str, max_length: int = 200) -> str:
    """
    Highlight search matches in text with <mark> tags.
    Returns a snippet around the first match.
    """
    if not text or not query:
        return text[:max_length] if text else ''

    # Normalize both for matching
    text_normalized = normalize_arabic(text.lower())
    query_normalized = normalize_arabic(query.lower())

    # Find the position of the match in normalized text
    match_pos = text_normalized.find(query_normalized)

    if match_pos == -1:
        # No match found, return beginning of text
        return text[:max_length] + ('...' if len(text) > max_length else '')

    # Calculate snippet boundaries
    context_before = 50
    context_after = 100

    start = max(0, match_pos - context_before)
    end = min(len(text), match_pos + len(query) + context_after)

    snippet = text[start:end]

    # Add ellipsis if truncated
    if start > 0:
        snippet = '...' + snippet
    if end < len(text):
        snippet = snippet + '...'

    # Now highlight the actual query in the snippet
    # We need to find where the query appears in the original text
    # Use case-insensitive search on normalized text
    snippet_normalized = normalize_arabic(snippet.lower())
    query_pos_in_snippet = snippet_normalized.find(query_normalized)

    if query_pos_in_snippet != -1:
        # Find the actual text at this position (may have diacritics)
        # We need to highlight the corresponding original characters
        original_start = query_pos_in_snippet

        # Count how many characters in original text correspond to normalized position
        # This is approximate but works for most cases
        highlighted = (
            snippet[:original_start] +
            '<mark>' +
            snippet[original_start:original_start + len(query) + 5] +  # +5 for potential diacritics
            '</mark>' +
            snippet[original_start + len(query) + 5:]
        )
        return highlighted

    return snippet


class SearchEngine:
    """FTS5-based search engine for Arabic text."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Get database connection with timeout for concurrency."""
        conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=30000')
        return conn

    def index_page(self, book_id: str, page_num: int, content: str):
        """Index a single page in FTS5."""
        normalized_content = normalize_arabic(content)

        conn = self._get_connection()
        cursor = conn.cursor()

        # Update the pages table
        cursor.execute('''
            INSERT OR REPLACE INTO pages (book_id, page_num, content, content_normalized)
            VALUES (?, ?, ?, ?)
        ''', (book_id, page_num, content, normalized_content))

        # Update FTS5 index
        cursor.execute('''
            INSERT INTO pages_fts (book_id, page_num, content)
            VALUES (?, ?, ?)
        ''', (book_id, str(page_num), normalized_content))

        conn.commit()
        conn.close()

    def index_book(self, book_id: str, pages: List[Dict[str, Any]]):
        """Index all pages of a book in FTS5."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Clear existing index for this book
        cursor.execute('DELETE FROM pages_fts WHERE book_id = ?', (book_id,))
        cursor.execute('DELETE FROM pages WHERE book_id = ?', (book_id,))

        # Insert all pages
        for page in pages:
            page_num = page['page_num']
            content = page['content']
            normalized_content = normalize_arabic(content)

            cursor.execute('''
                INSERT INTO pages (book_id, page_num, content, content_normalized)
                VALUES (?, ?, ?, ?)
            ''', (book_id, page_num, content, normalized_content))

            cursor.execute('''
                INSERT INTO pages_fts (book_id, page_num, content)
                VALUES (?, ?, ?)
            ''', (book_id, str(page_num), normalized_content))

        conn.commit()
        conn.close()

    def search(
        self,
        query: str,
        book_ids: Optional[List[str]] = None,
        author_ids: Optional[List[str]] = None,
        category_ids: Optional[List[int]] = None,
        page: int = 1,
        limit: int = 20,
        precision: str = 'all',
        simplify: bool = True,
        full_result: bool = False,
        highlight: bool = True
    ) -> Dict[str, Any]:
        """
        Search for query across all indexed content.

        Args:
            query: Search query (will be normalized if simplify=True)
            book_ids: Filter by specific book IDs
            author_ids: Filter by author IDs
            category_ids: Filter by category IDs
            page: Page number for pagination
            limit: Results per page
            precision: Search precision mode:
                - 'some': OR search, matches if ANY word appears
                - 'all': AND search, matches if ALL words appear (default)
                - 'phrase': Exact phrase match
            simplify: Apply Arabic normalization (strip diacritics, normalize alif)
            full_result: Show extended context around matches
            highlight: Highlight matching terms in results

        Returns:
            Dict with results, total count, and pagination info
        """
        if not query or not query.strip():
            return {'results': [], 'total': 0, 'page': page, 'pages': 0}

        # Normalize the query if simplify is enabled
        query_clean = query.strip()
        if simplify:
            normalized_query = normalize_arabic(query_clean)
        else:
            normalized_query = query_clean

        conn = self._get_connection()
        cursor = conn.cursor()

        # Build FTS5 query based on precision mode
        fts_query = self._build_fts_query(normalized_query, precision)

        # Base query with FTS5 search
        sql = '''
            SELECT
                p.id,
                p.book_id,
                p.page_num,
                p.content,
                b.title as book_title,
                a.name as author_name,
                a.death_date as author_death,
                c.name as category_name,
                bm25(pages_fts) as rank
            FROM pages_fts
            JOIN pages p ON pages_fts.book_id = p.book_id AND CAST(pages_fts.page_num AS INTEGER) = p.page_num
            JOIN books b ON p.book_id = b.id
            LEFT JOIN authors a ON b.author_id = a.id
            LEFT JOIN categories c ON b.category_id = c.id
            WHERE pages_fts MATCH ?
        '''

        params = [f'"{fts_query}"']

        # Add filters
        if book_ids:
            placeholders = ','.join('?' * len(book_ids))
            sql += f' AND p.book_id IN ({placeholders})'
            params.extend(book_ids)

        if author_ids:
            placeholders = ','.join('?' * len(author_ids))
            sql += f' AND b.author_id IN ({placeholders})'
            params.extend(author_ids)

        if category_ids:
            placeholders = ','.join('?' * len(category_ids))
            sql += f' AND b.category_id IN ({placeholders})'
            params.extend(category_ids)

        # Get total count
        count_sql = f'SELECT COUNT(*) FROM ({sql})'
        cursor.execute(count_sql, params)
        total = cursor.fetchone()[0]

        # Add ordering and pagination
        sql += ' ORDER BY rank'
        sql += ' LIMIT ? OFFSET ?'
        params.extend([limit, (page - 1) * limit])

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Format results
        results = []
        snippet_length = 400 if full_result else 200
        for row in rows:
            if highlight:
                snippet = highlight_matches(row['content'], query, max_length=snippet_length)
            else:
                # No highlighting, just truncate
                content = row['content']
                snippet = content[:snippet_length] + ('...' if len(content) > snippet_length else '')

            results.append({
                'id': row['id'],
                'book_id': row['book_id'],
                'book_title': row['book_title'],
                'author': row['author_name'],
                'author_death': row['author_death'],
                'category': row['category_name'],
                'page': row['page_num'],
                'snippet': snippet
            })

        # Save to search history
        self._save_search_history(query, total)

        conn.close()

        total_pages = (total + limit - 1) // limit

        return {
            'results': results,
            'total': total,
            'page': page,
            'pages': total_pages
        }

    def _build_fts_query(self, query: str, precision: str) -> str:
        """
        Build FTS5 query string based on precision mode.

        Args:
            query: The normalized search query
            precision: 'some' (OR), 'all' (AND), or 'phrase'

        Returns:
            FTS5-compatible query string
        """
        # Escape quotes for FTS5
        query = query.replace('"', '""')

        # Split into words
        words = query.split()

        if not words:
            return f'"{query}"'

        if precision == 'phrase':
            # Exact phrase match - wrap entire query in quotes
            return f'"{query}"'

        elif precision == 'some':
            # OR search - any word matches
            # FTS5 OR syntax: word1 OR word2 OR word3
            return ' OR '.join(f'"{w}"' for w in words)

        else:  # 'all' (default)
            # AND search - all words must match
            # FTS5 AND syntax: word1 AND word2 AND word3
            # Or just space-separated words (implicit AND in FTS5)
            return ' '.join(f'"{w}"' for w in words)

    def _save_search_history(self, query: str, results_count: int):
        """Save search query to history."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO search_history (query, results_count)
            VALUES (?, ?)
        ''', (query, results_count))

        # Keep only last 50 searches
        cursor.execute('''
            DELETE FROM search_history
            WHERE id NOT IN (
                SELECT id FROM search_history ORDER BY searched_at DESC LIMIT 50
            )
        ''')

        conn.commit()
        conn.close()

    def get_search_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent search history."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT query, MAX(searched_at) as searched_at, MAX(results_count) as results_count
            FROM search_history
            GROUP BY query
            ORDER BY MAX(searched_at) DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [{'id': i, 'query': row['query']} for i, row in enumerate(rows, 1)]

    def rebuild_index(self):
        """Rebuild the entire FTS5 index from pages table."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Clear existing FTS index
        cursor.execute('DELETE FROM pages_fts')

        # Repopulate from pages table
        cursor.execute('''
            INSERT INTO pages_fts (book_id, page_num, content)
            SELECT book_id, CAST(page_num AS TEXT), content_normalized
            FROM pages
            WHERE content_normalized IS NOT NULL
        ''')

        conn.commit()
        conn.close()
