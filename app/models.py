"""
Granada v2 Database Models
SQLite with FTS5 for full-text search
"""
import sqlite3
import os


def get_db_connection(db_path):
    """Create a database connection with timeout and proper settings."""
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrency
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
    return conn


def init_db(db_path):
    """Initialize the database with schema."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.executescript('''
        -- Books metadata
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author_id TEXT,
            category_id INTEGER,
            death_date INTEGER,
            file_size INTEGER,
            is_downloaded INTEGER DEFAULT 0,
            is_owned INTEGER DEFAULT 0,
            download_date TEXT,
            source TEXT DEFAULT 'upload',
            volumes_count INTEGER DEFAULT 1,
            editor TEXT,
            edition TEXT,
            publisher TEXT,
            -- Extended metadata fields
            author_name TEXT,
            author_aka TEXT,
            author_born INTEGER,
            subtitle TEXT,
            alt_title TEXT,
            subject TEXT,
            language TEXT,
            publication_place TEXT,
            publication_year TEXT,
            isbn TEXT,
            page_count INTEGER,
            openiti_uri TEXT,
            FOREIGN KEY (author_id) REFERENCES authors(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        -- Book pages/content
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY,
            book_id TEXT,
            page_num INTEGER,
            volume INTEGER DEFAULT 1,
            original_page INTEGER,
            content TEXT,
            content_normalized TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id)
        );

        -- Create indexes for pages
        CREATE INDEX IF NOT EXISTS idx_pages_book ON pages(book_id);
        CREATE INDEX IF NOT EXISTS idx_pages_book_page ON pages(book_id, page_num);
        -- Note: idx_pages_volume_page is created by migration after columns are added

        -- Authors
        CREATE TABLE IF NOT EXISTS authors (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            death_date INTEGER,
            bio TEXT
        );

        -- Create index for authors by death date
        CREATE INDEX IF NOT EXISTS idx_authors_death ON authors(death_date);

        -- Categories
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            book_count INTEGER DEFAULT 0
        );

        -- User's custom categories (Granada feature)
        CREATE TABLE IF NOT EXISTS custom_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS book_custom_categories (
            book_id TEXT,
            category_id INTEGER,
            PRIMARY KEY (book_id, category_id),
            FOREIGN KEY (book_id) REFERENCES books(id),
            FOREIGN KEY (category_id) REFERENCES custom_categories(id)
        );

        -- Reading collections (Granada feature)
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS collection_books (
            collection_id INTEGER,
            book_id TEXT,
            position INTEGER,
            PRIMARY KEY (collection_id, book_id),
            FOREIGN KEY (collection_id) REFERENCES collections(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        );

        -- Reading progress (Granada feature)
        CREATE TABLE IF NOT EXISTS reading_progress (
            book_id TEXT PRIMARY KEY,
            current_page INTEGER DEFAULT 1,
            total_pages INTEGER,
            last_read TEXT,
            is_complete INTEGER DEFAULT 0,
            FOREIGN KEY (book_id) REFERENCES books(id)
        );

        -- Search history
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            searched_at TEXT DEFAULT CURRENT_TIMESTAMP,
            results_count INTEGER
        );

        -- Settings
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );

        -- Table of Contents (TOC) entries
        CREATE TABLE IF NOT EXISTS toc_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT NOT NULL,
            title TEXT NOT NULL,
            level INTEGER DEFAULT 1,
            page_num INTEGER,
            position INTEGER,
            FOREIGN KEY (book_id) REFERENCES books(id)
        );

        CREATE INDEX IF NOT EXISTS idx_toc_book ON toc_entries(book_id);
        CREATE INDEX IF NOT EXISTS idx_toc_page ON toc_entries(book_id, page_num);

        -- Notes and annotations (Granada feature)
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_type TEXT,  -- 'manual', 'ai_chat', 'highlight'
            source_ref TEXT    -- JSON: {book_id, page_num, author, title, highlighted_text}
        );

        CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created_at);
        CREATE INDEX IF NOT EXISTS idx_notes_source ON notes(source_type);
    ''')

    # Create FTS5 virtual table for full-text search
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
            book_id,
            page_num,
            content,
            tokenize='unicode61'
        );
    ''')

    conn.commit()
    conn.close()


def run_migrations(db_path):
    """Run database migrations to add new columns."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Get existing columns in books table
    cursor.execute('PRAGMA table_info(books)')
    existing_columns = {row[1] for row in cursor.fetchall()}

    # New columns to add with their definitions
    new_columns = [
        ('author_name', 'TEXT'),
        ('author_aka', 'TEXT'),
        ('author_born', 'INTEGER'),
        ('subtitle', 'TEXT'),
        ('alt_title', 'TEXT'),
        ('subject', 'TEXT'),
        ('language', 'TEXT'),
        ('publication_place', 'TEXT'),
        ('publication_year', 'TEXT'),
        ('isbn', 'TEXT'),
        ('page_count', 'INTEGER'),
        ('openiti_uri', 'TEXT'),
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            try:
                cursor.execute(f'ALTER TABLE books ADD COLUMN {col_name} {col_type}')
                print(f"Added column: {col_name}")
            except sqlite3.OperationalError as e:
                # Column might already exist
                if 'duplicate column' not in str(e).lower():
                    print(f"Warning: Could not add column {col_name}: {e}")

    conn.commit()
    conn.close()


def seed_sample_data(db_path):
    """Insert sample data for development."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Check if data already exists
    cursor.execute('SELECT COUNT(*) FROM authors')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Insert sample authors
    authors = [
        ('bukhari', 'الإمام البخاري', 256, 'محمد بن إسماعيل بن إبراهيم بن المغيرة البخاري'),
        ('muslim', 'الإمام مسلم', 261, 'مسلم بن الحجاج القشيري النيسابوري'),
        ('abu_dawud', 'أبو داود السجستاني', 275, 'سليمان بن الأشعث بن إسحاق السجستاني'),
        ('tirmidhi', 'الترمذي', 279, 'محمد بن عيسى بن سورة الترمذي'),
        ('nasai', 'النسائي', 303, 'أحمد بن شعيب النسائي'),
    ]

    cursor.executemany(
        'INSERT OR IGNORE INTO authors (id, name, death_date, bio) VALUES (?, ?, ?, ?)',
        authors
    )

    # Insert sample categories
    categories = [
        (1, 'كتب السنة', 9),
        (2, 'كتب الفقه', 45),
        (3, 'كتب التفسير', 23),
        (4, 'كتب العقيدة', 18),
        (5, 'كتب السيرة', 12),
        (6, 'كتب التاريخ', 34),
    ]

    cursor.executemany(
        'INSERT OR IGNORE INTO categories (id, name, book_count) VALUES (?, ?, ?)',
        categories
    )

    # Insert sample books
    books = [
        ('sahih_bukhari', 'صحيح البخاري', 'bukhari', 1, 256, 5242880, 1, 0, None, 'openiti'),
        ('sahih_muslim', 'صحيح مسلم', 'muslim', 1, 261, 4718592, 1, 1, None, 'openiti'),
        ('sunan_abi_dawud', 'سنن أبي داود', 'abu_dawud', 1, 275, 3145728, 1, 0, None, 'openiti'),
    ]

    cursor.executemany(
        '''INSERT OR IGNORE INTO books
           (id, title, author_id, category_id, death_date, file_size, is_downloaded, is_owned, download_date, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        books
    )

    # Insert sample collection
    cursor.execute(
        'INSERT OR IGNORE INTO collections (id, name) VALUES (?, ?)',
        (1, 'الكتب التسعة')
    )

    # Add books to collection
    cursor.executemany(
        'INSERT OR IGNORE INTO collection_books (collection_id, book_id, position) VALUES (?, ?, ?)',
        [(1, 'sahih_bukhari', 1), (1, 'sahih_muslim', 2), (1, 'sunan_abi_dawud', 3)]
    )

    # Insert sample reading progress
    cursor.executemany(
        'INSERT OR IGNORE INTO reading_progress (book_id, current_page, total_pages, is_complete) VALUES (?, ?, ?, ?)',
        [
            ('sahih_bukhari', 500, 500, 1),
            ('sahih_muslim', 234, 500, 0),
            ('sunan_abi_dawud', 1, 400, 0),
        ]
    )

    # Insert sample pages with content for search testing
    sample_pages = [
        # Sahih Bukhari pages
        ('sahih_bukhari', 1, '''بسم الله الرحمن الرحيم
كتاب بدء الوحي
باب كيف كان بدء الوحي إلى رسول الله صلى الله عليه وسلم
حدثنا الحميدي عبد الله بن الزبير قال حدثنا سفيان قال حدثنا يحيى بن سعيد الأنصاري قال أخبرني محمد بن إبراهيم التيمي أنه سمع علقمة بن وقاص الليثي يقول سمعت عمر بن الخطاب رضي الله عنه على المنبر قال سمعت رسول الله صلى الله عليه وسلم يقول إنما الأعمال بالنيات وإنما لكل امرئ ما نوى فمن كانت هجرته إلى دنيا يصيبها أو إلى امرأة ينكحها فهجرته إلى ما هاجر إليه'''),

        ('sahih_bukhari', 2, '''باب الوحي
حدثنا عبد الله بن يوسف قال أخبرنا مالك عن هشام بن عروة عن أبيه عن عائشة أم المؤمنين رضي الله عنها أن الحارث بن هشام رضي الله عنه سأل رسول الله صلى الله عليه وسلم فقال يا رسول الله كيف يأتيك الوحي فقال رسول الله صلى الله عليه وسلم أحيانا يأتيني مثل صلصلة الجرس وهو أشده علي فيفصم عني وقد وعيت عنه ما قال وأحيانا يتمثل لي الملك رجلا فيكلمني فأعي ما يقول'''),

        ('sahih_bukhari', 3, '''كتاب الإيمان
باب قول النبي صلى الله عليه وسلم بني الإسلام على خمس
حدثنا عبيد الله بن موسى قال أخبرنا حنظلة بن أبي سفيان عن عكرمة بن خالد عن ابن عمر رضي الله عنهما قال قال رسول الله صلى الله عليه وسلم بني الإسلام على خمس شهادة أن لا إله إلا الله وأن محمدا رسول الله وإقام الصلاة وإيتاء الزكاة والحج وصوم رمضان'''),

        # Sahih Muslim pages
        ('sahih_muslim', 1, '''بسم الله الرحمن الرحيم
مقدمة الإمام مسلم
الحمد لله رب العالمين والعاقبة للمتقين والصلاة والسلام على رسوله محمد وآله أجمعين
أما بعد فإنك يرحمك الله بتوفيق خالقك ذكرت أنك هممت بالفحص عن تعرف جملة الأخبار المأثورة عن رسول الله صلى الله عليه وسلم في سنن الدين وأحكامه'''),

        ('sahih_muslim', 2, '''كتاب الإيمان
باب بيان الإيمان والإسلام والإحسان
حدثني أبو خيثمة زهير بن حرب حدثنا وكيع عن كهمس عن عبد الله بن بريدة عن يحيى بن يعمر قال كان أول من قال في القدر بالبصرة معبد الجهني فانطلقت أنا وحميد بن عبد الرحمن الحميري حاجين أو معتمرين فقلنا لو لقينا أحدا من أصحاب رسول الله صلى الله عليه وسلم فسألناه عما يقول هؤلاء في القدر'''),

        # Sunan Abi Dawud pages
        ('sunan_abi_dawud', 1, '''بسم الله الرحمن الرحيم
كتاب الطهارة
باب فرض الوضوء
حدثنا عبد الله بن مسلمة عن مالك عن صفوان بن سليم عن عطاء بن يسار عن أبي سعيد الخدري أن رسول الله صلى الله عليه وسلم قال الطهور شطر الإيمان والحمد لله تملأ الميزان وسبحان الله والحمد لله تملآن أو تملأ ما بين السماوات والأرض والصلاة نور والصدقة برهان والصبر ضياء والقرآن حجة لك أو عليك'''),

        ('sunan_abi_dawud', 2, '''باب السواك
حدثنا محمد بن كثير أخبرنا سفيان عن أبي الزناد عن الأعرج عن أبي هريرة قال قال رسول الله صلى الله عليه وسلم لولا أن أشق على أمتي لأمرتهم بالسواك عند كل صلاة'''),
    ]

    # Import normalization function
    from app.search import normalize_arabic

    for book_id, page_num, content in sample_pages:
        normalized = normalize_arabic(content)

        cursor.execute('''
            INSERT OR IGNORE INTO pages (book_id, page_num, content, content_normalized)
            VALUES (?, ?, ?, ?)
        ''', (book_id, page_num, content, normalized))

        # Insert into FTS5 index
        cursor.execute('''
            INSERT OR IGNORE INTO pages_fts (book_id, page_num, content)
            VALUES (?, ?, ?)
        ''', (book_id, str(page_num), normalized))

    conn.commit()
    conn.close()
