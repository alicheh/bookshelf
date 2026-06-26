# Design System — BookShelf

> Read this before making any visual or UI decision. It is the source of truth for
> layout, navigation, fonts, color, spacing, and motion. Do not deviate without
> explicit user approval. The interactive reference prototype lives at
> `.context/design/preview.html` (open in a browser).

## Product Context

- **What this is:** A personal library for ~3,937 books/documents (PDF, epub, …)
  consolidated from scattered Mac locations into one place, to **find → read → (later) chat with / build from**.
- **Who it's for:** A single power user. Keyboard-first, dense, used for hours.
- **Part of a bigger system:** BookShelf is the **"books" connector for Daftar**
  (`~/DevProjects/daftar`), a source-agnostic knowledge OS
  (`sources → ingest → filter junk → synthesize (summaries, tags) → search / chat / API`).
  BookShelf's scanner = Daftar's *ingest*; the dedup work = *filter junk*; the future
  "chat with your books" = Daftar's *search/chat* over this connector. Keep the two a
  coherent family, but BookShelf owns the books-specific browsing surface below.

## The memorable thing

**"Everything is here, filed where it should be, and I can fly through it."**
Trust + speed — the opposite of scattered-folder anxiety. Every decision serves this.

## Core interaction model — Miller columns over a *computed* taxonomy

The signature UX is macOS Finder's **column view** (Miller columns) crossed with the
keyboard speed of `ranger`/`lf`, but navigating a **trustworthy, computed** tree
instead of messy real folders.

- **Left rail** → smart groups (All Books, Reading, Recently Added, Favorites, Unfiled)
  with live counts. `Unfiled: 0` is the trust thesis in miniature.
- **Cascading columns** → each column is a **facet** (Topic → Subtopic → …), one-line
  dense rows (~30px), **no cover thumbnails**, every folder row shows an item **count**.
- **Preview pane** (right) → renders the actual file in place (PDF first page / epub),
  plus metadata. "Read in place" = no app-launch, no context-switch, no losing your place.
- **Breadcrumb** (footer) → the full path, always visible.
- **Full keyboard nav** → `↑↓` within the focused column, `←→` between columns,
  `↵` drill in, `⌘K` search. The focused column is visually marked.

### Folders are computed, not stored (this is the key idea)

Columns are **facets dynamically computed from each book's metadata** (topic, subtopic,
author, year, format, tags — tags supplied by Daftar's synthesize step). A search/query
produces a result set; columns group that set by a facet, with counts; selecting a value
filters and the next column groups the remainder. **The tree is materialized per query
and thrown away** — which is *why it can be trusted*: nothing to maintain, never stale,
always complete. This is faceted navigation wearing column-view clothes (cf. the old
iTunes column browser).

- **Pivotable columns:** the user can change a column's facet (Topic → Author → Year → …).
- **Dynamic columns (planned):** the system auto-chooses *which* facet each column should
  be, based on the query and which facet best splits the current result set (e.g. searching
  an author auto-switches columns to Topic → Year). Status: explored, not yet specified.

## Typography

- **Primary (UI, rows, body):** system font —
  `system-ui, -apple-system, "Segoe UI", "SF Pro Text", sans-serif`.
  Chosen deliberately: it is Finder's own font (SF Pro), the fastest to skim, and
  renders Persian/Arabic natively. No web-font download.
- **Mono (metadata, counts, breadcrumb, facet labels):**
  `ui-monospace, "SF Mono", "Menlo", monospace`.
- **Scale:** rows 13px / row-height 30px; section + facet labels ~10px uppercase mono with
  `.04–.06em` tracking; preview title ~18px bold; metadata ~11px mono.
- **RTL:** Persian/Arabic titles render right-to-left (`dir="rtl"`) in rows and preview.

## Color — theme system (6 palettes, user-switchable in Settings)

Color is delivered as **CSS custom-property palettes**. All six ship as a **theme
setting** the user can switch at runtime. **Default: `paper`.** Tokens per palette:
`--bg --panel --rail --border --text --muted --faint --accent --accent-soft --accent-ink --keep`.

| Palette | bg | panel | accent (selection) | note |
|---|---|---|---|---|
| **paper** (default) | `#F7F4EE` | `#FFFFFF` | `#C8862B` amber | warm off-white, bookmark amber |
| finder | `#F1F2F4` | `#FFFFFF` | `#2F6BE0` blue | neutral, closest to macOS Finder |
| ice | `#E8EFFA` | `#F6F9FE` | `#2563EB` blue | light-blue background, not white |
| graphite | `#ECEDF0` | `#FAFAFB` | `#0F8C8C` teal | cool gray, techy-calm |
| sage | `#EDF1EB` | `#FBFCFA` | `#3E7D52` green | soft green-gray |
| night | `#1A1815` | `#211E1A` | `#E0A03C` amber | dark (dim, warm) |

Full token values live in `.context/design/preview.html` (`PALETTES`) and are the
canonical source until ported into the app.

**Rules:** accent is reserved for selection/active-path, focus, links, and tag emphasis.
The focused column's selected row uses the solid `--accent` fill (white text); the trail
behind it uses `--accent-soft` (Finder's focused/unfocused selection behavior). Format
badges (PDF/EPUB) are the only other tint.

## Spacing & layout

- **Base unit:** 4px. **Density:** compact (this is a fly-through tool; comfortable
  spacing would waste the screen).
- **Row height:** 30px. **Rail width:** ~184px. **Preview pane:** ~312px. Folder columns
  flex; the books (leaf) column is slightly wider.
- **Depth:** borders-only (`1px solid var(--border)`) and tonal fills. No drop shadows.

## Motion

- **Approach:** minimal-functional. Speed is the brand — animation must never make you wait.
- Column/preview updates are instant; any transition ≤150ms ease-out. Nothing bounces.
  Do not animate layout properties; use color/opacity for feedback. Every control needs a
  visible focus state.

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-26 | Miller-column shell over a computed/faceted taxonomy | User's Finder column-view reference + the need for a *trustworthy* tree (real folders are messy) |
| 2026-06-26 | System font (not Fraunces/IBM Plex) | Fast to skim, Finder-native, renders Persian; no download |
| 2026-06-26 | 6 palettes shipped as a Settings theme; **paper** default | User wanted to experiment and keep all; chose paper for now |
| 2026-06-26 | BookShelf = Daftar's books connector | Daftar roadmap lists books; same stack; aligns ingest/search/chat |
