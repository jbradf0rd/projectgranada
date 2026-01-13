# Granada v2: Product Requirements Document

## Overview

Granada is an offline Arabic book search engine and personal library manager. It replicates turath.io's UI/UX exactly while adding features for personal library management.

**Core Principle:** Visual fidelity to turath.io is paramount. Every pixel, color, and interaction must match.

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask (Python) |
| Database | SQLite with FTS5 |
| Frontend | Jinja2 templates + Alpine.js |
| Styling | Custom CSS (no frameworks) |
| Arabic Processing | PyArabic |
| Text Source | OpenITI corpus |
| Packaging | PyInstaller (Windows .exe) |

---

## Design Specifications

### Colors (Dark Mode - Default)

```css
:root {
  --bg-color: #242426;           /* Main background */
  --bg-card: #2d2d30;            /* Cards, popovers */
  --bg-input: #2d2d30;           /* Input fields */
  --bg-hover: #3a3a3d;           /* Hover states */
  
  --text-primary: #d0d0d0;       /* Main text */
  --text-secondary: #888;        /* Secondary text */
  --text-muted: #666;            /* Muted text */
  
  --border-color: #555;          /* Borders */
  --accent: #5294c4;             /* Links, active states */
  --accent-light: #bbd6e7;       /* Light accent */
  
  --danger: #e57373;             /* Delete, errors */
  --success: #81c784;            /* Success states */
}
```

### Typography

```css
html {
  font-family: 'Kitab', 'Noto Naskh Arabic', system-ui, sans-serif;
  font-size: 18px;               /* Mobile */
  line-height: 1.75;
  direction: rtl;
}

@media (min-width: 576px) { html { font-size: 19px; } }
@media (min-width: 768px) { html { font-size: 21px; } }
@media (min-width: 992px) { html { font-size: 22px; } }
```

### Component Specifications

#### Search Input Container
```css
.search-input-cont {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  width: min(85vw, 20rem);
  margin: 0 auto;
  font-size: 0.9rem;
}
```

#### Popover (Dropdowns)
```css
.popover {
  background: var(--bg-card);
  border-radius: 4px;
  padding: 4px;
  font-size: 0.85rem;
  box-shadow: 0 0 10px rgba(0,0,0,0.5);
  width: 250px;
  max-height: 70vh;
  overflow-y: auto;
}
```

#### Filter Tags (Active Filters)
```css
.filter-tag {
  background: linear-gradient(#38383b, #2f2f32 90%);
  border: 1px solid var(--border-color);
  border-radius: 5px;
  padding: 2px 8px;
  font-size: 0.75rem;
}
```

#### Navigation (Bottom on Mobile, Top on Desktop)
```css
nav {
  position: fixed;
  bottom: 0;                     /* Mobile */
  background: var(--bg-color);
  border-top: 1px solid var(--border-color);
  padding: 6px 0;
}

@media (min-width: 768px) {
  nav {
    top: 0;
    bottom: auto;
    border-top: none;
  }
}
```

---

## Page Specifications

### 1. Search Page (`/` or `/search`)

**Layout:**
- Search input container at top center
- 4 icon buttons inside search box (right side in RTL):
  - History (clock icon)
  - Filter (funnel icon)
  - Sort (lines icon)
  - Settings (gear icon)
- Active filter tags below search box (when filters applied)
- Results count below filters
- Search results list

**Filter Popover Structure:**
```
┌─────────────────────────┐
│ تصفية                   │  <- Title
├─────────────────────────┤
│ > الكتاب (2)            │  <- Expandable section
│   ┌───────────────────┐ │
│   │ كلمات البحث...    │ │  <- Search within filter
│   ├───────────────────┤ │
│   │ ☐ Book title 1    │ │  <- Checkbox list
│   │ ☑ Book title 2    │ │
│   │ ☐ Book title 3    │ │
│   └───────────────────┘ │
├─────────────────────────┤
│ > المؤلف               │
├─────────────────────────┤
│ > القسم                │
├─────────────────────────┤
│ ☐ بحث في الهامش        │  <- Checkbox option
└─────────────────────────┘
```

**Active Filter Tags:**
When a filter is selected, it appears as a tag below the search box:
```
[× الكتاب (2) ▾]  [× المؤلف (1) ▾]
```
- Clicking × removes the filter
- Clicking the tag opens a popover with checkboxes for that filter type

