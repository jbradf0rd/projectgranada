# Granada v2: Ralph Implementation Guide

This document provides phase-by-phase instructions for building Granada, an offline Arabic book search engine. Each phase is self-contained and testable before moving to the next.

---

## Project Overview

**Goal:** Build a turath.io clone with personal library features

**Tech Stack:**
- Flask (Python backend)
- SQLite + FTS5 (database + search)
- Jinja2 + Alpine.js (frontend)
- PyArabic (Arabic text normalization)

**Critical Design Principle:** Every UI element must visually match turath.io exactly. Reference screenshots are the source of truth.

---

## File Structure

```
granada-v2/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
│
├── app/
│   ├── __init__.py            # App factory
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py            # Page routes (HTML)
│   │   └── api.py             # API routes (JSON)
│   ├── models.py              # SQLAlchemy models
│   ├── database.py            # Database initialization
│   ├── search.py              # FTS5 search logic
│   ├── normalize.py           # Arabic normalization
│   └── openiti.py             # OpenITI integration
│
├── templates/                  # [ALREADY CREATED]
│   ├── base.html
│   ├── search.html
│   ├── books.html
│   ├── authors.html
│   ├── categories.html
│   ├── collections.html
│   ├── settings.html
│   ├── reader.html
│   └── wizard.html
│
├── static/
│   ├── css/
│   │   └── main.css           # [ALREADY CREATED]
│   └── js/
│       └── alpine.min.js      # (CDN used instead)
│
└── data/
    └── granada.db             # SQLite database
```

---

## Phase 1: Minimal Flask App

**Goal:** Get Flask serving the existing templates with navigation working

### Story 1.1: Create Flask App Structure

Create the minimal Flask application that serves templates.

**Files to create:**

`requirements.txt`:
```
Flask==3.0.0
python-dotenv==1.0.0
```

`config.py`:
```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'granada.db')
```

`app/__init__.py`:
```python
from flask import Flask
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config_class)
    
    from app.routes import main
    app.register_blueprint(main.bp)
    
    return app
```

`app/routes/__init__.py`:
```python
# Routes package
```

`app/routes/main.py`:
```python
from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/search')
def search():
    return render_template('search.html', active_page='search')

@bp.route('/books')
def books():
    return render_template('books.html', active_page='books')

@bp.route('/authors')
def authors():
    return render_template('authors.html', active_page='authors')

@bp.route('/categories')
def categories():
    return render_template('categories.html', active_page='categories')

@bp.route('/collections')
def collections():
    return render_template('collections.html', active_page='collections')

@bp.route('/settings')
def settings():
    return render_template('settings.html', active_page='settings')

@bp.route('/book/<book_id>')
def reader(book_id):
    return render_template('reader.html', active_page='books', book={'id': book_id, 'title': 'عنوان الكتاب'})

@bp.route('/wizard')
def wizard():
    return render_template('wizard.html')
```

`app.py`:
```python
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

**Acceptance Criteria:**
- [ ] `python app.py` starts server on port 5000
- [ ] All pages load without errors: /, /books, /authors, /categories, /collections, /settings
- [ ] Navigation highlights correct active page
- [ ] CSS loads correctly (dark theme visible)
- [ ] No 404 errors for static files

---

### Story 1.2: Verify All Templates Render

Test each page and fix any Jinja2 template errors.

**Test checklist:**
- [ ] Search page: dropdowns open/close with Alpine.js
- [ ] Books page: tabs switch correctly
- [ ] Authors page: list renders
- [ ] Categories page: custom categories section visible
- [ ] Collections page: empty state shows
- [ ] Settings page: all sections visible
- [ ] Reader page: navigation works
- [ ] Wizard page: buttons work

**Common issues to fix:**
- Missing `url_for` references
- Alpine.js x-data not initializing
- CSS not loading (check static path)

---

## Phase 2: API Endpoints (Stub Data)

**Goal:** Create API endpoints that return hardcoded data so frontend can fetch it

### Story 2.1: Create API Blueprint

`app/routes/api.py`:
```python
from flask import Blueprint, jsonify, request

