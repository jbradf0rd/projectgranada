"""
Granada v2 Book Upload System
Upload and parse books from local files
"""
import os
import re
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from app.search import normalize_arabic


def parse_metadata_header(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse metadata header from book content.

    Supports format:
    #META#
    Title: كتاب العلم
    Author: الإمام البخاري
    ...
    #META#END#

    Returns (metadata_dict, content_without_header)
    """
    metadata = {}

    # Check for metadata block
    meta_match = re.search(r'#META#\s*\n(.*?)\n#META#END#', content, re.DOTALL)

    if meta_match:
        meta_block = meta_match.group(1)
        remaining_content = content[meta_match.end():].strip()

        # Parse each metadata line
        for line in meta_block.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Map to standard keys
                key_map = {
                    'Title': 'title',
                    'TitleLatin': 'title_latin',
                    'Author': 'author',
                    'AuthorDeath': 'author_death',
                    'Editor': 'editor',
                    'Publisher': 'publisher',
                    'Edition': 'edition',
                    'Volumes': 'volumes',
                }

                mapped_key = key_map.get(key, key.lower())

                # Convert numeric fields
                if mapped_key in ('author_death', 'volumes'):
                    try:
                        value = int(value)
                    except ValueError:
                        pass

                metadata[mapped_key] = value

        return metadata, remaining_content

    # Support OpenITI-style metadata (######OpenITI# header format)
    if '#META#Header#End#' in content or '######OpenITI#' in content:
        # Split at header end
        if '#META#Header#End#' in content:
            remaining_content = content.split('#META#Header#End#')[1].strip()
        else:
            remaining_content = content

        # Extract ALL OpenITI metadata fields
        openiti_patterns = {
            # Book info
            'title': r'#META#\s*020\.BookTITLE\s*::\s*(.+)',
            'subtitle': r'#META#\s*020\.BookTITLESUB\s*::\s*(.+)',
            'alt_title': r'#META#\s*029\.BookTITLEalt\s*::\s*(.+)',
            'subject': r'#META#\s*021\.BookSUBJ\s*::\s*(.+)',
            'volumes': r'#META#\s*022\.BookVOLS\s*::\s*(\d+)',
            'language': r'#META#\s*025\.BookLANG\s*::\s*(.+)',
            'openiti_uri': r'#META#\s*000\.BookURI\s*::\s*(.+)',
            # Author info
            'author': r'#META#\s*010\.AuthorNAME\s*::\s*(.+)',
            'author_aka': r'#META#\s*010\.AuthorAKA\s*::\s*(.+)',
            'author_born': r'#META#\s*011\.AuthorBORN\s*::\s*(\d+)',
            'author_death': r'#META#\s*011\.AuthorDIED\s*::\s*(\d+)',
            # Edition info
            'editor': r'#META#\s*040\.EdEDITOR\s*::\s*(.+)',
            'edition': r'#META#\s*041\.EdNUMBER\s*::\s*(.+)',
            'publisher': r'#META#\s*043\.EdPUBLISHER\s*::\s*(.+)',
            'publication_place': r'#META#\s*044\.EdPLACE\s*::\s*(.+)',
            'publication_year': r'#META#\s*045\.EdYEAR\s*::\s*(.+)',
            'isbn': r'#META#\s*049\.EdISBN\s*::\s*(.+)',
            'page_count': r'#META#\s*049\.EdPAGES\s*::\s*(\d+)',
        }

        for key, pattern in openiti_patterns.items():
            match = re.search(pattern, content)
            if match:
                value = match.group(1).strip()
                # Skip NODATA/NOTGIVEN/9999/- values
                if value in ('NODATA', 'NOTGIVEN', 'NOCODE', '9999', '-', ''):
                    continue
                if key in ('volumes', 'author_death', 'author_born', 'page_count'):
                    try:
                        metadata[key] = int(value)
                    except ValueError:
                        pass
                else:
                    metadata[key] = value

        return metadata, remaining_content

    return metadata, content


def parse_openiti_filename(filename: str) -> Optional[Dict[str, Any]]:
    """
    Parse OpenITI filename format to extract metadata.

    Format: 0001AbuTalibCabdManaf.Diwan.JK007501-ara1
            │    │                │     │        │
            │    │                │     │        └── Language
            │    │                │     └── Version ID
            │    │                └── Book title
            │    └── Author name (CamelCase)
            └── Death date (AH)

    Returns metadata dict or None if not OpenITI format.
    """
    # Remove extension if present
    name = Path(filename).stem

    # OpenITI pattern: 4 digits + CamelCase author + dot + title + optional version
    pattern = r'^(\d{4})([A-Za-z]+)\.([^.]+)(?:\.([^-]+))?(?:-([a-z]{3}\d?))?$'
    match = re.match(pattern, name)

    if not match:
        return None

    death_date, author_camel, title_camel, version_id, lang = match.groups()

    # Convert CamelCase to readable Arabic-friendly format
    def camel_to_spaced(s):
        # Insert space before capital letters
        return re.sub(r'([a-z])([A-Z])', r'\1 \2', s)

    # Common Arabic name transliterations
    arabic_names = {
        'Abu': 'أبو', 'Ibn': 'ابن', 'Al': 'ال', 'Abd': 'عبد',
        'Muhammad': 'محمد', 'Ahmad': 'أحمد', 'Ali': 'علي',
        'Umar': 'عمر', 'Uthman': 'عثمان', 'Bukhari': 'البخاري',
        'Muslim': 'مسلم', 'Tirmidhi': 'الترمذي', 'Nasai': 'النسائي',
        'Malik': 'مالك', 'Hanbal': 'حنبل', 'Dawud': 'داود',
        'Maja': 'ماجه', 'Darimi': 'الدارمي', 'Talib': 'طالب',
        'Manaf': 'مناف', 'Diwan': 'ديوان', 'Sahih': 'صحيح',
        'Sunan': 'سنن', 'Musnad': 'مسند', 'Muwatta': 'موطأ',
        'Kitab': 'كتاب', 'Sharh': 'شرح', 'Tafsir': 'تفسير',
    }

    def transliterate(text):
        """Try to transliterate common terms to Arabic."""
        words = camel_to_spaced(text).split()
        result = []
        for word in words:
            # Check if we have an Arabic equivalent
            if word in arabic_names:
                result.append(arabic_names[word])
            else:
                result.append(word)
        return ' '.join(result)

    return {
        'author_death': int(death_date),
        'author': transliterate(author_camel),
        'author_latin': camel_to_spaced(author_camel),
        'title': transliterate(title_camel),
        'title_latin': camel_to_spaced(title_camel),
        'openiti_id': name,
        'version_id': version_id,
        'source': 'openiti'
    }


def parse_book_content(content: str) -> List[Dict[str, Any]]:
    """
    Parse book content into pages.

    Supports multiple page marker formats:
    - ---PAGE V01P001--- (Volume 1, Page 1)
    - ---PAGE 1--- (Simple sequential)
    - PageV01P001 or # PageV01P001 (OpenITI style)

    Returns list of pages with: page_num, volume, original_page, content
    """
    pages = []

    # First extract metadata if present
    _, content = parse_metadata_header(content)

    # Try different page marker patterns
    patterns = [
        # New format: ---PAGE V01P001--- or ---PAGE 1---
        (r'---PAGE\s+V?(\d{1,2})P(\d{1,4})---', True),  # With volume
        (r'---PAGE\s+(\d+)---', False),  # Simple sequential
        # OpenITI format: # PageV01P001 or PageV01P001
        (r'#?\s*PageV(\d{2})P(\d{2,4})', True),
    ]

    markers = []
    pattern_has_volume = False

    for pattern, has_volume in patterns:
        found = list(re.finditer(pattern, content))
        if found:
            markers = found
            pattern_has_volume = has_volume
            break

    if markers:
        for i, match in enumerate(markers):
            if pattern_has_volume:
                vol = int(match.group(1))
                pg = int(match.group(2))
            else:
                vol = 1
                pg = int(match.group(1))

            volume = vol if vol > 0 else 1

            # Get content from this marker to the next (or end)
            start_pos = match.end()
            end_pos = markers[i + 1].start() if i + 1 < len(markers) else len(content)

            page_content = content[start_pos:end_pos].strip()
            page_content = clean_markup(page_content)

            if page_content.strip():
                pages.append({
                    'page_num': len(pages) + 1,
                    'volume': volume,
                    'original_page': pg,
                    'content': page_content
                })

    # If no markers found, split by approximate page size
    if not pages and content.strip():
        content = clean_markup(content)
        # Split into ~2000 character pages, trying to break at paragraph boundaries
        chunk_size = 2000

        paragraphs = content.split('\n\n')
        current_chunk = ''

        for para in paragraphs:
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                pages.append({
                    'page_num': len(pages) + 1,
                    'volume': 1,
                    'original_page': len(pages) + 1,
                    'content': current_chunk.strip()
                })
                current_chunk = para
            else:
                current_chunk += '\n\n' + para if current_chunk else para

        # Don't forget the last chunk
        if current_chunk.strip():
            pages.append({
                'page_num': len(pages) + 1,
                'volume': 1,
                'original_page': len(pages) + 1,
                'content': current_chunk.strip()
            })

    return pages


def clean_markup(text: str) -> str:
    """Remove OpenITI and other markup from text."""
    # Remove page markers (all formats)
    text = re.sub(r'---PAGE[^-]*---', '', text)
    text = re.sub(r'PageV\d+P\d+', '', text)

    # Remove OpenITI milestone markers (ms0017, etc.)
    text = re.sub(r'\bms\d+\b', '', text)

    # Remove editorial notes ~~text~~ and standalone ~~
    text = re.sub(r'~~[^~]*~~', '', text)
    text = re.sub(r'~~', '', text)

    # Remove hemistich markers (poetry: % text % or %~%)
    text = text.replace('%~%', ' ')
    text = re.sub(r'\s*%\s*', ' ', text)

    # Remove line numbers at end of lines (common in poetry: verse text 123)
    text = re.sub(r'\s+\d+\s*$', '', text, flags=re.MULTILINE)

    # Remove standalone numbers at start of content (misplaced verse numbers)
    text = re.sub(r'^\d+\s*\n', '', text)
    text = re.sub(r'\n\d+\s*\n', '\n', text)

    # Remove # at start of lines (OpenITI comments/headers)
    text = re.sub(r'^#\s*', '', text, flags=re.MULTILINE)

    # Clean up metadata remnants
    text = re.sub(r'#META#.*?#META#END#', '', text, flags=re.DOTALL)
    text = re.sub(r'#META#Header#End#', '', text)

    # Remove OpenITI header block (######OpenITI# to #META#Header#End#)
    text = re.sub(r'######OpenITI#.*?#META#Header#End#', '', text, flags=re.DOTALL)

    # Clean up extra whitespace
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single
    text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines to double
    text = re.sub(r'^\s+$', '', text, flags=re.MULTILINE)  # Empty lines with whitespace
    text = text.strip()

    return text


def extract_toc_entries(content: str) -> List[Dict[str, Any]]:
    """
    Extract TOC (Table of Contents) entries from OpenITI content.

    OpenITI markers:
    - ### | title - level 1 (chapters)
    - ### || title - level 2 (sections)
    - ### ||| title - level 3 (subsections)
    - # | title - headers (level 1)
    - | title at start of line - headers (level 2)

    Returns list of {title, level, char_position}
    """
    toc_entries = []

    # Pattern for ### | markers with varying levels
    # ### | title or ### || title or ### ||| title
    pattern_triple_hash = r'###\s*(\|+)\s*([^\n]*)'
    for match in re.finditer(pattern_triple_hash, content):
        pipes = match.group(1)
        title = match.group(2).strip()
        level = len(pipes)  # Number of | determines level

        if title:  # Only add if there's a title
            toc_entries.append({
                'title': title,
                'level': level,
                'char_pos': match.start()
            })

    # Pattern for # | title (single hash with pipe) - common in OpenITI
    # Match lines like "# | الحديث الاول"
    pattern_hash_pipe = r'^#\s*\|\s*(.+)$'
    for match in re.finditer(pattern_hash_pipe, content, re.MULTILINE):
        title = match.group(1).strip()
        if title and len(title) >= 3:
            toc_entries.append({
                'title': title,
                'level': 1,  # Treat as level 1 (chapter/hadith)
                'char_pos': match.start()
            })

    # Pattern for | at start of line (without #)
    # Match lines like "| الحديث الاول" or "| فصل"
    pattern_pipe = r'^\|\s*([^|\n]+)$'
    for match in re.finditer(pattern_pipe, content, re.MULTILINE):
        title = match.group(1).strip()
        # Skip if too short
        if len(title) < 3:
            continue

        toc_entries.append({
            'title': title,
            'level': 2,  # Treat as level 2 (section)
            'char_pos': match.start()
        })

    # Sort by position in document
    toc_entries.sort(key=lambda x: x['char_pos'])

    # Deduplicate entries with same title close together
    deduped = []
    for entry in toc_entries:
        if not deduped or entry['title'] != deduped[-1]['title']:
            deduped.append(entry)

    return deduped


def parse_book_content_with_toc(content: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parse book content into pages and extract TOC entries.

    Returns (pages, toc_entries) where each toc_entry has page_num assigned.
    """
    # First extract TOC entries with character positions
    toc_entries = extract_toc_entries(content)

    # Extract metadata
    _, content_body = parse_metadata_header(content)

    # Find page markers and their positions
    page_markers = []
    patterns = [
        (r'PageV(\d{2})P(\d{2,4})', True),  # OpenITI: PageV01P001
        (r'---PAGE\s+V?(\d{1,2})P(\d{1,4})---', True),  # With volume
        (r'---PAGE\s+(\d+)---', False),  # Simple sequential
    ]

    for pattern, has_volume in patterns:
        for match in re.finditer(pattern, content):
            if has_volume:
                vol = int(match.group(1))
                pg = int(match.group(2))
            else:
                vol = 1
                pg = int(match.group(1))

            page_markers.append({
                'volume': vol if vol > 0 else 1,
                'original_page': pg,
                'start_pos': match.end(),
                'marker_pos': match.start()
            })

        if page_markers:
            break

    # Sort markers by position
    page_markers.sort(key=lambda x: x['marker_pos'])

    # Parse pages
    pages = []
    for i, marker in enumerate(page_markers):
        end_pos = page_markers[i + 1]['marker_pos'] if i + 1 < len(page_markers) else len(content)
        page_content = content[marker['start_pos']:end_pos].strip()
        page_content = clean_markup(page_content)

        if page_content.strip():
            pages.append({
                'page_num': len(pages) + 1,
                'volume': marker['volume'],
                'original_page': marker['original_page'],
                'content': page_content,
                'char_start': marker['marker_pos'],
                'char_end': end_pos
            })

    # If no page markers, create pages by splitting content
    if not pages and content_body.strip():
        content_clean = clean_markup(content_body)
        chunk_size = 2000
        paragraphs = content_clean.split('\n\n')
        current_chunk = ''
        char_pos = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) > chunk_size and current_chunk:
                pages.append({
                    'page_num': len(pages) + 1,
                    'volume': 1,
                    'original_page': len(pages) + 1,
                    'content': current_chunk.strip(),
                    'char_start': char_pos,
                    'char_end': char_pos + len(current_chunk)
                })
                char_pos += len(current_chunk)
                current_chunk = para
            else:
                current_chunk += '\n\n' + para if current_chunk else para

        if current_chunk.strip():
            pages.append({
                'page_num': len(pages) + 1,
                'volume': 1,
                'original_page': len(pages) + 1,
                'content': current_chunk.strip(),
                'char_start': char_pos,
                'char_end': char_pos + len(current_chunk)
            })

    # Assign page numbers to TOC entries based on character position
    for toc in toc_entries:
        toc['page_num'] = 1  # Default
        for page in pages:
            if toc['char_pos'] >= page.get('char_start', 0):
                toc['page_num'] = page['page_num']
            else:
                break

    # Clean up internal fields from pages
    for page in pages:
        page.pop('char_start', None)
        page.pop('char_end', None)

    return pages, toc_entries


