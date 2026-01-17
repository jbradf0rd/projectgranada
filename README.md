# Granada | غرناطة

**An offline Arabic Islamic library and personal book manager**

---

## Overview

Granada is a desktop application for managing and reading Arabic Islamic texts offline. It provides a clean, RTL-optimized interface inspired by [turath.io](https://turath.io), with additional features for personal library management, AI-powered assistance, and note-taking.

### Key Features

- **Full-Text Search** - Fast Arabic text search with FTS5, supporting diacritics normalization
- **OpenITI Integration** - Browse and download books from the [OpenITI corpus](https://openiti.org/)
- **Book Reader** - Clean reading interface with table of contents navigation
- **AI Chat** - Ask questions about the text using Claude API or local Ollama models
- **Notes System (كناشة الفوائد)** - Save highlights, annotations, and AI conversations
- **Collections** - Organize books into reading lists and track progress
- **Physical Ownership Tracking** - Mark books you own in print
- **Export to Obsidian** - Export notes as Markdown with YAML frontmatter
- **Offline-First** - Works entirely offline (except OpenITI downloads)

---

## Installation

### Option 1: Download Release (Recommended)

1. Download the latest `Granada.exe` from [Releases](../../releases)
2. Run the executable - no installation required
3. On first run, optionally download starter books

### Option 2: Run from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/granada.git
cd granada

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

The application will open in your default browser at `http://localhost:5000`.

---

## Usage

### Navigation

| Page | Description |
|------|-------------|
| **البحث** (Search) | Full-text search across all books |
| **المكتبة** (Library) | Browse downloaded books, OpenITI catalog, upload custom books |
| **المؤلفون** (Authors) | Browse authors sorted by death date |
| **الأقسام** (Categories) | Browse books by category |
| **المجموعات** (Collections) | Manage reading lists |
| **كناشة** (Notebook) | View and manage saved notes |
| **الإعدادات** (Settings) | Configure AI, theme, and data options |

### AI Chat

1. Open any book in the reader
2. Click the AI button in the header
3. Ask questions about the current page or book
4. Save useful responses to your notebook

### Notes & Highlights

- Select text in the reader to see the action menu
- **Copy with Citation** - Copies text with APA-style citation
- **Insert in Chat** - Adds selected text to AI chat context
- **Save as Note** - Saves highlight to your notebook

### Exporting Notes

1. Go to **كناشة** (Notebook)
2. Click the export button
3. Choose a folder (defaults to Obsidian vault if detected)
4. Notes are exported as Markdown files with metadata

---

## Configuration

### AI Settings

Navigate to **الإعدادات** > **الذكاء الاصطناعي** to configure:

| Setting | Description |
|---------|-------------|
| **Claude API Key** | Your Anthropic API key for Claude models |
| **Ollama URL** | Local Ollama server address (default: `http://localhost:11434`) |
| **Model** | Select between Claude (Sonnet/Opus/Haiku) or Ollama models |

### Data Location

By default, Granada stores data in:

- **Windows:** `%APPDATA%\Granada\`
- **Database:** `granada.db`
- **Books:** `books/` directory

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask (Python) |
| Database | SQLite with FTS5 |
| Frontend | Jinja2 + Alpine.js |
| Styling | Custom CSS (RTL-optimized) |
| Arabic Processing | PyArabic |
| Text Source | OpenITI corpus |
| AI Integration | Anthropic Claude API, Ollama |
| Packaging | PyInstaller |

---

## Building from Source

### Prerequisites

- Python 3.9+
- pip

### Build Executable

```bash
# Install dependencies
pip install -r requirements.txt

# Run build script
python build.py

# Or use PyInstaller directly
pyinstaller granada.spec
```

The executable will be created in the `dist/` folder.

---

## Project Structure

```
granada/
├── app.py                 # Application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
│
├── app/
│   ├── routes/
│   │   ├── main.py        # Page routes
│   │   └── api.py         # REST API endpoints
│   ├── models.py          # Database schema
│   ├── search.py          # FTS5 search logic
│   └── openiti.py         # OpenITI integration
│
├── templates/             # Jinja2 HTML templates
│   ├── base.html
│   ├── search.html
│   ├── books.html
│   ├── reader.html
│   ├── notebook.html
│   └── ...
│
├── static/
│   └── css/
│       └── main.css       # All styles
│
└── data/
    └── granada.db         # SQLite database
```

---

## API Reference

Granada exposes a REST API for all operations:

### Search

```
GET /api/search?q=<query>&books=<ids>&authors=<ids>&categories=<ids>
```

### Books

```
GET    /api/books                    # List all books
GET    /api/books/<id>               # Get book details
GET    /api/books/<id>/pages/<num>   # Get page content
PUT    /api/books/<id>               # Update book metadata
DELETE /api/books/<id>               # Delete book
```

### Notes

```
GET    /api/notes                    # List all notes
POST   /api/notes                    # Create note
PUT    /api/notes/<id>               # Update note
DELETE /api/notes/<id>               # Delete note
POST   /api/notes/export             # Export to Markdown
```

### AI Chat

```
POST /api/chat                       # Send message to AI
```

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

This is required due to the use of [PyArabic](https://github.com/linuxscout/pyarabic), which is GPL-licensed.

### What this means:

- You can use, modify, and distribute this software freely
- Source code must be made available for any distributed versions
- Derivative works must also be GPL-licensed
- Commercial use is permitted

See [LICENSE](LICENSE) for the full text.

### Dependencies and Their Licenses

| Dependency | License |
|------------|---------|
| Flask | BSD-3-Clause |
| PyArabic | GPL |
| PyInstaller | GPL-2.0 (with exception) |
| Anthropic SDK | MIT |
| Alpine.js | MIT |

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/granada.git
cd granada

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python app.py
```

---

## Acknowledgments

- [OpenITI](https://openiti.org/) - For the corpus of digitized Arabic texts
- [turath.io](https://turath.io) - For UI/UX inspiration
- [PyArabic](https://github.com/linuxscout/pyarabic) - For Arabic text processing
- [Alpine.js](https://alpinejs.dev/) - For the lightweight reactive framework

---

## Support

- **Issues:** [GitHub Issues](../../issues)
- **Discussions:** [GitHub Discussions](../../discussions)

---

**غرناطة** - *Your personal Islamic library*
