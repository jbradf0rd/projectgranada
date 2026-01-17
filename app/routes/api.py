"""
Granada v2 API Routes
"""
from flask import Blueprint, jsonify, request, current_app
from app.search import SearchEngine
from app.models import get_db_connection
from app.book_upload import BookUploader, BOOK_FORMAT_HELP

api_bp = Blueprint('api', __name__)


def get_search_engine():
    """Get search engine instance."""
    return SearchEngine(current_app.config['DATABASE_PATH'])


def get_db():
    """Get database connection."""
    return get_db_connection(current_app.config['DATABASE_PATH'])


def get_book_uploader():
    """Get book uploader instance."""
    return BookUploader(current_app.config['DATABASE_PATH'])


# ============================================================================
# FILTERS
# ============================================================================

@api_bp.route('/filters')
def get_filters():
    """Get all filter options for search."""
    conn = get_db()
    cursor = conn.cursor()

    # Get books
    cursor.execute('''
        SELECT id, title FROM books WHERE is_downloaded = 1
        ORDER BY title
    ''')
    books = [{'id': row['id'], 'title': row['title']} for row in cursor.fetchall()]

    # Get authors
    cursor.execute('''
        SELECT id, name FROM authors ORDER BY death_date
    ''')
    authors = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]

    # Get categories
    cursor.execute('''
        SELECT id, name FROM categories ORDER BY id
    ''')
    categories = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'books': books,
        'authors': authors,
        'categories': categories
    })


# ============================================================================
# SEARCH
# ============================================================================

@api_bp.route('/search')
def search():
    """Full-text search across all books."""
    query = request.args.get('q', '')
    books = request.args.get('books', '')
    authors = request.args.get('authors', '')
    categories = request.args.get('categories', '')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)

    # New turath-style search options
    precision = request.args.get('precision', 'all')  # 'some', 'all', 'phrase'
    simplify = request.args.get('simplify', 'true').lower() == 'true'
    full_result = request.args.get('full_result', 'false').lower() == 'true'
    highlight = request.args.get('highlight', 'true').lower() == 'true'

    if not query:
        return jsonify({'results': [], 'total': 0, 'page': page, 'pages': 0})

    # Parse filter lists
    book_ids = [b.strip() for b in books.split(',') if b.strip()] if books else None
    author_ids = [a.strip() for a in authors.split(',') if a.strip()] if authors else None
    category_ids = [int(c.strip()) for c in categories.split(',') if c.strip()] if categories else None

    # Perform search with precision options
    search_engine = get_search_engine()
    results = search_engine.search(
        query=query,
        book_ids=book_ids,
        author_ids=author_ids,
        category_ids=category_ids,
        page=page,
        limit=limit,
        precision=precision,
        simplify=simplify,
        full_result=full_result,
        highlight=highlight
    )

    return jsonify(results)


@api_bp.route('/search/history')
def search_history():
    """Get recent search history."""
    search_engine = get_search_engine()
    history = search_engine.get_search_history(limit=10)
    return jsonify({'history': history})


# ============================================================================
# BOOKS
# ============================================================================

@api_bp.route('/books')
def get_books():
    """Get all books in library."""
    downloaded = request.args.get('downloaded', None)
    owned = request.args.get('owned', None)

    conn = get_db()
    cursor = conn.cursor()

    sql = '''
        SELECT b.*, a.name as author_name, c.name as category_name
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.id
        LEFT JOIN categories c ON b.category_id = c.id
        WHERE 1=1
    '''
    params = []

    if downloaded is not None:
        sql += ' AND b.is_downloaded = ?'
        params.append(1 if downloaded == 'true' else 0)

    if owned is not None:
        sql += ' AND b.is_owned = ?'
        params.append(1 if owned == 'true' else 0)

    sql += ' ORDER BY b.title'

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    books = []
    for row in rows:
        books.append({
            'id': row['id'],
            'title': row['title'],
            'author': row['author_name'],
            'author_death': row['death_date'],
            'category': row['category_name'],
            'file_size': row['file_size'],
            'is_downloaded': bool(row['is_downloaded']),
            'is_owned': bool(row['is_owned'])
        })

    return jsonify({'books': books})