bp = Blueprint('api', __name__, url_prefix='/api')

# Stub data
STUB_BOOKS = [
    {'id': '1', 'title': 'صحيح البخاري', 'author': 'البخاري', 'author_id': '1', 'death_date': '256', 'category': 'كتب السنة', 'category_id': '6', 'file_size': 52428800, 'is_owned': True, 'is_downloaded': True},
    {'id': '2', 'title': 'صحيح مسلم', 'author': 'مسلم بن الحجاج', 'author_id': '2', 'death_date': '261', 'category': 'كتب السنة', 'category_id': '6', 'file_size': 41943040, 'is_owned': False, 'is_downloaded': True},
    {'id': '3', 'title': 'سنن أبي داود', 'author': 'أبو داود', 'author_id': '3', 'death_date': '275', 'category': 'كتب السنة', 'category_id': '6', 'file_size': 31457280, 'is_owned': False, 'is_downloaded': False},
]

STUB_AUTHORS = [
    {'id': '1', 'name': 'البخاري', 'death_date': '256', 'book_count': 1},
    {'id': '2', 'name': 'مسلم بن الحجاج', 'death_date': '261', 'book_count': 1},
    {'id': '3', 'name': 'أبو داود', 'death_date': '275', 'book_count': 1},
    {'id': '4', 'name': 'ابن تيمية', 'death_date': '728', 'book_count': 45},
]

STUB_CATEGORIES = [
    {'id': 1, 'number': '١', 'name': 'العقيدة', 'book_count': 808},
    {'id': 2, 'number': '٢', 'name': 'الفرق والردود', 'book_count': 151},
    {'id': 3, 'number': '٣', 'name': 'التفسير', 'book_count': 272},
    {'id': 4, 'number': '٤', 'name': 'علوم القرآن', 'book_count': 310},
    {'id': 5, 'number': '٥', 'name': 'التجويد والقراءات', 'book_count': 151},
    {'id': 6, 'number': '٦', 'name': 'كتب السنة', 'book_count': 1241},
]

@bp.route('/filters')
def get_filters():
    """Return filter options for search page"""
    return jsonify({
        'books': [{'id': b['id'], 'title': b['title']} for b in STUB_BOOKS],
        'authors': [{'id': a['id'], 'name': a['name']} for a in STUB_AUTHORS],
        'categories': [{'id': c['id'], 'name': c['name']} for c in STUB_CATEGORIES]
    })

@bp.route('/books')
def get_books():
    """Return list of books"""
    return jsonify({'books': STUB_BOOKS})

@bp.route('/books/<book_id>')
def get_book(book_id):
    """Return single book"""
    book = next((b for b in STUB_BOOKS if b['id'] == book_id), None)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify({'book': book})

@bp.route('/books/<book_id>/pages')
def get_book_pages(book_id):
    """Return page content"""
    page = request.args.get('page', 1, type=int)
    return jsonify({
        'content': f'<p>محتوى الصفحة {page} من الكتاب {book_id}</p><p>حدثنا عبد الله بن يوسف قال أخبرنا مالك...</p>',
        'page': page,
        'total_pages': 500
    })

@bp.route('/books/<book_id>/toc')
def get_book_toc(book_id):
    """Return table of contents"""
    return jsonify({
        'toc': [
            {'title': 'المقدمة', 'page': 1},
            {'title': 'كتاب الإيمان', 'page': 10},
            {'title': 'كتاب العلم', 'page': 45},
            {'title': 'كتاب الوضوء', 'page': 78},
        ]
    })

@bp.route('/authors')
def get_authors():
    """Return list of authors"""
    return jsonify({'authors': STUB_AUTHORS})

