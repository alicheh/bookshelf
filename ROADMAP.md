# BookShelf — Roadmap

BookShelf is the **books connector for Daftar** (`~/DevProjects/daftar`), a
source-agnostic knowledge OS (`ingest → filter junk → synthesize → search/chat`).
This roadmap tracks what's built, what's next, and the bigger vision.

## Shipped

- Column-view (Miller columns) browser over computed facets, full keyboard nav.
- Generic faceting backend (`/api/facets`, `/api/column-books`) — add a facet in one line.
- 6-palette theme system (Paper default), saved to localStorage.
- Single-column search mode; chronological Year sort; resizable columns.
- In-pane PDF first-page preview (`/api/file/{id}`).
- Original location(s) per book, recovered from the consolidation inventory
  (`backfill_origins.py`) — surfaces the 449 books that exist in multiple places,
  so duplicates can be reviewed and cleaned.

## Next — metadata enrichment (the real unlock)

Today only Format/Author/Year/Initial have signal; Topic/Subtopic/tags are empty,
so the column view can't yet group by meaning. This is Daftar's "synthesize" step.
Per book:

- **Extract text** — convert first N pages (or whole file) to plain text.
- **Derive clean metadata** with an LLM + embedded file metadata: **title, author(s),
  publisher, year of publication, edition, language, ISBN**, one-line summary, tags.
- **Standard fields** — settle a default book-metadata schema (the list above) and
  store it; backfill across the library.
- Topic/Subtopic facets then light up in the rail (`Topics · after tagging`).

### Base category taxonomy

- Adopt a **standard category system** (e.g. BISAC, Dewey/Library-of-Congress, or a
  Wikipedia/science-derived tree) as the canonical top-level categories.
- **Auto-classify** every book into that taxonomy (LLM over title/summary/text), so
  the Topic column reflects a real, shared vocabulary rather than ad-hoc folders.

## Future features (captured, not scheduled)

1. **Chat with your books** — a chat box to ask questions across the library, find
   ideas, compare books (RAG over extracted text + embeddings; cite back to page).
2. **In-app reader** — read books in place; highlight, annotate, bookmark; build a
   collection of highlights / bookmarks / per-book summaries.
3. **All documents, not just books** — ingest every doc on the laptop: PDF, DOCX,
   TXT, MD, … (a new Daftar connector / expanded scanner + `kind` field).
4. **Standard category taxonomy + auto-categorization** (see above) — promoted here
   as a first-class browsing axis.
5. **Audio** — generate podcasts / audiobooks from books or summaries.
6. **(implied) Dedup cleanup workflow** — use `origin_paths` to review and safely
   delete redundant original copies (see AGENTS.md cleanup table).

## UX backlog / smaller ideas

- **Configurable column count** — let the user choose how many facet columns to show
  (2, 3, 4…), not a fixed number. (Note: current build auto-collapses to one column
  during search — revisit; the real ask is user-chosen column count, not search-driven.)
- **Dynamic columns**: auto-pick which facet each column should be, based on the
  query and which facet best splits the current result set (explored in design).
- Reading status / Favorites / Recently-Added smart groups (need real status data).
- Virtualized rows for very large leaf lists.