@api_bp.route('/books/<book_id>')
def get_book(book_id):
    """Get single book details."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT b.*, a.name as author_name, a.bio as author_bio,
               c.name as category_name,
               (SELECT COUNT(*) FROM pages WHERE book_id = b.id) as total_pages
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.id
        LEFT JOIN categories c ON b.category_id = c.id
        WHERE b.id = ?
    ''', (book_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Book not found'}), 404

    return jsonify({
        'id': row['id'],
        'title': row['title'],
        'author': {
            'id': row['author_id'],
            'name': row['author_name'],
            'death_date': row['death_date']
        },
        'category': {
            'id': row['category_id'],
            'name': row['category_name']
        },
        'file_size': row['file_size'],
        'is_downloaded': bool(row['is_downloaded']),
        'is_owned': bool(row['is_owned']),
        'total_pages': row['total_pages'] or 0,
        'source': row['source']
    })


@api_bp.route('/books/<book_id>/card')
def get_book_card(book_id):
    """Get full book card with all metadata."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT b.*, a.name as author_display_name, a.bio as author_bio,
               c.name as category_name,
               (SELECT COUNT(*) FROM pages WHERE book_id = b.id) as total_pages,
               (SELECT COUNT(*) FROM toc_entries WHERE book_id = b.id) as toc_count
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.id
        LEFT JOIN categories c ON b.category_id = c.id
        WHERE b.id = ?
    ''', (book_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'Book not found'}), 404

    # Parse subject into hierarchy
    subject_hierarchy = []
    if row['subject']:
        parts = [p.strip() for p in row['subject'].split('::')]
        subject_hierarchy = parts

    # Build comprehensive book card
    card = {
        'id': row['id'],
        'title': row['title'],
        'subtitle': row['subtitle'],
        'alt_title': row['alt_title'],
        # Author info
        'author': {
            'id': row['author_id'],
            'name': row['author_name'] or row['author_display_name'],
            'aka': row['author_aka'],
            'born': row['author_born'],
            'death': row['death_date'],
            'bio': row['author_bio']
        },
        # Category info
        'category': {
            'id': row['category_id'],
            'name': row['category_name']
        },
        'subject': row['subject'],
        'subject_hierarchy': subject_hierarchy,
        # Edition info
        'edition': {
            'editor': row['editor'],
            'edition_number': row['edition'],
            'publisher': row['publisher'],
            'place': row['publication_place'],
            'year': row['publication_year'],
            'isbn': row['isbn']
        },
        # Book stats
        'stats': {
            'volumes': row['volumes_count'] or 1,
            'pages': row['total_pages'] or 0,
            'page_count': row['page_count'],
            'toc_entries': row['toc_count'] or 0,
            'file_size': row['file_size']
        },
        # Metadata
        'language': row['language'],
        'openiti_uri': row['openiti_uri'],
        'source': row['source'],
        'is_downloaded': bool(row['is_downloaded']),
        'is_owned': bool(row['is_owned']),
        'download_date': row['download_date']
    }

    return jsonify(card)


@api_bp.route('/books/<book_id>/pages')
def get_book_pages(book_id):
    """Get book page content. Supports single page or range query."""
    # Check for range query (start/end) or single page query
    start = request.args.get('start', type=int)
    end = request.args.get('end', type=int)
    page_num = request.args.get('page', 1, type=int)

    conn = get_db()
    cursor = conn.cursor()

    # Get total page count
    cursor.execute('''
        SELECT MAX(page_num) as total FROM pages WHERE book_id = ?
    ''', (book_id,))
    total_row = cursor.fetchone()
    total_pages = total_row['total'] if total_row and total_row['total'] else 1

    # Range query for continuous scrolling
    if start is not None and end is not None:
        cursor.execute('''
            SELECT page_num, volume, original_page, content FROM pages
            WHERE book_id = ? AND page_num >= ? AND page_num <= ?
            ORDER BY page_num
        ''', (book_id, start, end))

        pages = [{
            'page_num': row['page_num'],
            'volume': row['volume'] if row['volume'] else 1,
            'original_page': row['original_page'] if row['original_page'] else row['page_num'],
            'content': row['content']
        } for row in cursor.fetchall()]

        conn.close()

        return jsonify({
            'book_id': book_id,
            'pages': pages,
            'total_pages': total_pages,
            'start': start,
            'end': end
        })

    # Single page query (legacy support)
    cursor.execute('''
        SELECT volume, original_page, content FROM pages
        WHERE book_id = ? AND page_num = ?
    ''', (book_id, page_num))

    row = cursor.fetchone()
    conn.close()

    content = row['content'] if row else 'لم يتم العثور على المحتوى'
    volume = row['volume'] if row and row['volume'] else 1
    original_page = row['original_page'] if row and row['original_page'] else page_num

    return jsonify({
        'book_id': book_id,
        'page_num': page_num,
        'volume': volume,
        'original_page': original_page,
        'content': content,
        'total_pages': total_pages,
        'has_prev': page_num > 1,
        'has_next': page_num < total_pages
    })


@api_bp.route('/books/<book_id>/toc')
def get_book_toc(book_id):
    """Get table of contents for a book."""
    import re

    conn = get_db()
    cursor = conn.cursor()

    # Get TOC entries from database
    cursor.execute('''
        SELECT title, level, page_num, position
        FROM toc_entries
        WHERE book_id = ?
        ORDER BY position
    ''', (book_id,))

    toc = []
    # Pattern to skip: entries that are just numbers like "1 -", "123 -", etc.
    skip_pattern = re.compile(r'^\d+\s*-?\s*$')
    # Pattern to skip: page references like "[ص: 45]"
    page_ref_pattern = re.compile(r'^\[ص:\s*\d+\]$')

    for row in cursor.fetchall():
        title = row['title']

        # Skip numeric-only entries (hadith numbers, etc.)
        if skip_pattern.match(title):
            continue

        # Skip page reference entries
        if page_ref_pattern.match(title):
            continue

        # Skip very short titles
        if len(title.strip()) < 3:
            continue

        toc.append({
            'title': title,
            'level': row['level'],
            'page': row['page_num'],
            'expanded': False,
            'children': []
        })

        # Limit to 500 entries for performance
        if len(toc) >= 500:
            break

    conn.close()

    return jsonify({
        'toc': toc,
        'count': len(toc)
    })


@api_bp.route('/books/<book_id>/search')
def search_in_book(book_id):
    """Search within a specific book."""
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)

    if not query:
        return jsonify({'results': [], 'total': 0})

    conn = get_db()
    cursor = conn.cursor()

    # Use FTS5 search within this book
    from app.search import normalize_arabic
    normalized_query = normalize_arabic(query)

    cursor.execute('''
        SELECT page_num, content FROM pages
        WHERE book_id = ? AND content_normalized LIKE ?
        ORDER BY page_num
        LIMIT ?
    ''', (book_id, f'%{normalized_query}%', limit))

    results = []
    for row in cursor.fetchall():
        content = row['content']
        page_num = row['page_num']

        # Create snippet with highlight
        idx = content.lower().find(query.lower())
        if idx == -1:
            # Try normalized search
            from app.search import normalize_arabic
            norm_content = normalize_arabic(content)
            idx = norm_content.find(normalized_query)

        if idx >= 0:
            start = max(0, idx - 50)
            end = min(len(content), idx + len(query) + 50)
            snippet = content[start:end]
            if start > 0:
                snippet = '...' + snippet
            if end < len(content):
                snippet = snippet + '...'
            # Highlight the match
            snippet = snippet.replace(query, f'<mark>{query}</mark>')
        else:
            snippet = content[:100] + '...'

        results.append({
            'page': page_num,
            'snippet': snippet
        })

    conn.close()

    return jsonify({
        'results': results,
        'total': len(results),
        'query': query
    })


@api_bp.route('/books/<book_id>/download', methods=['POST'])
def download_book(book_id):
    """Download/import a book (legacy endpoint - now redirects to upload)."""
    # This endpoint is deprecated - use /api/upload/file instead
    return jsonify({
        'status': 'error',
        'message': 'استخدم صفحة رفع الكتب لإضافة كتب جديدة'
    }), 400


@api_bp.route('/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Delete a downloaded book."""
    conn = get_db()
    cursor = conn.cursor()

    # Delete pages
    cursor.execute('DELETE FROM pages WHERE book_id = ?', (book_id,))
    cursor.execute('DELETE FROM pages_fts WHERE book_id = ?', (book_id,))

    # Mark book as not downloaded
    cursor.execute('UPDATE books SET is_downloaded = 0 WHERE id = ?', (book_id,))

    conn.commit()
    conn.close()

    return jsonify({
        'status': 'success',
        'message': 'تم حذف الكتاب'
    })


@api_bp.route('/books/<book_id>', methods=['PUT'])
def update_book(book_id):
    """Update book metadata."""
    data = request.get_json()

    conn = get_db()
    cursor = conn.cursor()

    # Check if book exists
    cursor.execute('SELECT id FROM books WHERE id = ?', (book_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'الكتاب غير موجود'}), 404

    # Build update query dynamically based on provided fields
    allowed_fields = [
        'title', 'subtitle', 'alt_title', 'subject', 'language',
        'editor', 'edition', 'publisher', 'publication_place', 'publication_year', 'isbn',
        'author_name', 'author_aka', 'author_born', 'death_date',
        'volumes_count', 'page_count'
    ]

    updates = []
    params = []
    for field in allowed_fields:
        if field in data:
            updates.append(f'{field} = ?')
            params.append(data[field])

    if updates:
        params.append(book_id)
        cursor.execute(f'UPDATE books SET {", ".join(updates)} WHERE id = ?', params)
        conn.commit()

    conn.close()

    return jsonify({'status': 'success', 'message': 'تم تحديث الكتاب'})


@api_bp.route('/books/<book_id>/ownership', methods=['PUT'])
def update_book_ownership(book_id):
    """Update book ownership status."""
    data = request.get_json()
    is_owned = data.get('is_owned', False)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE books SET is_owned = ? WHERE id = ?',
        (1 if is_owned else 0, book_id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        'status': 'success',
        'is_owned': is_owned
    })


# ============================================================================
# AUTHORS
# ============================================================================

@api_bp.route('/authors')
def get_authors():
    """Get all authors."""
    search_term = request.args.get('search', '')

    conn = get_db()
    cursor = conn.cursor()

    sql = '''
        SELECT a.*, COUNT(b.id) as book_count
        FROM authors a
        LEFT JOIN books b ON a.id = b.author_id
    '''
    params = []

    if search_term:
        sql += ' WHERE a.name LIKE ?'
        params.append(f'%{search_term}%')

    sql += ' GROUP BY a.id ORDER BY a.death_date'

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    authors = [{
        'id': row['id'],
        'name': row['name'],
        'death_date': row['death_date'],
        'book_count': row['book_count']
    } for row in rows]

    return jsonify({'authors': authors})


@api_bp.route('/authors/<author_id>')
def get_author(author_id):
    """Get single author details."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM authors WHERE id = ?', (author_id,))
    author = cursor.fetchone()

    if not author:
        conn.close()
        return jsonify({'error': 'Author not found'}), 404

    cursor.execute('''
        SELECT id, title FROM books WHERE author_id = ?
    ''', (author_id,))
    books = [{'id': row['id'], 'title': row['title']} for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'id': author['id'],
        'name': author['name'],
        'death_date': author['death_date'],
        'bio': author['bio'],
        'books': books
    })


@api_bp.route('/authors/<author_id>', methods=['PUT'])
def update_author(author_id):
    """Update author information."""
    data = request.get_json()

    conn = get_db()
    cursor = conn.cursor()

    # Check if author exists
    cursor.execute('SELECT id FROM authors WHERE id = ?', (author_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'المؤلف غير موجود'}), 404

    # Build update query
    updates = []
    params = []

    if 'name' in data:
        updates.append('name = ?')
        params.append(data['name'])
    if 'death_date' in data:
        updates.append('death_date = ?')
        params.append(data['death_date'])
    if 'bio' in data:
        updates.append('bio = ?')
        params.append(data['bio'])

    if updates:
        params.append(author_id)
        cursor.execute(f'UPDATE authors SET {", ".join(updates)} WHERE id = ?', params)
        conn.commit()

    conn.close()

    return jsonify({'status': 'success', 'message': 'تم تحديث المؤلف'})


@api_bp.route('/authors/<author_id>', methods=['DELETE'])
def delete_author(author_id):
    """Delete an author and optionally reassign their books."""
    data = request.get_json() or {}
    reassign_to = data.get('reassign_to')  # Optional author_id to reassign books to

    conn = get_db()
    cursor = conn.cursor()

    # Check if author exists
    cursor.execute('SELECT id, name FROM authors WHERE id = ?', (author_id,))
    author = cursor.fetchone()
    if not author:
        conn.close()
        return jsonify({'error': 'المؤلف غير موجود'}), 404

    # Get books by this author
    cursor.execute('SELECT id FROM books WHERE author_id = ?', (author_id,))
    book_ids = [row['id'] for row in cursor.fetchall()]

    if book_ids:
        if reassign_to:
            # Reassign books to another author
            cursor.execute('UPDATE books SET author_id = ? WHERE author_id = ?', (reassign_to, author_id))
        else:
            # Set author_id to NULL for orphaned books
            cursor.execute('UPDATE books SET author_id = NULL WHERE author_id = ?', (author_id,))

    # Delete the author
    cursor.execute('DELETE FROM authors WHERE id = ?', (author_id,))

    conn.commit()
    conn.close()

    return jsonify({
        'status': 'success',
        'message': 'تم حذف المؤلف',
        'books_affected': len(book_ids)
    })


# ============================================================================
# CATEGORIES
# ============================================================================

@api_bp.route('/categories')
def get_categories():
    """Get all categories."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT c.id, c.name, COUNT(b.id) as book_count
        FROM categories c
        LEFT JOIN books b ON c.id = b.category_id AND b.is_downloaded = 1
        GROUP BY c.id
        ORDER BY c.id
    ''')
    categories = [{
        'id': row['id'],
        'name': row['name'],
        'book_count': row['book_count']
    } for row in cursor.fetchall()]

    # Get custom categories with book counts
    cursor.execute('''
        SELECT cc.id, cc.name, COUNT(bcc.book_id) as book_count
        FROM custom_categories cc
        LEFT JOIN book_custom_categories bcc ON cc.id = bcc.category_id
        LEFT JOIN books b ON bcc.book_id = b.id AND b.is_downloaded = 1
        GROUP BY cc.id
        ORDER BY cc.created_at DESC
    ''')
    custom = [{
        'id': row['id'],
        'name': row['name'],
        'book_count': row['book_count']
    } for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'categories': categories,
        'custom_categories': custom
    })