@bp.route('/categories')
def get_categories():
    """Return list of categories"""
    return jsonify({'categories': STUB_CATEGORIES})

@bp.route('/custom-categories')
def get_custom_categories():
    """Return user's custom categories"""
    return jsonify({'categories': []})

@bp.route('/collections')
def get_collections():
    """Return user's collections"""
    return jsonify({'collections': []})

@bp.route('/search')
def search():
    """Search books"""
    q = request.args.get('q', '')
    if not q:
        return jsonify({'results': []})
    
    # Stub search results
    return jsonify({
        'results': [
            {
                'id': '1',
                'book_id': '1',
                'book_title': 'صحيح البخاري',
                'author': 'البخاري',
                'death_date': '256',
                'category': 'كتب السنة',
                'page': 45,
                'snippet': f'...نتيجة بحث عن <mark>{q}</mark> في النص...'
            }
        ]
    })
```

**Register API blueprint in `app/__init__.py`:**
```python
from app.routes import main, api
app.register_blueprint(main.bp)
app.register_blueprint(api.bp)
```

**Acceptance Criteria:**
- [ ] GET /api/filters returns books, authors, categories
- [ ] GET /api/books returns list of books
- [ ] GET /api/authors returns list of authors
- [ ] GET /api/categories returns list of categories
- [ ] GET /api/search?q=test returns results
- [ ] All endpoints return valid JSON

---

### Story 2.2: Connect Frontend to API

Update templates to fetch from API instead of using inline sample data.

**Changes needed in each template:**

In `search.html`, the `loadFilters()` function should now work because the API exists.

Test by:
1. Open browser to /search
2. Check browser console for errors
3. Verify filter dropdowns populate with data from API

**Acceptance Criteria:**
- [ ] Search page filter dropdowns show books from API
- [ ] Books page shows books from API
- [ ] Authors page shows authors from API
- [ ] Categories page shows categories from API
- [ ] No console errors about failed fetch requests

---

## Phase 3: Database Setup

**Goal:** Replace stub data with SQLite database

### Story 3.1: Create Database Schema

`app/database.py`:
```python
import sqlite3
import os

def get_db_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'granada.db')

def get_db():
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author_id TEXT,
            category_id INTEGER,
            death_date INTEGER,
            file_size INTEGER,
            is_downloaded INTEGER DEFAULT 0,
            is_owned INTEGER DEFAULT 0,
            source TEXT DEFAULT 'openiti',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Pages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT NOT NULL,
            page_num INTEGER NOT NULL,
            content TEXT,
            content_normalized TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')
    
    # FTS5 index for search
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
            content,
            content='pages',
            content_rowid='id',
            tokenize='unicode61'
        )
    ''')
    
    # Authors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            death_date INTEGER,
            bio TEXT
        )
    ''')
    
    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            book_count INTEGER DEFAULT 0
        )
    ''')
    
    # Custom categories (Granada feature)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Collections (Granada feature)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collection_books (
            collection_id INTEGER,
            book_id TEXT,
            position INTEGER,
            is_complete INTEGER DEFAULT 0,
            current_page INTEGER,
            FOREIGN KEY (collection_id) REFERENCES collections(id),
            FOREIGN KEY (book_id) REFERENCES books(id),
            PRIMARY KEY (collection_id, book_id)
        )
    ''')
    
    # Reading progress (Granada feature)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reading_progress (
            book_id TEXT PRIMARY KEY,
            current_page INTEGER DEFAULT 1,
            total_pages INTEGER,
            last_read TEXT,
            is_complete INTEGER DEFAULT 0,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')
    
    # Search history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            results_count INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized at:", get_db_path())