def generate_book_id(title: str, author: str = None, death_date: int = None) -> str:
    """Generate a unique book ID from metadata."""
    import hashlib
    import time

    # Create base from title
    base = re.sub(r'[^\w\s]', '', title)
    base = base.replace(' ', '_')[:30]

    # Add hash for uniqueness
    unique = f"{title}{author}{death_date}{time.time()}"
    hash_suffix = hashlib.md5(unique.encode()).hexdigest()[:8]

    return f"{base}_{hash_suffix}"


class BookUploader:
    """Handles uploading and processing local book files."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=30000')
        return conn

    def get_categories(self) -> List[Dict[str, Any]]:
        """Get list of available categories (main + custom)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get main categories
        cursor.execute('SELECT id, name FROM categories ORDER BY name')
        main_categories = [{'id': row['id'], 'name': row['name'], 'is_custom': False}
                          for row in cursor.fetchall()]

        # Get custom categories
        cursor.execute('SELECT id, name FROM custom_categories ORDER BY name')
        custom_categories = [{'id': row['id'], 'name': row['name'], 'is_custom': True}
                            for row in cursor.fetchall()]

        conn.close()

        # Custom categories first, then main
        return custom_categories + main_categories

    def _check_duplicate(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Check if a book with this ID already exists and is downloaded."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check for existing downloaded book with same ID
        cursor.execute('''
            SELECT id, title, is_downloaded FROM books WHERE id = ?
        ''', (book_id,))
        row = cursor.fetchone()
        conn.close()

        if row and row['is_downloaded']:
            return {'id': row['id'], 'title': row['title']}
        return None

    def upload_file(
        self,
        file_path: str,
        category_id: int = 1,
        is_custom_category: bool = False,
        override_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Upload a single book file.

        Args:
            file_path: Path to the book file (.txt or .md)
            category_id: Category to assign the book to
            is_custom_category: Whether category_id refers to custom_categories table
            override_metadata: Optional metadata to override file metadata

        Returns:
            Dict with status and book info
        """
        path = Path(file_path)

        if not path.exists():
            return {'status': 'error', 'message': f'الملف غير موجود: {file_path}'}

        # Check if it's an OpenITI file (no extension, matches pattern)
        is_openiti = parse_openiti_filename(path.name) is not None

        # Allow .txt, .md, .markdown, or OpenITI files (no extension)
        valid_extensions = ('.txt', '.md', '.markdown')
        if path.suffix.lower() not in valid_extensions and path.suffix != '' and not is_openiti:
            return {'status': 'error', 'message': 'صيغة الملف غير مدعومة. استخدم .txt أو .md أو ملفات OpenITI'}

        try:
            # Read file content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(path, 'r', encoding='cp1256') as f:
                    content = f.read()
            except Exception as e:
                return {'status': 'error', 'message': f'خطأ في قراءة الملف: {e}'}

        if len(content) < 100:
            return {'status': 'error', 'message': 'الملف فارغ أو قصير جداً'}

        # Try to parse OpenITI filename first
        openiti_meta = parse_openiti_filename(path.name)

        # Parse metadata from file content
        content_meta, _ = parse_metadata_header(content)

        # Merge metadata: OpenITI filename -> content header -> defaults
        metadata = {}
        if openiti_meta:
            metadata.update(openiti_meta)
        if content_meta:
            metadata.update(content_meta)

        # Apply overrides
        if override_metadata:
            metadata.update(override_metadata)

        # Ensure required fields
        if 'title' not in metadata:
            # Use filename as title
            metadata['title'] = path.stem.replace('_', ' ')

        if 'author' not in metadata:
            metadata['author'] = 'غير معروف'

        # Check for duplicate using openiti_id or filename
        openiti_id = metadata.get('openiti_id', path.stem)
        existing = self._check_duplicate(openiti_id)
        if existing:
            return {
                'status': 'duplicate',
                'message': f'الكتاب موجود مسبقاً',
                'book_id': existing['id'],
                'title': existing['title']
            }

        # Generate book ID (use openiti_id if available for consistency)
        if metadata.get('openiti_id'):
            book_id = metadata['openiti_id']
        else:
            book_id = generate_book_id(
                metadata['title'],
                metadata.get('author'),
                metadata.get('author_death')
            )

        # Parse content into pages and extract TOC
        pages, toc_entries = parse_book_content_with_toc(content)

        if not pages:
            return {'status': 'error', 'message': 'فشل تحليل محتوى الكتاب'}

        # Save to database
        return self._save_book(book_id, metadata, pages, toc_entries, category_id, is_custom_category, len(content))

    def _get_or_create_category_from_subject(self, subject: str) -> Tuple[int, bool]:
        """
        Get or create a category based on the subject field.
        Uses the first part of the subject hierarchy.

        Args:
            subject: Subject string like "السنن :: فقه الحديث :: كتب الحديث"

        Returns:
            Tuple of (category_id, is_custom)
        """
        if not subject:
            return 1, False  # Default to first main category

        # Extract first part of hierarchy (main category)
        parts = [p.strip() for p in subject.split('::')]
        category_name = parts[0] if parts else subject

        conn = self._get_connection()
        cursor = conn.cursor()

        # First check if category exists in main categories
        cursor.execute('SELECT id FROM categories WHERE name = ?', (category_name,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return row['id'], False

        # Check custom categories
        cursor.execute('SELECT id FROM custom_categories WHERE name = ?', (category_name,))
        row = cursor.fetchone()
        if row:
            conn.close()
            return row['id'], True

        # Create new custom category
        cursor.execute('INSERT INTO custom_categories (name) VALUES (?)', (category_name,))
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return new_id, True

    def _get_file_subject(self, file_path: str) -> Optional[str]:
        """
        Read a file and extract just the subject field from metadata.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read first 5000 chars to get metadata header
                content = f.read(5000)
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1256') as f:
                    content = f.read(5000)
            except Exception:
                return None
        except Exception:
            return None

        # Extract subject from OpenITI metadata
        match = re.search(r'#META#\s*021\.BookSUBJ\s*::\s*(.+)', content)
        if match:
            value = match.group(1).strip()
            if value not in ('NODATA', 'NOTGIVEN', 'NOCODE', ''):
                return value

        return None

    def upload_folder(
        self,
        folder_path: str,
        category_id: int = 1,
        is_custom_category: bool = False,
        auto_assign: bool = False
    ) -> Dict[str, Any]:
        """
        Upload all book files from a folder.

        Args:
            folder_path: Path to folder containing book files
            category_id: Category to assign all books to
            is_custom_category: Whether category_id refers to custom_categories
            auto_assign: If True, auto-assign categories based on subject field

        Returns:
            Dict with status and list of results
        """
        path = Path(folder_path)

        if not path.exists():
            return {'status': 'error', 'message': f'المجلد غير موجود: {folder_path}'}

        if not path.is_dir():
            return {'status': 'error', 'message': 'المسار ليس مجلداً'}

        # Find all text files
        files = list(path.glob('*.txt')) + list(path.glob('*.md')) + list(path.glob('*.markdown'))

        # Also find OpenITI files (match pattern, not already in list)
        # OpenITI files have dots as separators, so they may appear to have extensions
        for f in path.iterdir():
            if f.is_file() and f not in files:
                # Check if it matches OpenITI pattern
                if parse_openiti_filename(f.name):
                    files.append(f)

        if not files:
            return {'status': 'error', 'message': 'لا توجد ملفات كتب في المجلد'}

        results = []
        success_count = 0

        for file_path in files:
            # Determine category for this file
            file_category_id = category_id
            file_is_custom = is_custom_category
            auto_category_name = None

            if auto_assign:
                # Try to get subject from file and create/find category
                subject = self._get_file_subject(str(file_path))
                if subject:
                    file_category_id, file_is_custom = self._get_or_create_category_from_subject(subject)
                    auto_category_name = subject.split('::')[0].strip()

            result = self.upload_file(str(file_path), file_category_id, file_is_custom)
            result['filename'] = file_path.name
            if auto_category_name:
                result['auto_category'] = auto_category_name
            results.append(result)

            if result['status'] == 'success':
                success_count += 1

        return {
            'status': 'success' if success_count > 0 else 'error',
            'message': f'تم رفع {success_count} من {len(files)} كتاب',
            'total': len(files),
            'success': success_count,
            'results': results
        }

    def scan_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Scan a folder and return list of detected book files.

        Args:
            folder_path: Path to folder to scan

        Returns:
            Dict with list of files and their basic info
        """
        path = Path(folder_path)

        if not path.exists():
            return {'status': 'error', 'message': f'المجلد غير موجود: {folder_path}'}

        if not path.is_dir():
            return {'status': 'error', 'message': 'المسار ليس مجلداً'}

        # Find standard text files
        files = list(path.glob('*.txt')) + list(path.glob('*.md')) + list(path.glob('*.markdown'))

        # Also find OpenITI files (match pattern, not already in list)
        # OpenITI files have dots as separators, so they may appear to have extensions
        for f in path.iterdir():
            if f.is_file() and f not in files:
                # Check if it matches OpenITI pattern
                if parse_openiti_filename(f.name):
                    files.append(f)

        file_list = []
        for f in files:
            try:
                size = f.stat().st_size

                # Try to parse OpenITI filename first
                openiti_meta = parse_openiti_filename(f.name)

                if openiti_meta:
                    # Use OpenITI metadata
                    file_list.append({
                        'path': str(f),
                        'name': f.name,
                        'size': size,
                        'size_formatted': f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB",
                        'title': openiti_meta.get('title', f.stem),
                        'author': openiti_meta.get('author', 'غير معروف'),
                        'is_openiti': True
                    })
                else:
                    # Try to read first few lines for title
                    with open(f, 'r', encoding='utf-8') as fp:
                        preview = fp.read(500)

                    metadata, _ = parse_metadata_header(preview)

                    file_list.append({
                        'path': str(f),
                        'name': f.name,
                        'size': size,
                        'size_formatted': f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.1f} MB",
                        'title': metadata.get('title', f.stem),
                        'author': metadata.get('author', 'غير معروف'),
                        'is_openiti': False
                    })
            except Exception:
                file_list.append({
                    'path': str(f),
                    'name': f.name,
                    'size': 0,
                    'size_formatted': '???',
                    'title': f.stem,
                    'author': 'غير معروف',
                    'is_openiti': False
                })

        return {
            'status': 'success',
            'files': file_list,
            'count': len(file_list)
        }

    def _save_book(
        self,
        book_id: str,
        metadata: Dict[str, Any],
        pages: List[Dict[str, Any]],
        toc_entries: List[Dict[str, Any]],
        category_id: int,
        is_custom_category: bool,
        file_size: int
    ) -> Dict[str, Any]:
        """Save book, pages, and TOC to database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Create author if needed
            author_id = re.sub(r'[^\w]', '', metadata.get('author', 'Unknown'))[:20]

            cursor.execute('SELECT id FROM authors WHERE id = ?', (author_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO authors (id, name, death_date)
                    VALUES (?, ?, ?)
                ''', (author_id, metadata.get('author', 'غير معروف'),
                      metadata.get('author_death')))

            # If book already exists, delete it first (re-upload scenario)
            cursor.execute('SELECT id FROM books WHERE id = ?', (book_id,))
            if cursor.fetchone():
                # Delete existing book data
                cursor.execute('DELETE FROM pages WHERE book_id = ?', (book_id,))
                cursor.execute('DELETE FROM pages_fts WHERE book_id = ?', (book_id,))
                cursor.execute('DELETE FROM toc_entries WHERE book_id = ?', (book_id,))
                cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))

            # For custom categories, set category_id to NULL in books table
            main_category_id = None if is_custom_category else category_id

            # Insert book with all metadata
            source = metadata.get('source', 'local')
            cursor.execute('''
                INSERT INTO books (id, title, author_id, category_id, death_date,
                                   file_size, is_downloaded, download_date, source,
                                   volumes_count, editor, edition, publisher,
                                   author_name, author_aka, author_born, subtitle,
                                   alt_title, subject, language, publication_place,
                                   publication_year, isbn, page_count, openiti_uri)
                VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'), ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (book_id, metadata.get('title', 'بدون عنوان'), author_id, main_category_id,
                  metadata.get('author_death'), file_size, source,
                  metadata.get('volumes', 1), metadata.get('editor'),
                  metadata.get('edition'), metadata.get('publisher'),
                  metadata.get('author'), metadata.get('author_aka'),
                  metadata.get('author_born'), metadata.get('subtitle'),
                  metadata.get('alt_title'), metadata.get('subject'),
                  metadata.get('language'), metadata.get('publication_place'),
                  metadata.get('publication_year'), metadata.get('isbn'),
                  metadata.get('page_count'), metadata.get('openiti_uri')))

            # If custom category, add to book_custom_categories
            if is_custom_category:
                cursor.execute('''
                    INSERT INTO book_custom_categories (book_id, category_id)
                    VALUES (?, ?)
                ''', (book_id, category_id))

            # Insert pages
            for page in pages:
                normalized = normalize_arabic(page['content'])

                cursor.execute('''
                    INSERT INTO pages (book_id, page_num, volume, original_page, content, content_normalized)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (book_id, page['page_num'], page.get('volume', 1),
                      page.get('original_page', page['page_num']), page['content'], normalized))

                cursor.execute('''
                    INSERT INTO pages_fts (book_id, page_num, content)
                    VALUES (?, ?, ?)
                ''', (book_id, str(page['page_num']), normalized))

            # Insert TOC entries
            for i, toc in enumerate(toc_entries):
                cursor.execute('''
                    INSERT INTO toc_entries (book_id, title, level, page_num, position)
                    VALUES (?, ?, ?, ?, ?)
                ''', (book_id, toc['title'], toc.get('level', 1),
                      toc.get('page_num', 1), i + 1))

            # Create reading progress entry
            cursor.execute('''
                INSERT OR IGNORE INTO reading_progress (book_id, current_page, total_pages)
                VALUES (?, 1, ?)
            ''', (book_id, len(pages)))

            conn.commit()

            return {
                'status': 'success',
                'book_id': book_id,
                'title': metadata.get('title', 'بدون عنوان'),
                'pages': len(pages),
                'toc_count': len(toc_entries),
                'message': f'تم رفع الكتاب بنجاح ({len(pages)} صفحة، {len(toc_entries)} فصل)'
            }

        except Exception as e:
            conn.rollback()
            return {'status': 'error', 'message': f'خطأ في حفظ الكتاب: {e}'}

        finally:
            conn.close()


# Format documentation for UI display
BOOK_FORMAT_HELP = """
# صيغة ملف الكتاب

## البيانات الوصفية (اختياري)
```
#META#
Title: عنوان الكتاب
TitleLatin: Book Title in Latin
Author: اسم المؤلف
AuthorDeath: 256
Editor: اسم المحقق
Publisher: دار النشر
Edition: رقم الطبعة
Volumes: 1
#META#END#
```

## علامات الصفحات
```
---PAGE V01P001---
محتوى الصفحة الأولى من المجلد الأول

---PAGE V01P002---
محتوى الصفحة الثانية

---PAGE 1---
أو استخدم ترقيم بسيط
```

## علامات الفهرس (اختياري)
```
### | كتاب العلم
### | باب فضل طلب العلم
```

## ملاحظات
- الملفات المدعومة: .txt, .md
- الترميز: UTF-8
- إذا لم توجد علامات صفحات، سيتم تقسيم النص تلقائياً
"""