@api_bp.route('/categories', methods=['POST'])
def create_category():
    """Create a new custom category."""
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'status': 'error', 'message': 'Category name is required'}), 400

    name = data['name'].strip()
    if not name:
        return jsonify({'status': 'error', 'message': 'Category name cannot be empty'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if category already exists
    cursor.execute('SELECT id FROM custom_categories WHERE name = ?', (name,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return jsonify({
            'status': 'exists',
            'message': 'Category already exists',
            'category': {'id': existing['id'], 'name': name, 'is_custom': True}
        })

    # Create new custom category
    cursor.execute(
        'INSERT INTO custom_categories (name) VALUES (?)',
        (name,)
    )
    category_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'status': 'success',
        'category': {'id': category_id, 'name': name, 'is_custom': True}
    })


@api_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update a custom category."""
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'status': 'error', 'message': 'Category name is required'}), 400

    name = data['name'].strip()
    if not name:
        return jsonify({'status': 'error', 'message': 'Category name cannot be empty'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if it's a custom category
    cursor.execute('SELECT id FROM custom_categories WHERE id = ?', (category_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'status': 'error', 'message': 'Category not found or cannot be edited'}), 404

    # Update the category
    cursor.execute('UPDATE custom_categories SET name = ? WHERE id = ?', (name, category_id))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


@api_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a custom category with options for handling books."""
    data = request.get_json() or {}
    action = data.get('action', 'delete')  # 'delete' or 'transfer'
    transfer_to = data.get('transfer_to')  # {id: int, is_custom: bool}

    conn = get_db()
    cursor = conn.cursor()

    # Check if it's a custom category
    cursor.execute('SELECT id, name FROM custom_categories WHERE id = ?', (category_id,))
    category = cursor.fetchone()
    if not category:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Category not found or cannot be deleted'}), 404

    # Get books in this category (using book_custom_categories association)
    cursor.execute('SELECT book_id FROM book_custom_categories WHERE category_id = ?', (category_id,))
    book_ids = [row['book_id'] for row in cursor.fetchall()]

    if book_ids:
        if action == 'transfer' and transfer_to:
            # Transfer books to another category
            target_id = transfer_to.get('id')
            is_custom = transfer_to.get('is_custom', False)

            if is_custom:
                # Transfer to another custom category
                for book_id in book_ids:
                    cursor.execute('''
                        INSERT OR IGNORE INTO book_custom_categories (book_id, category_id)
                        VALUES (?, ?)
                    ''', (book_id, target_id))
            else:
                # Transfer to a main category (update books.category_id)
                cursor.execute('''
                    UPDATE books SET category_id = ? WHERE id IN ({})
                '''.format(','.join('?' * len(book_ids))), [target_id] + book_ids)

        elif action == 'delete':
            # Delete all books in this category
            for book_id in book_ids:
                # Delete pages first
                cursor.execute('DELETE FROM pages WHERE book_id = ?', (book_id,))
                # Delete from search index
                cursor.execute('DELETE FROM books_fts WHERE book_id = ?', (book_id,))
                # Delete the book
                cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))

    # Remove all book associations for this category
    cursor.execute('DELETE FROM book_custom_categories WHERE category_id = ?', (category_id,))

    # Delete the category
    cursor.execute('DELETE FROM custom_categories WHERE id = ?', (category_id,))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