def seed_db():
    """Insert sample data for testing"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Seed categories
    categories = [
        (1, 'العقيدة', 808),
        (2, 'الفرق والردود', 151),
        (3, 'التفسير', 272),
        (4, 'علوم القرآن وأصول التفسير', 310),
        (5, 'التجويد والقراءات', 151),
        (6, 'كتب السنة', 1241),
        (7, 'شروح الحديث', 264),
        (8, 'التخريج والأطراف', 129),
        (9, 'العلل والسؤلات الحديثية', 78),
        (10, 'علوم الحديث', 320),
    ]
    cursor.executemany(
        'INSERT OR REPLACE INTO categories (id, name, book_count) VALUES (?, ?, ?)',
        categories
    )
    
    # Seed authors
    authors = [
        ('bukhari', 'البخاري', 256),
        ('muslim', 'مسلم بن الحجاج', 261),
        ('abudawud', 'أبو داود السجستاني', 275),
        ('tirmidhi', 'الترمذي', 279),
        ('nasai', 'النسائي', 303),
        ('ibnmajah', 'ابن ماجه', 273),
        ('malik', 'مالك بن أنس', 179),
        ('ahmad', 'أحمد بن حنبل', 241),
        ('ibntaymiyyah', 'ابن تيمية', 728),
        ('ibnalqayyim', 'ابن القيم', 751),
    ]
    cursor.executemany(
        'INSERT OR REPLACE INTO authors (id, name, death_date) VALUES (?, ?, ?)',
        authors
    )
    
    # Seed books
    books = [
        ('sahih-bukhari', 'صحيح البخاري', 'bukhari', 6, 256, 52428800, 1, 0),
        ('sahih-muslim', 'صحيح مسلم', 'muslim', 6, 261, 41943040, 1, 0),
        ('sunan-abi-dawud', 'سنن أبي داود', 'abudawud', 6, 275, 31457280, 0, 0),
        ('jami-tirmidhi', 'جامع الترمذي', 'tirmidhi', 6, 279, 28311552, 0, 0),
        ('sunan-nasai', 'سنن النسائي', 'nasai', 6, 303, 25165824, 0, 0),
    ]
    cursor.executemany(
        'INSERT OR REPLACE INTO books (id, title, author_id, category_id, death_date, file_size, is_downloaded, is_owned) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        books
    )
    
    conn.commit()
    conn.close()
    print("Database seeded with sample data")

if __name__ == '__main__':
    init_db()
    seed_db()
```

**Acceptance Criteria:**
- [ ] Running `python -m app.database` creates database file
- [ ] Database contains all tables
- [ ] Sample data is inserted

---

### Story 3.2: Update API to Use Database

Update `app/routes/api.py` to query database instead of stub data.

Replace stub data with database queries:

```python
from flask import Blueprint, jsonify, request
from app.database import get_db

bp = Blueprint('api', __name__, url_prefix='/api')

def to_arabic_numeral(num):
    """Convert Western numerals to Arabic"""
    arabic = '٠١٢٣٤٥٦٧٨٩'
    return ''.join(arabic[int(d)] for d in str(num))

@bp.route('/filters')
def get_filters():
    conn = get_db()
    
    books = conn.execute('''
        SELECT id, title FROM books WHERE is_downloaded = 1
    ''').fetchall()
    
    authors = conn.execute('''
        SELECT DISTINCT a.id, a.name 
        FROM authors a
        JOIN books b ON b.author_id = a.id
        WHERE b.is_downloaded = 1
    ''').fetchall()
    
    categories = conn.execute('SELECT id, name FROM categories').fetchall()
    
    conn.close()
    
    return jsonify({
        'books': [{'id': b['id'], 'title': b['title']} for b in books],
        'authors': [{'id': a['id'], 'name': a['name']} for a in authors],
        'categories': [{'id': c['id'], 'name': c['name']} for c in categories]
    })

@bp.route('/books')
def get_books():
    conn = get_db()
    books = conn.execute('''
        SELECT b.*, a.name as author_name, c.name as category_name
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.id
        LEFT JOIN categories c ON b.category_id = c.id
        WHERE b.is_downloaded = 1
        ORDER BY b.title
    ''').fetchall()
    conn.close()
    
    return jsonify({
        'books': [{
            'id': b['id'],
            'title': b['title'],
            'author': b['author_name'],
            'author_id': b['author_id'],
            'death_date': str(b['death_date']) if b['death_date'] else None,
            'category': b['category_name'],
            'category_id': b['category_id'],
            'file_size': b['file_size'],
            'is_owned': bool(b['is_owned']),
            'is_downloaded': bool(b['is_downloaded'])
        } for b in books]
    })

@bp.route('/authors')
def get_authors():
    conn = get_db()
    authors = conn.execute('''
        SELECT a.*, COUNT(b.id) as book_count
        FROM authors a
        LEFT JOIN books b ON b.author_id = a.id AND b.is_downloaded = 1
        GROUP BY a.id
        ORDER BY a.death_date
    ''').fetchall()
    conn.close()
    
    return jsonify({
        'authors': [{
            'id': a['id'],
            'name': a['name'],
            'death_date': str(a['death_date']) if a['death_date'] else None,
            'book_count': a['book_count']
        } for a in authors]
    })

@bp.route('/categories')
def get_categories():
    conn = get_db()
    categories = conn.execute('''
        SELECT * FROM categories ORDER BY id
    ''').fetchall()
    conn.close()
    
    return jsonify({
        'categories': [{
            'id': c['id'],
            'number': to_arabic_numeral(c['id']),
            'name': c['name'],
            'book_count': c['book_count']
        } for c in categories]
    })

# ... rest of endpoints
```

**Acceptance Criteria:**
- [ ] /api/books returns data from database
- [ ] /api/authors returns data from database
- [ ] /api/categories returns data from database
- [ ] Frontend displays database data correctly

---

## Phase 4: Full-Text Search

**Goal:** Implement FTS5-based Arabic search

### Story 4.1: Arabic Normalization

`app/normalize.py`:
```python
"""Arabic text normalization for search"""

def strip_tashkeel(text):
    """Remove Arabic diacritical marks"""
    tashkeel = (
        '\u064B',  # fathatan
        '\u064C',  # dammatan
        '\u064D',  # kasratan
        '\u064E',  # fatha
        '\u064F',  # damma
        '\u0650',  # kasra
        '\u0651',  # shadda
        '\u0652',  # sukun
        '\u0670',  # superscript alef
    )
    for mark in tashkeel:
        text = text.replace(mark, '')
    return text

def strip_tatweel(text):
    """Remove kashida (decorative elongation)"""
    return text.replace('\u0640', '')

def normalize_alef(text):
    """Normalize alef variants to plain alef"""
    alef_variants = ['أ', 'إ', 'آ', 'ٱ']
    for variant in alef_variants:
        text = text.replace(variant, 'ا')
    return text

def normalize_alef_maksura(text):
    """Normalize alef maksura to ya"""
    return text.replace('ى', 'ي')

def normalize_teh_marbuta(text):
    """Normalize teh marbuta to heh (optional, increases recall)"""
    return text.replace('ة', 'ه')

def normalize_arabic(text, aggressive=False):
    """
    Normalize Arabic text for search indexing and querying.
    
    Args:
        text: Arabic text to normalize
        aggressive: If True, also normalize teh marbuta (may over-match)
    
    Returns:
        Normalized text
    """
    if not text:
        return ''
    
    text = strip_tashkeel(text)
    text = strip_tatweel(text)
    text = normalize_alef(text)
    text = normalize_alef_maksura(text)
    
    if aggressive:
        text = normalize_teh_marbuta(text)
    
    return text
```

### Story 4.2: Search Implementation

`app/search.py`:
```python
"""Full-text search using SQLite FTS5"""

from app.database import get_db
from app.normalize import normalize_arabic

def search_books(query, book_ids=None, author_ids=None, category_ids=None, limit=50):
    """
    Search book content using FTS5.
    
    Args:
        query: Search query (Arabic text)
        book_ids: Optional list of book IDs to filter
        author_ids: Optional list of author IDs to filter
        category_ids: Optional list of category IDs to filter
        limit: Maximum results to return
    
    Returns:
        List of search results with snippets
    """
    if not query or len(query) < 2:
        return []
    
    # Normalize query
    normalized_query = normalize_arabic(query)
    
    conn = get_db()
    
    # Build query
    sql = '''
        SELECT 
            p.id,
            p.book_id,
            p.page_num,
            b.title as book_title,
            a.name as author_name,
            a.death_date,
            c.name as category_name,
            snippet(pages_fts, 0, '<mark>', '</mark>', '...', 64) as snippet,
            bm25(pages_fts) as rank
        FROM pages_fts
        JOIN pages p ON pages_fts.rowid = p.id
        JOIN books b ON p.book_id = b.id
        LEFT JOIN authors a ON b.author_id = a.id
        LEFT JOIN categories c ON b.category_id = c.id
        WHERE pages_fts MATCH ?
    '''
    
    params = [normalized_query]
    
    # Add filters
    if book_ids:
        placeholders = ','.join('?' * len(book_ids))
        sql += f' AND b.id IN ({placeholders})'
        params.extend(book_ids)
    
    if author_ids:
        placeholders = ','.join('?' * len(author_ids))
        sql += f' AND b.author_id IN ({placeholders})'
        params.extend(author_ids)
    
    if category_ids:
        placeholders = ','.join('?' * len(category_ids))
        sql += f' AND b.category_id IN ({placeholders})'
        params.extend(category_ids)
    
    sql += ' ORDER BY rank LIMIT ?'
    params.append(limit)
    
    try:
        results = conn.execute(sql, params).fetchall()
    except Exception as e:
        print(f"Search error: {e}")
        results = []
    
    conn.close()
    
    return [{
        'id': str(r['id']),
        'book_id': r['book_id'],
        'book_title': r['book_title'],
        'author': r['author_name'],
        'death_date': str(r['death_date']) if r['death_date'] else None,
        'category': r['category_name'],
        'page': r['page_num'],
        'snippet': r['snippet']
    } for r in results]

def index_book_content(book_id, pages):
    """
    Index book pages for search.
    
    Args:
        book_id: Book ID
        pages: List of (page_num, content) tuples
    """
    conn = get_db()
    cursor = conn.cursor()
    
    for page_num, content in pages:
        normalized = normalize_arabic(content)
        
        # Insert page
        cursor.execute('''
            INSERT INTO pages (book_id, page_num, content, content_normalized)
            VALUES (?, ?, ?, ?)
        ''', (book_id, page_num, content, normalized))
        
        page_id = cursor.lastrowid
        
        # Index in FTS
        cursor.execute('''
            INSERT INTO pages_fts (rowid, content)
            VALUES (?, ?)
        ''', (page_id, normalized))
    
    conn.commit()
    conn.close()
```

Update API search endpoint:
```python
@bp.route('/search')
def search():
    from app.search import search_books
    
    q = request.args.get('q', '')
    books = request.args.get('books', '')
    authors = request.args.get('authors', '')
    categories = request.args.get('categories', '')
    
    book_ids = books.split(',') if books else None
    author_ids = authors.split(',') if authors else None
    category_ids = [int(c) for c in categories.split(',')] if categories else None
    
    results = search_books(q, book_ids, author_ids, category_ids)
    
    return jsonify({'results': results})
```

**Acceptance Criteria:**
- [ ] Search finds Arabic text with diacritics stripped
- [ ] Search respects book/author/category filters
- [ ] Results include highlighted snippets
- [ ] Empty/short queries return empty results

---

## Phase 5: Granada Features

**Goal:** Implement Granada-specific features (collections, ownership, custom categories)

### Story 5.1: Collections API

Add to `app/routes/api.py`:
```python
@bp.route('/collections', methods=['GET'])
def get_collections():
    conn = get_db()
    collections = conn.execute('SELECT * FROM collections ORDER BY created_at DESC').fetchall()
    
    result = []
    for c in collections:
        books = conn.execute('''
            SELECT cb.*, b.title
            FROM collection_books cb
            JOIN books b ON cb.book_id = b.id
            WHERE cb.collection_id = ?
            ORDER BY cb.position
        ''', (c['id'],)).fetchall()
        
        complete = sum(1 for b in books if b['is_complete'])
        progress = int((complete / len(books) * 100)) if books else 0
        
        result.append({
            'id': c['id'],
            'name': c['name'],
            'progress': progress,
            'books': [{
                'id': b['book_id'],
                'title': b['title'],
                'is_complete': bool(b['is_complete']),
                'current_page': b['current_page']
            } for b in books]
        })
    
    conn.close()
    return jsonify({'collections': result})

@bp.route('/collections', methods=['POST'])
def create_collection():
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'error': 'Name required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO collections (name) VALUES (?)', (name,))
    collection_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'collection': {'id': collection_id, 'name': name}})

@bp.route('/collections/<int:collection_id>', methods=['DELETE'])
def delete_collection(collection_id):
    conn = get_db()
    conn.execute('DELETE FROM collection_books WHERE collection_id = ?', (collection_id,))
    conn.execute('DELETE FROM collections WHERE id = ?', (collection_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@bp.route('/collections/<int:collection_id>/books', methods=['POST'])
def add_book_to_collection(collection_id):
    data = request.get_json()
    book_id = data.get('book_id')
    
    conn = get_db()
    # Get next position
    pos = conn.execute('''
        SELECT COALESCE(MAX(position), 0) + 1 FROM collection_books WHERE collection_id = ?
    ''', (collection_id,)).fetchone()[0]
    
    conn.execute('''
        INSERT OR REPLACE INTO collection_books (collection_id, book_id, position)
        VALUES (?, ?, ?)
    ''', (collection_id, book_id, pos))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})
```

### Story 5.2: Book Ownership Toggle

```python
@bp.route('/books/<book_id>/owned', methods=['PUT'])
def toggle_owned(book_id):
    data = request.get_json()
    is_owned = 1 if data.get('is_owned') else 0
    
    conn = get_db()
    conn.execute('UPDATE books SET is_owned = ? WHERE id = ?', (is_owned, book_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})
```

### Story 5.3: Custom Categories

```python
@bp.route('/custom-categories', methods=['GET'])
def get_custom_categories():
    conn = get_db()
    categories = conn.execute('''
        SELECT cc.*, COUNT(bcc.book_id) as book_count
        FROM custom_categories cc
        LEFT JOIN book_custom_categories bcc ON cc.id = bcc.category_id
        GROUP BY cc.id
        ORDER BY cc.created_at DESC
    ''').fetchall()
    conn.close()
    
    return jsonify({
        'categories': [{
            'id': c['id'],
            'name': c['name'],
            'book_count': c['book_count']
        } for c in categories]
    })

@bp.route('/custom-categories', methods=['POST'])
def create_custom_category():
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'error': 'Name required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO custom_categories (name) VALUES (?)', (name,))
    cat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'category': {'id': cat_id, 'name': name, 'book_count': 0}})

@bp.route('/custom-categories/<int:cat_id>', methods=['DELETE'])
def delete_custom_category(cat_id):
    conn = get_db()
    conn.execute('DELETE FROM book_custom_categories WHERE category_id = ?', (cat_id,))
    conn.execute('DELETE FROM custom_categories WHERE id = ?', (cat_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})
```

**Acceptance Criteria:**
- [ ] Can create/delete collections
- [ ] Can add/remove books from collections
- [ ] Collection progress calculates correctly
- [ ] Can toggle book ownership
- [ ] Can create/delete custom categories

---

## Phase 6: OpenITI Integration

**Goal:** Browse and download books from OpenITI corpus

### Story 6.1: OpenITI Catalog

`app/openiti.py`:
```python
"""OpenITI corpus integration"""

import os
import urllib.request
import json

OPENITI_METADATA_URL = "https://raw.githubusercontent.com/OpenITI/RELEASE/main/metadata/OpenITI_metadata_complete.csv"

def get_openiti_catalog():
    """
    Get OpenITI book catalog.
    In production, this would fetch from GitHub or local cache.
    """
    # For now, return sample data
    return [
        {
            'id': 'Shamela0023790',
            'title': 'صحيح البخاري',
            'author': 'البخاري',
            'death_date': '256',
            'category': 'كتب السنة',
            'file_size': 52428800
        },
        # ... more books
    ]

def download_openiti_book(book_id):
    """
    Download a book from OpenITI.
    
    Returns:
        List of (page_num, content) tuples
    """
    # In production, this would:
    # 1. Fetch from GitHub
    # 2. Parse the markdown format
    # 3. Split into pages
    # 4. Return content
    pass
```

### Story 6.2: Download Endpoint

```python
@bp.route('/openiti/books')
def get_openiti_books():
    from app.openiti import get_openiti_catalog
    
    search = request.args.get('search', '')
    catalog = get_openiti_catalog()
    
    if search:
        catalog = [b for b in catalog if search in b['title'] or search in b['author']]
    
    return jsonify({'books': catalog})

@bp.route('/openiti/books/<book_id>/download', methods=['POST'])
def download_openiti_book(book_id):
    from app.openiti import download_openiti_book
    from app.search import index_book_content
    
    # Download book content
    pages = download_openiti_book(book_id)
    
    if not pages:
        return jsonify({'error': 'Download failed'}), 500
    
    # Save to database
    conn = get_db()
    # ... insert book metadata
    # ... insert pages
    conn.commit()
    conn.close()
    
    # Index for search
    index_book_content(book_id, pages)
    
    return jsonify({'success': True})
```

---

## Phase 7: Polish & Packaging

### Story 7.1: Error Handling

Add proper error handling to all API endpoints:
- Try/catch around database operations
- Return appropriate HTTP status codes
- Log errors for debugging

### Story 7.2: Loading States

Ensure all templates show loading indicators:
- During API calls
- During search
- During book downloads

### Story 7.3: PyInstaller Packaging

`build.py`:
```python
import PyInstaller.__main__
import os

PyInstaller.__main__.run([
    'app.py',
    '--onefile',
    '--windowed',
    '--name=Granada',
    '--add-data=templates:templates',
    '--add-data=static:static',
    '--icon=static/icon.ico',
])
```

`requirements.txt` (add):
```
pyinstaller==6.0.0
```

---

## Testing Checklist

### Visual Testing
- [ ] Each page matches turath.io screenshots
- [ ] RTL layout correct throughout
- [ ] Dark theme colors match
- [ ] Arabic text renders correctly
- [ ] Responsive on mobile (375px width)

### Functional Testing
- [ ] Navigation between all pages
- [ ] Search with Arabic text
- [ ] Filter dropdowns work
- [ ] Active filter tags appear/remove
- [ ] Book download flow
- [ ] Book reader navigation
- [ ] Collections CRUD
- [ ] Settings save/load

### Edge Cases
- [ ] Empty search results
- [ ] No downloaded books
- [ ] Very long book titles (truncation)
- [ ] Network errors (graceful handling)
- [ ] Database errors (graceful handling)

---

## Reference Files

All templates are already created in `/templates/`:
- base.html
- search.html
- books.html
- authors.html
- categories.html
- collections.html
- settings.html
- reader.html
- wizard.html

CSS is already created in `/static/css/main.css`

PRD document: `GRANADA-PRD.md`