**Search Results Item:**
```
┌─────────────────────────────────────┐
│ Book Title                          │
│ Author Name (ت 123) · Category      │
│                                     │
│ ...search result snippet with       │
│ <mark>highlighted</mark> terms...   │
│                                     │
│ صفحة 45                             │
└─────────────────────────────────────┘
```

### 2. Books Page (`/books`)

**Three Sub-tabs:**
1. **كتبي** - User's downloaded/owned books
2. **مكتبة OpenITI** - Browse OpenITI catalog
3. **رفع كتاب** - Upload custom PDF/text

**Book Item:**
```
┌─────────────────────────────────────┐
│ Book Title                          │
│ Author (ت 456) · Category · 5.2 MB  │
│                        [⬇] [×] [?]  │
└─────────────────────────────────────┘
```
- Download button (if not downloaded)
- Delete button (if downloaded)
- Info button

**Granada Addition - Ownership Badge:**
Books user owns physically show a badge/indicator.

### 3. Authors Page (`/authors`)

**Layout:**
- Search input for filtering authors
- Author count
- Scrollable list sorted by death date (oldest first)

**Author Item:**
```
┌─────────────────────────────────────┐
│ Author Name (ت 123 هـ)          (5) │  <- (5) = book count
└─────────────────────────────────────┘
```

### 4. Categories Page (`/categories`)

**Layout:**
- List of categories with book counts
- Numbered (١، ٢، ٣...)

**Granada Addition - Custom Categories:**
User's custom categories appear at top in editable section.

**Category Item:**
```
┌─────────────────────────────────────┐
│ ٦- كتب السنة                  (1241)│
└─────────────────────────────────────┘
```

### 5. Settings Page (`/settings`)

**Sections:**

1. **التطبيق** (Application)
   - Share app
   - About

2. **التفضيلات** (Preferences)
   - Theme toggle (light/dark)
   - Keep screen on
   - Open search first

3. **البيانات والتخزين** (Data & Storage)
   - Data size
   - Clear data button
   - Export/Import data
   - Version info

**Granada Additions:**

4. **الذكاء الاصطناعي** (AI)
   - Claude API key input
   - Ollama server URL
   - Model selection

5. **المجموعات** (Collections)
   - Manage reading collections

### 6. Book Reader (`/book/<id>`)

**Layout:**
- Book title header with back button
- Page content (Arabic text)
- Page navigation (prev/next, page number input)
- Table of contents sidebar (toggleable)

**Granada Additions:**
- Reading progress saved automatically
- AI chat button (opens side panel)
- "I own this" toggle in sidebar
- Notes/highlights (future)

### 7. Collections Page (`/collections`) - Granada Only

**Layout:**
- List of user's reading collections
- Each collection shows:
  - Name
  - Book count
  - Progress bar
  - Expand to see books

**Collection Item:**
```
┌─────────────────────────────────────┐
│ ▾ الكتب التسعة                      │
│   ████████░░░░░░░░░ 45%       (9)   │
├─────────────────────────────────────┤
│   ☑ صحيح البخاري         ✓ مكتمل   │
│   ☐ صحيح مسلم           صفحة 234   │
│   ☐ سنن أبي داود        لم يبدأ    │
└─────────────────────────────────────┘
```

### 8. First-Run Wizard (`/wizard`)