@api_bp.route('/categories/<int:category_id>/books')
def get_category_books(category_id):
    """Get books in a category."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
    category = cursor.fetchone()

    if not category:
        conn.close()
        return jsonify({'error': 'Category not found'}), 404

    cursor.execute('''
        SELECT b.id, b.title, a.name as author
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.id
        WHERE b.category_id = ?
    ''', (category_id,))
    books = [{'id': row['id'], 'title': row['title'], 'author': row['author']}
             for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        'category': {'id': category['id'], 'name': category['name']},
        'books': books
    })


# ============================================================================
# COLLECTIONS
# ============================================================================

@api_bp.route('/collections')
def get_collections():
    """Get all user collections."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM collections ORDER BY created_at DESC')
    collections_data = []

    for coll in cursor.fetchall():
        # Get books in this collection
        cursor.execute('''
            SELECT b.id, b.title, rp.current_page, rp.total_pages, rp.is_complete
            FROM collection_books cb
            JOIN books b ON cb.book_id = b.id
            LEFT JOIN reading_progress rp ON b.id = rp.book_id
            WHERE cb.collection_id = ?
            ORDER BY cb.position
        ''', (coll['id'],))

        books = []
        total_progress = 0
        for book in cursor.fetchall():
            current = book['current_page'] or 1
            total = book['total_pages'] or 1
            is_complete = bool(book['is_complete'])

            books.append({
                'id': book['id'],
                'title': book['title'],
                'progress': {
                    'current_page': current,
                    'total_pages': total,
                    'is_complete': is_complete
                }
            })

            if is_complete:
                total_progress += 1
            elif total > 0:
                total_progress += current / total

        book_count = len(books)
        overall_progress = total_progress / book_count if book_count > 0 else 0

        collections_data.append({
            'id': coll['id'],
            'name': coll['name'],
            'book_count': book_count,
            'progress': round(overall_progress, 2),
            'books': books
        })

    conn.close()

    return jsonify({'collections': collections_data})


@api_bp.route('/collections', methods=['POST'])
def create_collection():
    """Create a new collection."""
    data = request.get_json()
    name = data.get('name', '')

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO collections (name) VALUES (?)', (name,))
    collection_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        'id': collection_id,
        'name': name,
        'created_at': None  # Would need to query back
    })


@api_bp.route('/collections/<int:collection_id>', methods=['PUT'])
def update_collection(collection_id):
    """Update a collection."""
    data = request.get_json()
    name = data.get('name', '')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('UPDATE collections SET name = ? WHERE id = ?', (name, collection_id))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


