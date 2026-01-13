# Granada v2 Activity Log

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