**Single Screen:**
- Welcome message
- Brief explanation
- "Download starter books" button (downloads 9 kutub al-tis'a)
- Skip option

---

## Database Schema

```sql
-- Books metadata
CREATE TABLE books (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author_id TEXT,
    category_id INTEGER,
    death_date INTEGER,          -- Hijri year
    file_size INTEGER,
    is_downloaded INTEGER DEFAULT 0,
    is_owned INTEGER DEFAULT 0,  -- Granada: physical ownership
    download_date TEXT,
    source TEXT DEFAULT 'openiti'
);

-- Full-text search index
CREATE VIRTUAL TABLE books_fts USING fts5(
    title,
    content,
    content='pages',
    content_rowid='id',
    tokenize='unicode61'
);

-- Book pages/content
CREATE TABLE pages (
    id INTEGER PRIMARY KEY,
    book_id TEXT,
    page_num INTEGER,
    content TEXT,
    content_normalized TEXT,     -- For search
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- Authors
CREATE TABLE authors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    death_date INTEGER,
    bio TEXT
);

-- Categories
CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    book_count INTEGER DEFAULT 0
);

-- User's custom categories (Granada)
CREATE TABLE custom_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE book_custom_categories (
    book_id TEXT,
    category_id INTEGER,
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (category_id) REFERENCES custom_categories(id)
);

-- Reading collections (Granada)
CREATE TABLE collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE collection_books (
    collection_id INTEGER,
    book_id TEXT,
    position INTEGER,
    FOREIGN KEY (collection_id) REFERENCES collections(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- Reading progress (Granada)
CREATE TABLE reading_progress (
    book_id TEXT PRIMARY KEY,
    current_page INTEGER DEFAULT 1,
    total_pages INTEGER,
    last_read TEXT,
    is_complete INTEGER DEFAULT 0,
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- Search history
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    results_count INTEGER
);

-- Settings
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

---

## API Endpoints

### Search
```
GET /api/search?q=<query>&books=<ids>&authors=<ids>&categories=<ids>
Response: { results: [{ id, book_id, book_title, author, page, snippet }] }
```

### Filters
```
GET /api/filters
Response: { 
  books: [{ id, title }],
  authors: [{ id, name }],
  categories: [{ id, name }]
}
```

### Books
```
GET /api/books
GET /api/books/<id>
GET /api/books/<id>/pages?page=<num>
POST /api/books/<id>/download
DELETE /api/books/<id>
```

### OpenITI Catalog
```
GET /api/openiti/books?page=<num>&search=<query>
POST /api/openiti/books/<id>/download
```

### Authors
```
GET /api/authors?search=<query>
GET /api/authors/<id>
```

### Categories
```
GET /api/categories
GET /api/categories/<id>/books
```

### Collections (Granada)
```
GET /api/collections
POST /api/collections
PUT /api/collections/<id>
DELETE /api/collections/<id>
POST /api/collections/<id>/books
DELETE /api/collections/<id>/books/<book_id>
```

### Reading Progress (Granada)
```
GET /api/progress/<book_id>
PUT /api/progress/<book_id>
```

### Settings
```
GET /api/settings
PUT /api/settings
```

---

## File Structure

```
granada-v2/
├── app.py                    # Flask application factory
├── config.py                 # Configuration
├── requirements.txt
│
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py          # Page routes
│   │   └── api.py           # API routes
│   ├── models.py            # Database models
│   ├── search.py            # FTS5 search logic
│   └── openiti.py           # OpenITI integration
│
├── templates/
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
│   │   └── main.css
│   ├── js/
│   │   └── alpine.min.js
│   └── fonts/
│       └── (Arabic fonts)
│
└── data/
    └── granada.db
```

---

## Implementation Phases

### Phase 1: Static Templates
**Goal:** All HTML/CSS templates with hardcoded data, pixel-perfect to turath.io

**Deliverables:**
- [ ] base.html with navigation
- [ ] main.css with all styles
- [ ] search.html with working dropdowns (Alpine.js, fake data)
- [ ] books.html with tabs
- [ ] authors.html
- [ ] categories.html
- [ ] collections.html
- [ ] settings.html
- [ ] reader.html
- [ ] wizard.html

**Acceptance Criteria:**
- All pages visually match turath.io screenshots
- Dropdowns open/close correctly
- Filter tags appear when selections made
- Navigation switches between pages
- Responsive on mobile and desktop

### Phase 2: Flask Routing
**Goal:** Flask serves all templates with basic routing

**Deliverables:**
- [ ] Flask app with page routes
- [ ] Templates render correctly
- [ ] Navigation links work
- [ ] Static files served

**Acceptance Criteria:**
- All pages accessible via URLs
- Navigation works
- No 404 errors

### Phase 3: Database Setup
**Goal:** SQLite database with schema and seed data

**Deliverables:**
- [ ] Database schema created
- [ ] Seed data for testing (10-20 books, authors, categories)
- [ ] Database initialization script

**Acceptance Criteria:**
- Database file created on first run
- Seed data queryable
- Schema matches specification

### Phase 4: API Endpoints - Read
**Goal:** API endpoints that return data from database

**Deliverables:**
- [ ] GET /api/filters
- [ ] GET /api/books
- [ ] GET /api/authors
- [ ] GET /api/categories
- [ ] GET /api/collections

**Acceptance Criteria:**
- All endpoints return JSON
- Data matches database content
- No errors on empty results

### Phase 5: Frontend-Backend Integration
**Goal:** Templates fetch and display real data

**Deliverables:**
- [ ] search.html loads filters from API
- [ ] books.html loads books from API
- [ ] authors.html loads authors from API
- [ ] categories.html loads categories from API
- [ ] collections.html loads collections from API

**Acceptance Criteria:**
- All pages display database data
- Loading states shown
- Empty states handled

### Phase 6: Search Functionality
**Goal:** Full-text search with FTS5

**Deliverables:**
- [ ] FTS5 index created
- [ ] Search API endpoint
- [ ] Arabic normalization (PyArabic)
- [ ] Result highlighting
- [ ] Filter application

**Acceptance Criteria:**
- Search returns relevant results
- Arabic diacritics handled
- Filters narrow results correctly
- Results highlighted

### Phase 7: OpenITI Integration
**Goal:** Browse and download books from OpenITI

**Deliverables:**
- [ ] OpenITI catalog browsing
- [ ] Book download functionality
- [ ] Progress indication
- [ ] Downloaded books appear in library

**Acceptance Criteria:**
- Can browse OpenITI catalog
- Can download books
- Downloads are persistent
- Books are searchable after download

### Phase 8: Book Reader
**Goal:** Read downloaded books

**Deliverables:**
- [ ] Page display
- [ ] Page navigation
- [ ] Table of contents
- [ ] Reading progress tracking

**Acceptance Criteria:**
- Can read any downloaded book
- Page navigation works
- Progress saved automatically
- TOC navigation works

### Phase 9: Granada Features
**Goal:** Personal library features

**Deliverables:**
- [ ] Collections CRUD
- [ ] Physical ownership tracking
- [ ] Custom categories
- [ ] Reading progress in collections

**Acceptance Criteria:**
- Can create/edit/delete collections
- Can mark books as owned
- Can assign custom categories
- Collection progress calculated correctly

### Phase 10: AI Integration
**Goal:** AI chat for book content

**Deliverables:**
- [ ] Claude API integration
- [ ] Ollama integration
- [ ] Chat UI in reader
- [ ] Context from current page/book

**Acceptance Criteria:**
- Can chat about current book
- Works with Claude API
- Works with local Ollama
- Context is relevant

### Phase 11: Polish & Packaging
**Goal:** Production-ready application

**Deliverables:**
- [ ] Error handling
- [ ] Loading states
- [ ] Empty states
- [ ] PyInstaller packaging
- [ ] Windows executable

**Acceptance Criteria:**
- No unhandled errors
- Professional UX
- Single .exe file works
- Size under 100MB

---

## Testing Checklist

### Visual Testing
- [ ] Compare each page to turath.io screenshot
- [ ] Test on 1920x1080, 1366x768, 375x667 (iPhone)
- [ ] Verify RTL layout
- [ ] Verify Arabic text rendering
- [ ] Verify dark theme colors

### Functional Testing
- [ ] All navigation links work
- [ ] All dropdowns open/close
- [ ] Search returns results
- [ ] Filters work correctly
- [ ] Books download successfully
- [ ] Book reader displays pages
- [ ] Collections save correctly
- [ ] Settings persist

### Edge Cases
- [ ] Empty search results
- [ ] No books downloaded
- [ ] No collections created
- [ ] Very long book titles
- [ ] Special Arabic characters
- [ ] Network errors (OpenITI)

---

## Reference Screenshots

Store reference screenshots in `/docs/screenshots/`:
- turath-search.png
- turath-search-filter.png
- turath-search-filter-books.png
- turath-books.png
- turath-authors.png
- turath-categories.png
- turath-settings.png
- turath-reader.png

---

## Notes

1. **Performance:** FTS5 should handle 10-50 million words easily. Index after all content loaded.

2. **Arabic Normalization:** Always normalize both indexed content and search queries.

3. **Offline-First:** All features must work offline. OpenITI browsing is the only network-dependent feature.

4. **Data Persistence:** Use SQLite for everything. No localStorage for critical data.

5. **Error Recovery:** Database should be recoverable. Include backup/restore functionality.
