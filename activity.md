# Granada v2 Activity Log

---

## 2026-01-16: v1.0.0 Release

### Notebook Enhancements
- Added export functionality with individual note selection via checkboxes
- Export notes as separate Markdown files for Obsidian import
- Fixed sidebar toggle positioning (dynamic left value based on AI chat state)
- Fixed new note button - API now allows creating notes with empty content

### Search Improvements
- Added turath.io-style search options UI
- Radio buttons for search precision: بعض الكلمات, كل الكلمات, كل الكلمات متتالية
- Checkboxes for additional search options
- Updated `search.py` with `_build_fts_query()` method for new parameters

### Distribution & Packaging
- Updated `config.py` with PyInstaller-aware path resolution
  - `get_base_dir()` - user data directory (next to executable)
  - `get_resource_dir()` - bundled resources (`sys._MEIPASS`)
- Updated `granada.spec` with hidden imports and icon configuration
- Built Windows executable: 45 MB uncompressed, 18.5 MB zipped

### Bundled Content
- Downloaded and bundled sample books from OpenITI:
  - Quran
  - Riyadh al-Salihin
- Added `import_bundled_books()` function for auto-import on first run

### Branding & Icons
- Created `static/icons/granada.ico` (multi-size: 16, 32, 48, 256px)
- Created `static/favicon.ico`
- Added favicon route in `main.py`
- Updated `base.html` with favicon links

### Git & GitHub
- Fixed corrupted `.gitignore` (was UTF-16 encoded)
- Committed 37 files to GitHub
- Created GitHub Release v1.0.0 with `Granada-v1.0.0-win64.zip`

### Release URL
https://github.com/jbradf0rd/projectgranada/releases/tag/v1.0.0

---

## 2026-01-13: Task 1.1 - Create minimal Flask app structure

### Changes made:
- Created `requirements.txt` with Flask==3.0.0 and python-dotenv
- Created `config.py` with SECRET_KEY and DATABASE_PATH configuration
- Created `app/__init__.py` with create_app factory function
- Created `app/routes/__init__.py` (routes package)
- Created `app/routes/main.py` with routes for all pages (/, /search, /books, /authors, /categories, /collections, /settings, /reader, /wizard)
- Created `app.py` entry point

### Commands run:
- `pip install Flask==3.0.0 python-dotenv` - installed dependencies
- `python app.py` - verified app starts successfully on port 5000

### Verified:
- Flask app starts without errors
- Server runs on http://127.0.0.1:5000

---