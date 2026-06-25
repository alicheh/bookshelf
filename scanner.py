"""
scanner.py — scan ~/Books/ and sync filenames into the database.
Run after adding new books to the folder.
"""
import re
import json
from pathlib import Path
from datetime import datetime

from config import BOOKS_DIR, DB_PATH
from database import init_db, upsert_book

BOOK_EXTS = {".pdf", ".epub", ".mobi", ".azw3", ".azw", ".djvu", ".cbz", ".cbr"}


# ── filename parser ───────────────────────────────────────────────────────────

def _clean(s: str) -> str:
    s = re.sub(r"\s*\(\d{4}\)\s*$", "", s)   # trailing (year)
    s = re.sub(r"\s*-\s*(Pearson|Wiley|Manning|O'Reilly|Springer|Apress|"
               r"Packt|MIT Press|Penguin|McGraw|Tarcher|Doubleday|"
               r"CreateSpace|Routledge|Bloomsbury|Sybex|Wrox|Syngress).*$",
               "", s, flags=re.I)
    return s.strip(" -–—_")


def parse_filename(filename: str) -> tuple[str, list[str]]:
    """Return (title, [authors]) extracted from the filename stem."""
    stem = Path(filename).stem

    # Anna's Archive / libgen format: "Title -- Author -- Year -- Publisher …"
    if " -- " in stem:
        parts = [p.strip() for p in stem.split(" -- ")]
        title  = _clean(parts[0])
        author = _clean(re.sub(r",?\s*\d{4}.*$", "", parts[1])) if len(parts) > 1 else ""
        return title, [author] if author else []

    # "Author - Title" or "Author, F. - Title"
    if " - " in stem:
        left, right = stem.split(" - ", 1)
        left, right = left.strip(), right.strip()
        words_left = left.split()
        if len(words_left) <= 4 and len(left) <= 55:
            return _clean(right), [_clean(left)]
        return _clean(left), []

    # dots-as-spaces (e.g. "Neuroscience.Science.of_.the_.Brain_")
    cleaned = re.sub(r"_", " ", stem)
    cleaned = re.sub(r"\.(?=[a-z])", " ", cleaned).strip()
    return cleaned, []


# ── folder scanner ────────────────────────────────────────────────────────────

def scan_folder(books_dir: Path = BOOKS_DIR, db_path: Path = DB_PATH) -> tuple[int, int]:
    """Walk books_dir, upsert every book file into the DB. Returns (added, updated)."""
    init_db(db_path)
    added = updated = 0

    from database import _conn
    with _conn(db_path) as c:
        existing = {r[0] for r in c.execute("SELECT filename FROM books")}

    for path in books_dir.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() not in BOOK_EXTS:
            continue

        stat  = path.stat()
        title, authors = parse_filename(path.name)
        data = {
            "filename":      path.name,
            "title":         title,
            "authors":       authors,
            "extension":     path.suffix.lower().lstrip("."),
            "size_bytes":    stat.st_size,
            "modified_date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
            "source_path":   str(path),
        }
        upsert_book(db_path, data)
        if path.name in existing:
            updated += 1
        else:
            added += 1

    print(f"Scan complete: {added} new, {updated} updated")
    return added, updated


if __name__ == "__main__":
    scan_folder()
