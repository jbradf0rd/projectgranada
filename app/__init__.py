"""
Granada v2 Flask Application Factory
"""
import os
from flask import Flask

from config import config, DATA_DIR, RESOURCE_DIR


def migrate_database(db_path):
    """Run database migrations to add new columns."""
    import sqlite3
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()

    # Get existing columns in pages table
    cursor.execute("PRAGMA table_info(pages)")
    page_columns = {row[1] for row in cursor.fetchall()}

    # Add volume column if missing
    if 'volume' not in page_columns:
        cursor.execute('ALTER TABLE pages ADD COLUMN volume INTEGER DEFAULT 1')
        print("Added 'volume' column to pages table")

    # Add original_page column if missing
    if 'original_page' not in page_columns:
        cursor.execute('ALTER TABLE pages ADD COLUMN original_page INTEGER')
        print("Added 'original_page' column to pages table")

    # Get existing columns in books table
    cursor.execute("PRAGMA table_info(books)")
    book_columns = {row[1] for row in cursor.fetchall()}

    # All metadata columns to add if missing
    book_columns_to_add = [
        ('volumes_count', 'INTEGER DEFAULT 1'),
        ('editor', 'TEXT'),
        ('edition', 'TEXT'),
        ('publisher', 'TEXT'),
        # Extended OpenITI metadata columns
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

    for col_name, col_type in book_columns_to_add:
        if col_name not in book_columns:
            cursor.execute(f'ALTER TABLE books ADD COLUMN {col_name} {col_type}')
            print(f"Added '{col_name}' column to books table")

    # Create index if it doesn't exist
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pages_volume_page ON pages(book_id, volume, original_page)')
    except sqlite3.OperationalError:
        pass  # Index already exists

    conn.commit()
    conn.close()


def import_bundled_books(db_path):
    """Import bundled starter books on first run."""
    import sqlite3
    from pathlib import Path

    # Check for bundled_books directory
    bundled_dir = os.path.join(RESOURCE_DIR, 'bundled_books')
    if not os.path.exists(bundled_dir):
        return

    # Get list of book files
    book_files = [f for f in os.listdir(bundled_dir)
                  if f.endswith('.mARkdown') or f.endswith('.md') or f.endswith('.txt')]

    if not book_files:
        return

    # Check if we've already imported bundled books
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'bundled_books_imported'")
    row = cursor.fetchone()
    conn.close()

    if row and row[0] == 'true':
        return  # Already imported

    print(f"Importing {len(book_files)} bundled books...")

    # Import each book
    from app.book_upload import BookUploader
    uploader = BookUploader(db_path)

    imported_count = 0
    for book_file in book_files:
        file_path = os.path.join(bundled_dir, book_file)
        try:
            result = uploader.upload_file(file_path, category_id=1)
            if result.get('status') == 'success':
                imported_count += 1
                print(f"  Imported: {result.get('book', {}).get('title', book_file)}")
            else:
                print(f"  Skipped {book_file}: {result.get('message', 'unknown error')}")
        except Exception as e:
            print(f"  Error importing {book_file}: {e}")

    # Mark as imported
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value) VALUES ('bundled_books_imported', 'true')
    ''')
    conn.commit()
    conn.close()

    print(f"Imported {imported_count} bundled books.")


def cleanup_sample_data(db_path):
    """Remove old sample data entries that conflict with OpenITI downloads."""
    import sqlite3
    conn = sqlite3.connect(db_path, timeout=30)
    cursor = conn.cursor()

    # Sample data IDs that should be removed (they conflict with OpenITI IDs)
    sample_book_ids = ['sahih_bukhari', 'sahih_muslim', 'sunan_abi_dawud']
    sample_author_ids = ['bukhari', 'muslim', 'abu_dawud', 'tirmidhi', 'nasai']

    # Remove sample books and their related data
    for book_id in sample_book_ids:
        cursor.execute('DELETE FROM pages WHERE book_id = ?', (book_id,))
        cursor.execute('DELETE FROM pages_fts WHERE book_id = ?', (book_id,))
        cursor.execute('DELETE FROM reading_progress WHERE book_id = ?', (book_id,))
        cursor.execute('DELETE FROM collection_books WHERE book_id = ?', (book_id,))
        cursor.execute('DELETE FROM book_custom_categories WHERE book_id = ?', (book_id,))
        cursor.execute('DELETE FROM books WHERE id = ?', (book_id,))

    # Remove sample authors (only if they have no books left)
    for author_id in sample_author_ids:
        cursor.execute('SELECT COUNT(*) FROM books WHERE author_id = ?', (author_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('DELETE FROM authors WHERE id = ?', (author_id,))

    conn.commit()
    conn.close()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')

    # Get the config class first to access folder paths
    config_class = config[config_name]

    app = Flask(__name__,
                static_folder=config_class.STATIC_FOLDER,
                template_folder=config_class.TEMPLATES_FOLDER)

    # Load configuration
    app.config.from_object(config_class)

    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Initialize database
    from app.models import init_db
    with app.app_context():
        init_db(app.config['DATABASE_PATH'])
        # Run migrations for new columns
        migrate_database(app.config['DATABASE_PATH'])
        # Clean up old sample data that creates duplicates
        cleanup_sample_data(app.config['DATABASE_PATH'])
        # Import bundled books on first run
        import_bundled_books(app.config['DATABASE_PATH'])

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
