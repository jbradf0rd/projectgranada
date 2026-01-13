# Granada v2 Quick Start

## What's Included

This package contains:

```
granada-v2/
├── GRANADA-PRD.md          # Full product requirements
├── RALPH-STORIES.md        # Implementation phases for Ralph
├── static/css/main.css     # Complete CSS (turath.io clone)
└── templates/              # All 9 HTML templates
    ├── base.html           # Navigation + layout
    ├── search.html         # Search with filter system
    ├── books.html          # Books with tabs
    ├── authors.html        # Authors listing
    ├── categories.html     # Categories + custom categories
    ├── collections.html    # Reading collections (Granada)
    ├── settings.html       # Settings + AI config (Granada)
    ├── reader.html         # Book reader
    └── wizard.html         # First-run wizard
```

## How to Use with Ralph

1. **Extract** this folder to your working directory
2. **Open Ralph** and give it this prompt:

```
Read RALPH-STORIES.md in the granada-v2 folder. 
Start with Phase 1: Create the minimal Flask app structure.
The templates and CSS are already created - just wire them up.
```

3. **Work through phases** one at a time:
   - Phase 1: Flask serving templates
   - Phase 2: API endpoints with stub data
   - Phase 3: SQLite database
   - Phase 4: Full-text search
   - Phase 5: Granada features
   - Phase 6: OpenITI integration
   - Phase 7: Packaging

## Key Points for Ralph

- **Templates are complete** - don't recreate them
- **CSS is complete** - don't modify unless fixing bugs
- **Follow phases in order** - each builds on previous
- **Test after each phase** - acceptance criteria included
- **Visual fidelity is critical** - must match turath.io exactly

## Testing Templates Before Backend

You can test templates with a minimal Flask setup:

```python
# test_app.py
from flask import Flask, render_template

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def search():
    return render_template('search.html', active_page='search')

@app.route('/books')
def books():
    return render_template('books.html', active_page='books')

# ... add other routes

if __name__ == '__main__':
    app.run(debug=True)
```

## Reference

- turath.io - the UI we're cloning
- GRANADA-PRD.md - full specifications
- RALPH-STORIES.md - implementation guide