@api_bp.route('/collections/<int:collection_id>', methods=['DELETE'])
def delete_collection(collection_id):
    """Delete a collection."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM collection_books WHERE collection_id = ?', (collection_id,))
    cursor.execute('DELETE FROM collections WHERE id = ?', (collection_id,))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


@api_bp.route('/collections/<int:collection_id>/books', methods=['POST'])
def add_book_to_collection(collection_id):
    """Add a book to a collection."""
    data = request.get_json()
    book_id = data.get('book_id')

    if not book_id:
        return jsonify({'error': 'book_id is required'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Get next position
    cursor.execute('''
        SELECT COALESCE(MAX(position), 0) + 1 as next_pos
        FROM collection_books WHERE collection_id = ?
    ''', (collection_id,))
    next_pos = cursor.fetchone()['next_pos']

    cursor.execute('''
        INSERT OR IGNORE INTO collection_books (collection_id, book_id, position)
        VALUES (?, ?, ?)
    ''', (collection_id, book_id, next_pos))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


@api_bp.route('/collections/<int:collection_id>/books/<book_id>', methods=['DELETE'])
def remove_book_from_collection(collection_id, book_id):
    """Remove a book from a collection."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM collection_books WHERE collection_id = ? AND book_id = ?
    ''', (collection_id, book_id))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


# ============================================================================
# READING PROGRESS
# ============================================================================

@api_bp.route('/progress/<book_id>')
def get_progress(book_id):
    """Get reading progress for a book."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM reading_progress WHERE book_id = ?', (book_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({
            'book_id': book_id,
            'current_page': 1,
            'total_pages': 1,
            'last_read': None,
            'is_complete': False,
            'progress_percent': 0
        })

    total = row['total_pages'] or 1
    current = row['current_page'] or 1

    return jsonify({
        'book_id': book_id,
        'current_page': current,
        'total_pages': total,
        'last_read': row['last_read'],
        'is_complete': bool(row['is_complete']),
        'progress_percent': round(current / total, 3) if total > 0 else 0
    })


@api_bp.route('/progress/<book_id>', methods=['PUT'])
def update_progress(book_id):
    """Update reading progress."""
    data = request.get_json()
    current_page = data.get('current_page', 1)
    is_complete = data.get('is_complete', False)

    conn = get_db()
    cursor = conn.cursor()

    # Get total pages if not set
    cursor.execute('''
        SELECT MAX(page_num) as total FROM pages WHERE book_id = ?
    ''', (book_id,))
    total_row = cursor.fetchone()
    total_pages = total_row['total'] if total_row and total_row['total'] else current_page

    cursor.execute('''
        INSERT OR REPLACE INTO reading_progress
        (book_id, current_page, total_pages, last_read, is_complete)
        VALUES (?, ?, ?, datetime('now'), ?)
    ''', (book_id, current_page, total_pages, 1 if is_complete else 0))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


# ============================================================================
# SETTINGS
# ============================================================================

@api_bp.route('/settings')
def get_settings():
    """Get application settings."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT key, value FROM settings')
    rows = cursor.fetchall()
    conn.close()

    settings = {row['key']: row['value'] for row in rows}

    # Return with defaults
    return jsonify({
        'theme': settings.get('theme', 'dark'),
        'keep_screen_on': settings.get('keep_screen_on', 'false') == 'true',
        'open_search_first': settings.get('open_search_first', 'true') == 'true',
        'claude_api_key': settings.get('claude_api_key', ''),
        'ollama_url': settings.get('ollama_url', 'http://localhost:11434'),
        'ai_model': settings.get('ai_model', 'claude-sonnet-4-5')
    })


@api_bp.route('/settings', methods=['PUT'])
def update_settings():
    """Update application settings."""
    data = request.get_json()

    conn = get_db()
    cursor = conn.cursor()

    for key, value in data.items():
        # Convert booleans to strings
        if isinstance(value, bool):
            value = 'true' if value else 'false'

        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        ''', (key, str(value)))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


# ============================================================================
# BOOK UPLOAD
# ============================================================================

@api_bp.route('/upload/categories')
def get_upload_categories():
    """Get categories for upload dropdown."""
    uploader = get_book_uploader()
    categories = uploader.get_categories()
    return jsonify({'categories': categories})


@api_bp.route('/upload/file', methods=['POST'])
def upload_book_file():
    """Upload a single book file."""
    data = request.get_json()
    file_path = data.get('file_path', '')
    category_id = data.get('category_id', 1)
    is_custom = data.get('is_custom', False)
    override_metadata = data.get('metadata', {})

    if not file_path:
        return jsonify({'status': 'error', 'message': 'مسار الملف مطلوب'}), 400

    uploader = get_book_uploader()
    result = uploader.upload_file(file_path, category_id, is_custom, override_metadata)

    if result['status'] == 'error':
        return jsonify(result), 400

    return jsonify(result)


@api_bp.route('/upload/folder', methods=['POST'])
def upload_book_folder():
    """Upload all books from a folder."""
    data = request.get_json()
    folder_path = data.get('folder_path', '')
    category_id = data.get('category_id', 1)
    is_custom = data.get('is_custom', False)
    auto_assign = data.get('auto_assign', False)

    if not folder_path:
        return jsonify({'status': 'error', 'message': 'مسار المجلد مطلوب'}), 400

    uploader = get_book_uploader()
    result = uploader.upload_folder(folder_path, category_id, is_custom, auto_assign)

    return jsonify(result)


@api_bp.route('/upload/scan', methods=['POST'])
def scan_upload_folder():
    """Scan a folder and return list of book files."""
    data = request.get_json()
    folder_path = data.get('folder_path', '')

    if not folder_path:
        return jsonify({'status': 'error', 'message': 'مسار المجلد مطلوب'}), 400

    uploader = get_book_uploader()
    result = uploader.scan_folder(folder_path)

    return jsonify(result)


@api_bp.route('/upload/format-help')
def get_format_help():
    """Get book format documentation."""
    return jsonify({'help': BOOK_FORMAT_HELP})


