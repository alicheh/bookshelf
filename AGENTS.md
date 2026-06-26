# BookShelf — Agent Context

## Design system
Always read `DESIGN.md` before making any visual or UI decision (layout, fonts, color,
spacing, motion). The interactive UI reference is `.context/design/preview.html`.
BookShelf is the **books connector for Daftar** (`~/DevProjects/daftar`) — keep the two
a coherent family.

## What this app is
Personal book library web app. ~3,937 books consolidated from scattered Mac locations
(Downloads, Dropbox, iCloud, Google Drive, DevProjects) into a single flat folder.

## Running the app
```bash
./run.sh          # starts on http://localhost:7878
```
Or manually:
```bash
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 7878 --reload
```

After adding new books to ~/Books/, rescan:
```bash
.venv/bin/python scanner.py
# or hit the ↻ Rescan button in the UI
```

## Key paths (on the owner's Mac)
- **Books folder:** `~/Books/` — flat, all files at root, local only (not cloud-synced)
- **Database:** `~/Books/library.db` — moves with the books folder
- **Inventory/reports:** `~/conductor/workspaces/conductor-dev/ottawa/.context/mac-organization/`

To use a different books folder: `BOOKS_DIR=/path/to/books ./run.sh`

## Architecture
- `config.py` — BOOKS_DIR, DB_PATH (overridable via env var)
- `database.py` — SQLite schema, search, CRUD, stats
- `scanner.py` — scan ~/Books/, parse Author-Title filenames, upsert into DB
- `consolidate.py` — one-time migration script (already run, see below)
- `app.py` — FastAPI backend
- `static/index.html` — full frontend (plain HTML/CSS/JS, no build step)
- `static/legacy-grid.html` — old Tailwind CDN + Alpine.js CDN grid UI, kept as reference

## Database schema
```
books: id, filename, title, authors (JSON), extension, size_bytes,
       modified_date, added_date, source_path, tags (JSON),
       category, read_status (unread/reading/read), rating (0-5), notes,
       origin_paths (JSON)
```

## Consolidation — already done, originals untouched
`consolidate.py` was run on 2026-06-25. It COPIED (never moved) books from all
locations to ~/Books/. Every book in the DB has `source_path` pointing to where
it came from originally.

### Pending cleanup — redundant original copies to delete
The same book existed in multiple locations. 356 exact duplicates (same filename +
same byte size) were skipped during consolidation. The originals are still sitting
in their original places:

| Location | Redundant copies | Priority |
|---|---|---|
| `~/Downloads/` | 61 | Delete first — clear staging area |
| `~/DevProjects/` | 58 | Delete second — books that lived in code folders |
| iCloud (`~/Library/Mobile Documents/`) | 32 | Delete last — verify ~/Books/ copies open first |
| `~/Documents/` | 1 | Safe to delete |

**How to generate the delete list:** re-run `consolidate.py --dry-run` — it prints
which copy was kept (winner) vs skipped (redundant). The skipped ones are safe to
delete once the ~/Books/ copy is confirmed good.

**Before deleting:** verify the file exists in ~/Books/ and opens correctly.
Never delete iCloud-only copies until you've confirmed the local copy works.

## Known issues / TODO
- The old Tailwind/Alpine grid UI lives at `static/legacy-grid.html`; the current
  app is the no-build column-view UI in `static/index.html`.
- No cover images yet — plan is Open Library Covers API:
  `https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg`
- No bulk-edit (tagging/categorizing multiple books at once)
- Title parsing is imperfect for numeric/arxiv filenames (e.g. `2501.12948v1.pdf`)
- Configurable column count is captured in `ROADMAP.md`; current search mode
  collapses to one result column.
