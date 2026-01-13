{
  "tasks": [
    {
      "id": "1.1",
      "category": "Phase 1: Flask Setup",
      "description": "Create minimal Flask app structure with requirements.txt, config.py, app/__init__.py, app/routes/main.py, and app.py",
      "steps": [
        "Create requirements.txt with Flask==3.0.0 and python-dotenv",
        "Create config.py with SECRET_KEY and DATABASE_PATH",
        "Create app/__init__.py with create_app factory",
        "Create app/routes/__init__.py",
        "Create app/routes/main.py with all page routes",
        "Create app.py entry point"
      ],
      "passes": false
    },
    {
      "id": "1.2",
      "category": "Phase 1: Flask Setup",
      "description": "Verify all templates render without errors",
      "steps": [
        "Run flask app on port 5000",
        "Test each route: /, /books, /authors, /categories, /collections, /settings",
        "Verify navigation highlights active page",
        "Verify CSS loads correctly (dark theme visible)",
        "Fix any Jinja2 template errors"
      ],
      "passes": false
    },
    {
      "id": "2.1",
      "category": "Phase 2: API Endpoints",
      "description": "Create API blueprint with stub data",
      "steps": [
        "Create app/routes/api.py with Blueprint",
        "Add stub data for books, authors, categories",
        "Implement GET /api/filters endpoint",
        "Implement GET /api/books endpoint",
        "Implement GET /api/authors endpoint",
        "Implement GET /api/categories endpoint",
        "Implement GET /api/search endpoint",
        "Register API blueprint in app/__init__.py"
      ],
      "passes": false
    },
    {
      "id": "2.2",
      "category": "Phase 2: API Endpoints",
      "description": "Verify frontend fetches from API",
      "steps": [
        "Open /search in browser",
        "Check browser console for errors",
        "Verify filter dropdowns populate with API data",
        "Verify books page shows books from API",
        "Verify authors page shows authors from API"
      ],
      "passes": false
    },
    {
      "id": "3.1",
      "category": "Phase 3: Database",
      "description": "Create SQLite database with schema",
      "steps": [
        "Create app/database.py with get_db() and init_db()",
        "Create books table",
        "Create pages table",
        "Create pages_fts FTS5 virtual table",
        "Create authors table",
        "Create categories table",
        "Create custom_categories table",
        "Create collections and collection_books tables",
        "Create reading_progress table",
        "Create search_history table"
      ],
      "passes": false
    },
    {
      "id": "3.2",
      "category": "Phase 3: Database",
      "description": "Seed database and update API to use it",
      "steps": [
        "Create seed_db() function with sample data",
        "Add 10 categories with Arabic names",
        "Add 10 authors with death dates",
        "Add 5 sample books",
        "Update API endpoints to query database",
        "Verify frontend displays database data"
      ],
      "passes": false
    },
    {
      "id": "4.1",
      "category": "Phase 4: Search",
      "description": "Implement Arabic text normalization",
      "steps": [
        "Create app/normalize.py",
        "Implement strip_tashkeel() for diacritics",
        "Implement strip_tatweel() for kashida",
        "Implement normalize_alef() for alef variants",
        "Implement normalize_alef_maksura()",
        "Implement normalize_arabic() main function"
      ],
      "passes": false
    },
    {
      "id": "4.2",
      "category": "Phase 4: Search",
      "description": "Implement FTS5 search",
      "steps": [
        "Create app/search.py",
        "Implement search_books() with FTS5 MATCH",
        "Add filter support for books, authors, categories",
        "Add snippet() for highlighted results",
        "Add bm25() for ranking",
        "Update /api/search to use search_books()",
        "Test search with Arabic text"
      ],
      "passes": false
    }
  ]
}