@api_bp.route('/upload/browse-file', methods=['POST'])
def browse_file():
    """Open native file picker dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        # Create hidden root window
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        # Open file dialog
        file_path = filedialog.askopenfilename(
            title='اختر ملف كتاب',
            filetypes=[
                ('Text files', '*.txt'),
                ('Markdown files', '*.md'),
                ('All files', '*.*')
            ]
        )

        root.destroy()

        if file_path:
            return jsonify({'status': 'success', 'path': file_path})
        else:
            return jsonify({'status': 'cancelled'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/upload/browse-folder', methods=['POST'])
def browse_folder():
    """Open native folder picker dialog."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        # Create hidden root window
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        # Open folder dialog
        folder_path = filedialog.askdirectory(
            title='اختر مجلد الكتب'
        )

        root.destroy()

        if folder_path:
            return jsonify({'status': 'success', 'path': folder_path})
        else:
            return jsonify({'status': 'cancelled'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
# AI CHAT
# ============================================================================

@api_bp.route('/ai/chat', methods=['POST'])
def ai_chat():
    """AI chat endpoint for book assistance."""
    import urllib.request
    import json as json_lib

    data = request.get_json()
    message = data.get('message', '')
    book_id = data.get('book_id', '')
    page_content = data.get('page_content', '')
    book_title = data.get('book_title', '')

    if not message:
        return jsonify({'error': 'الرجاء كتابة رسالة'}), 400

    # Get AI settings
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM settings WHERE key IN (?, ?, ?)',
                   ('claude_api_key', 'ollama_url', 'ai_model'))
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    conn.close()

    claude_api_key = settings.get('claude_api_key', '').strip()
    ollama_url = settings.get('ollama_url', '').strip()
    ai_model = settings.get('ai_model', 'claude-sonnet-4-5').strip()

    # Model mapping for Ollama (UI name -> actual model name)
    OLLAMA_MODEL_MAP = {
        'ollama-llama2': 'llama2:latest',
        'ollama-llama3': 'llama3.2:latest',
        'ollama-mistral': 'mistral:latest',
        'ollama-deepseek': 'deepseek-r1:8b',
    }

    # Claude model mapping (UI name -> API model name)
    # Updated to Claude 4.5 family (2025)
    CLAUDE_MODEL_MAP = {
        'claude-sonnet-4-5': 'claude-sonnet-4-5-20250929',
        'claude-opus-4-5': 'claude-opus-4-5-20251101',
        'claude-haiku-4-5': 'claude-haiku-4-5-20251001',
    }

    # Build context from current page
    context = f"""أنت مساعد ذكي متخصص في الكتب العربية الإسلامية.
الكتاب الحالي: {book_title}
محتوى الصفحة الحالية:
{page_content[:2000] if page_content else 'لا يوجد محتوى'}

سؤال المستخدم: {message}

أجب باللغة العربية بشكل موجز ومفيد."""

    errors = []

    # Determine which service to use based on ai_model setting
    use_claude = ai_model.startswith('claude')
    use_ollama = ai_model.startswith('ollama')

    # Try Claude API if selected and key is set
    if use_claude:
        if not claude_api_key:
            return jsonify({'error': 'مفتاح Claude API غير مُعيّن. يرجى إضافته في الإعدادات.'}), 503

        try:
            claude_model = CLAUDE_MODEL_MAP.get(ai_model, 'claude-sonnet-4-5-20250929')

            headers = {
                'Content-Type': 'application/json',
                'x-api-key': claude_api_key,
                'anthropic-version': '2023-06-01'
            }

            payload = json_lib.dumps({
                'model': claude_model,
                'max_tokens': 1024,
                'messages': [{'role': 'user', 'content': context}]
            }).encode('utf-8')

            req = urllib.request.Request(
                'https://api.anthropic.com/v1/messages',
                data=payload,
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json_lib.loads(response.read().decode('utf-8'))
                ai_response = result.get('content', [{}])[0].get('text', '')
                return jsonify({'response': ai_response})

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            errors.append(f'Claude API error: {e.code} - {error_body}')
        except Exception as e:
            errors.append(f'Claude error: {str(e)}')

    # Try Ollama if selected
    if use_ollama:
        if not ollama_url:
            return jsonify({'error': 'عنوان Ollama غير مُعيّن. يرجى إضافته في الإعدادات.'}), 503

        try:
            # Map UI model name to actual Ollama model name
            ollama_model = OLLAMA_MODEL_MAP.get(ai_model, 'llama2:latest')

            payload = json_lib.dumps({
                'model': ollama_model,
                'prompt': context,
                'stream': False
            }).encode('utf-8')

            req = urllib.request.Request(
                f'{ollama_url}/api/generate',
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                result = json_lib.loads(response.read().decode('utf-8'))
                ai_response = result.get('response', '')
                return jsonify({'response': ai_response})

        except urllib.error.URLError as e:
            errors.append(f'Ollama connection error: {str(e.reason)}')
        except Exception as e:
            errors.append(f'Ollama error: {str(e)}')

    # If no AI service is configured or all failed
    if errors:
        return jsonify({
            'error': f'فشل الاتصال بخدمة الذكاء الاصطناعي: {"; ".join(errors)}'
        }), 503

    return jsonify({
        'error': 'لم يتم تكوين خدمة الذكاء الاصطناعي. يرجى اختيار نموذج وإضافة الإعدادات المطلوبة.'
    }), 503


@api_bp.route('/ai/debug', methods=['GET'])
def ai_debug():
    """Debug endpoint to check AI configuration status."""
    import urllib.request

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM settings WHERE key IN (?, ?, ?)',
                   ('claude_api_key', 'ollama_url', 'ai_model'))
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    conn.close()

    claude_api_key = settings.get('claude_api_key', '').strip()
    ollama_url = settings.get('ollama_url', '').strip()
    ai_model = settings.get('ai_model', '').strip()

    # Check Ollama connectivity
    ollama_status = {'reachable': False, 'models': [], 'error': None}
    if ollama_url:
        try:
            req = urllib.request.Request(f'{ollama_url}/api/tags', method='GET')
            with urllib.request.urlopen(req, timeout=5) as response:
                import json
                result = json.loads(response.read().decode('utf-8'))
                ollama_status['reachable'] = True
                ollama_status['models'] = [m.get('name') for m in result.get('models', [])]
        except Exception as e:
            ollama_status['error'] = str(e)

    return jsonify({
        'ai_model': ai_model,
        'has_claude_key': bool(claude_api_key),
        'claude_key_length': len(claude_api_key) if claude_api_key else 0,
        'ollama_url': ollama_url,
        'ollama_status': ollama_status,
        'use_claude': ai_model.startswith('claude') if ai_model else False,
        'use_ollama': ai_model.startswith('ollama') if ai_model else False,
    })


# ============================================================================
# DATA MANAGEMENT
# ============================================================================

@api_bp.route('/data/export')
def export_data():
    """Export all user data as JSON backup."""
    import json
    from datetime import datetime

    conn = get_db()
    cursor = conn.cursor()

    export_data = {
        'export_date': datetime.now().isoformat(),
        'version': '2.0',
        'collections': [],
        'reading_progress': [],
        'settings': {},
        'search_history': [],
        'custom_categories': [],
        'book_ownership': []
    }

    # Export collections
    cursor.execute('SELECT * FROM collections')
    for coll in cursor.fetchall():
        collection_data = {
            'id': coll['id'],
            'name': coll['name'],
            'created_at': coll['created_at'],
            'books': []
        }
        cursor.execute('''
            SELECT book_id, position FROM collection_books
            WHERE collection_id = ? ORDER BY position
        ''', (coll['id'],))
        collection_data['books'] = [
            {'book_id': row['book_id'], 'position': row['position']}
            for row in cursor.fetchall()
        ]
        export_data['collections'].append(collection_data)

    # Export reading progress
    cursor.execute('SELECT * FROM reading_progress')
    export_data['reading_progress'] = [
        {
            'book_id': row['book_id'],
            'current_page': row['current_page'],
            'total_pages': row['total_pages'],
            'last_read': row['last_read'],
            'is_complete': bool(row['is_complete'])
        }
        for row in cursor.fetchall()
    ]

    # Export settings (except sensitive ones)
    cursor.execute('SELECT key, value FROM settings')
    for row in cursor.fetchall():
        # Don't export sensitive data like API keys
        if row['key'] not in ('claude_api_key',):
            export_data['settings'][row['key']] = row['value']

    # Export search history
    cursor.execute('SELECT query, searched_at FROM search_history ORDER BY searched_at DESC LIMIT 100')
    export_data['search_history'] = [
        {'query': row['query'], 'searched_at': row['searched_at']}
        for row in cursor.fetchall()
    ]

    # Export custom categories
    cursor.execute('SELECT * FROM custom_categories')
    export_data['custom_categories'] = [
        {'id': row['id'], 'name': row['name'], 'created_at': row['created_at']}
        for row in cursor.fetchall()
    ]

    # Export book ownership status
    cursor.execute('SELECT id, is_owned FROM books WHERE is_owned = 1')
    export_data['book_ownership'] = [
        {'book_id': row['id'], 'is_owned': True}
        for row in cursor.fetchall()
    ]

    conn.close()

    return jsonify(export_data)


@api_bp.route('/data/import', methods=['POST'])
def import_data():
    """Import user data from JSON backup."""
    data = request.get_json()

    if not data or 'version' not in data:
        return jsonify({'error': 'ملف النسخة الاحتياطية غير صالح'}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Import collections
        if 'collections' in data:
            for coll in data['collections']:
                cursor.execute('''
                    INSERT OR REPLACE INTO collections (id, name, created_at)
                    VALUES (?, ?, ?)
                ''', (coll.get('id'), coll['name'], coll.get('created_at')))

                coll_id = coll.get('id') or cursor.lastrowid

                # Import collection books
                if 'books' in coll:
                    for book in coll['books']:
                        cursor.execute('''
                            INSERT OR IGNORE INTO collection_books (collection_id, book_id, position)
                            VALUES (?, ?, ?)
                        ''', (coll_id, book['book_id'], book.get('position', 0)))

        # Import reading progress
        if 'reading_progress' in data:
            for progress in data['reading_progress']:
                cursor.execute('''
                    INSERT OR REPLACE INTO reading_progress
                    (book_id, current_page, total_pages, last_read, is_complete)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    progress['book_id'],
                    progress.get('current_page', 1),
                    progress.get('total_pages', 1),
                    progress.get('last_read'),
                    1 if progress.get('is_complete') else 0
                ))

        # Import settings (except sensitive ones)
        if 'settings' in data:
            for key, value in data['settings'].items():
                if key not in ('claude_api_key',):  # Skip sensitive settings
                    cursor.execute('''
                        INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
                    ''', (key, value))

        # Import custom categories
        if 'custom_categories' in data:
            for cat in data['custom_categories']:
                cursor.execute('''
                    INSERT OR IGNORE INTO custom_categories (id, name, created_at)
                    VALUES (?, ?, ?)
                ''', (cat.get('id'), cat['name'], cat.get('created_at')))

        # Import book ownership
        if 'book_ownership' in data:
            for ownership in data['book_ownership']:
                cursor.execute('''
                    UPDATE books SET is_owned = 1 WHERE id = ?
                ''', (ownership['book_id'],))

        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': 'تم استيراد البيانات بنجاح'
        })

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({
            'status': 'error',
            'message': f'فشل استيراد البيانات: {str(e)}'
        }), 500


# ============================================================================
# NOTES / NOTEBOOK
# ============================================================================

@api_bp.route('/notes')
def get_notes():
    """Get all notes, grouped by date."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, content, created_at, updated_at, source_type, source_ref
        FROM notes
        ORDER BY created_at DESC
    ''')

    notes = []
    for row in cursor.fetchall():
        notes.append({
            'id': row['id'],
            'content': row['content'],
            'excerpt': row['content'][:80] + '...' if len(row['content']) > 80 else row['content'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'source_type': row['source_type'],
            'source_ref': row['source_ref']
        })

    conn.close()
    return jsonify({'notes': notes})


@api_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note."""
    import json as json_lib

    data = request.get_json()
    content = data.get('content', '')  # Allow empty content for new notes
    source_type = data.get('source_type', 'manual')
    source_ref = data.get('source_ref')

    # Serialize source_ref to JSON if it's a dict
    if source_ref and isinstance(source_ref, dict):
        source_ref = json_lib.dumps(source_ref, ensure_ascii=False)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO notes (content, source_type, source_ref)
        VALUES (?, ?, ?)
    ''', (content, source_type, source_ref))

    note_id = cursor.lastrowid

    # Get the created note
    cursor.execute('SELECT * FROM notes WHERE id = ?', (note_id,))
    row = cursor.fetchone()

    conn.commit()
    conn.close()

    return jsonify({
        'status': 'success',
        'note': {
            'id': row['id'],
            'content': row['content'],
            'excerpt': row['content'][:80] + '...' if len(row['content']) > 80 else row['content'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'source_type': row['source_type'],
            'source_ref': row['source_ref']
        }
    })


@api_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a single note by ID."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM notes WHERE id = ?', (note_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'الملاحظة غير موجودة'}), 404

    return jsonify({
        'id': row['id'],
        'content': row['content'],
        'created_at': row['created_at'],
        'updated_at': row['updated_at'],
        'source_type': row['source_type'],
        'source_ref': row['source_ref']
    })


@api_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update an existing note."""
    data = request.get_json()
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'error': 'محتوى الملاحظة مطلوب'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check if note exists
    cursor.execute('SELECT id FROM notes WHERE id = ?', (note_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'الملاحظة غير موجودة'}), 404

    cursor.execute('''
        UPDATE notes SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (content, note_id))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


@api_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a note."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    deleted = cursor.rowcount > 0

    conn.commit()
    conn.close()

    if not deleted:
        return jsonify({'error': 'الملاحظة غير موجودة'}), 404

    return jsonify({'status': 'success'})


@api_bp.route('/notes/export', methods=['POST'])
def export_notes():
    """Export selected notes as Markdown files."""
    import os
    import re
    import json as json_lib
    from datetime import datetime

    data = request.get_json()
    note_ids = data.get('note_ids', [])
    folder_path = data.get('folder_path', '')
    with_frontmatter = data.get('with_frontmatter', True)

    if not folder_path:
        return jsonify({'error': 'مسار المجلد مطلوب'}), 400

    if not os.path.isdir(folder_path):
        return jsonify({'error': 'المجلد غير موجود'}), 400

    if not note_ids:
        return jsonify({'error': 'لم يتم تحديد أي فوائد للتصدير'}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Get selected notes
    placeholders = ','.join('?' * len(note_ids))
    cursor.execute(f'SELECT * FROM notes WHERE id IN ({placeholders})', note_ids)

    notes = cursor.fetchall()
    conn.close()

    exported = []
    for note in notes:
        # Generate filename
        try:
            created = datetime.fromisoformat(note['created_at'].replace('Z', '+00:00')) if note['created_at'] else datetime.now()
        except:
            created = datetime.now()
        timestamp = created.strftime('%Y-%m-%d_%H%M%S')

        # Create slug from first 30 chars of content
        content = note['content'] or ''
        content_slug = re.sub(r'[^\w\s\u0600-\u06FF]', '', content[:30])
        content_slug = re.sub(r'\s+', '-', content_slug.strip()) or f"note-{note['id']}"

        filename = f"{timestamp}_{content_slug}.md"
        filepath = os.path.join(folder_path, filename)

        file_content = ''

        # Build Obsidian-compatible frontmatter if enabled
        if with_frontmatter:
            frontmatter = ['---']
            frontmatter.append(f"created: {note['created_at']}")
            frontmatter.append(f"updated: {note['updated_at']}")
            if note['source_type']:
                frontmatter.append(f"source_type: {note['source_type']}")
            if note['source_ref']:
                try:
                    ref = json_lib.loads(note['source_ref'])
                    if ref.get('book_title'):
                        frontmatter.append(f"book: \"{ref['book_title']}\"")
                    if ref.get('author'):
                        frontmatter.append(f"author: \"{ref['author']}\"")
                    if ref.get('page_num'):
                        frontmatter.append(f"page: {ref['page_num']}")
                except:
                    pass
            frontmatter.append('---')
            frontmatter.append('')
            file_content = '\n'.join(frontmatter)

        # Add note content
        file_content += content

        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)

        exported.append({'id': note['id'], 'filename': filename})

    return jsonify({
        'status': 'success',
        'exported': len(exported),
        'files': exported
    })


@api_bp.route('/notes/browse-export-folder', methods=['POST'])
def browse_export_folder():
    """Open native folder picker for export destination."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        folder_path = filedialog.askdirectory(
            title='اختر مجلد التصدير'
        )

        root.destroy()

        if folder_path:
            return jsonify({'status': 'success', 'path': folder_path})
        else:
            return jsonify({'status': 'cancelled'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/data/stats')
def get_data_stats():
    """Get database statistics and size information."""
    import os

    conn = get_db()
    cursor = conn.cursor()

    stats = {}

    # Count books
    cursor.execute('SELECT COUNT(*) as count FROM books')
    stats['total_books'] = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM books WHERE is_downloaded = 1')
    stats['downloaded_books'] = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) as count FROM books WHERE is_owned = 1')
    stats['owned_books'] = cursor.fetchone()['count']

    # Count pages
    cursor.execute('SELECT COUNT(*) as count FROM pages')
    stats['total_pages'] = cursor.fetchone()['count']

    # Count authors
    cursor.execute('SELECT COUNT(*) as count FROM authors')
    stats['total_authors'] = cursor.fetchone()['count']

    # Count collections
    cursor.execute('SELECT COUNT(*) as count FROM collections')
    stats['total_collections'] = cursor.fetchone()['count']

    # Count search history
    cursor.execute('SELECT COUNT(*) as count FROM search_history')
    stats['search_history_count'] = cursor.fetchone()['count']

    # Reading progress stats
    cursor.execute('SELECT COUNT(*) as count FROM reading_progress WHERE is_complete = 1')
    stats['completed_books'] = cursor.fetchone()['count']

    conn.close()

    # Database file size
    db_path = current_app.config['DATABASE_PATH']
    if os.path.exists(db_path):
        size_bytes = os.path.getsize(db_path)
        if size_bytes < 1024:
            stats['database_size'] = f'{size_bytes} B'
        elif size_bytes < 1024 * 1024:
            stats['database_size'] = f'{size_bytes / 1024:.1f} KB'
        elif size_bytes < 1024 * 1024 * 1024:
            stats['database_size'] = f'{size_bytes / (1024 * 1024):.1f} MB'
        else:
            stats['database_size'] = f'{size_bytes / (1024 * 1024 * 1024):.2f} GB'
        stats['database_size_bytes'] = size_bytes
    else:
        stats['database_size'] = '0 B'
        stats['database_size_bytes'] = 0

    return jsonify(stats)
