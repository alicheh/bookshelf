import sqlite3
import json
from pathlib import Path


def _conn(db_path: Path):
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _conn(db_path) as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS books (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                filename      TEXT    NOT NULL UNIQUE,
                title         TEXT    NOT NULL DEFAULT '',
                authors       TEXT    NOT NULL DEFAULT '[]',
                extension     TEXT    NOT NULL DEFAULT '',
                size_bytes    INTEGER NOT NULL DEFAULT 0,
                modified_date TEXT    NOT NULL DEFAULT '',
                added_date    TEXT    NOT NULL DEFAULT (datetime('now')),
                source_path   TEXT    NOT NULL DEFAULT '',
                tags          TEXT    NOT NULL DEFAULT '[]',
                category      TEXT    NOT NULL DEFAULT '',
                read_status   TEXT    NOT NULL DEFAULT 'unread'
                                      CHECK(read_status IN ('unread','reading','read')),
                rating        INTEGER NOT NULL DEFAULT 0
                                      CHECK(rating BETWEEN 0 AND 5),
                notes         TEXT    NOT NULL DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_extension   ON books(extension);
            CREATE INDEX IF NOT EXISTS idx_read_status ON books(read_status);
            CREATE INDEX IF NOT EXISTS idx_title       ON books(title COLLATE NOCASE);
        """)


# ── helpers ──────────────────────────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    d = dict(row)
    for f in ("authors", "tags"):
        try:
            d[f] = json.loads(d[f])
        except Exception:
            d[f] = []
    return d


def _encode(value):
    return json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value


# ── queries ──────────────────────────────────────────────────────────────────

def get_books(db_path: Path, *, q="", fmt="", status="",
              sort="title", page=1, per_page=50):
    offset = (page - 1) * per_page
    where, params = ["1=1"], []

    if q:
        where.append("(title LIKE ? OR authors LIKE ? OR tags LIKE ? OR notes LIKE ?)")
        like = f"%{q}%"
        params += [like, like, like, like]
    if fmt:
        where.append("extension = ?"); params.append(fmt)
    if status:
        where.append("read_status = ?"); params.append(status)

    order = {
        "title":      "title COLLATE NOCASE ASC",
        "author":     "authors COLLATE NOCASE ASC",
        "date_added": "added_date DESC",
        "size":       "size_bytes DESC",
        "format":     "extension ASC, title COLLATE NOCASE ASC",
        "rating":     "rating DESC, title COLLATE NOCASE ASC",
    }.get(sort, "title COLLATE NOCASE ASC")

    base = f"FROM books WHERE {' AND '.join(where)}"
    with _conn(db_path) as c:
        total = c.execute(f"SELECT COUNT(*) {base}", params).fetchone()[0]
        rows  = c.execute(
            f"SELECT * {base} ORDER BY {order} LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()
    return [_row_to_dict(r) for r in rows], total


def get_book(db_path: Path, book_id: int):
    with _conn(db_path) as c:
        row = c.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    return _row_to_dict(row) if row else None


def upsert_book(db_path: Path, data: dict):
    cols = ["filename", "title", "authors", "extension", "size_bytes",
            "modified_date", "source_path"]
    vals = [_encode(data.get(k, "")) for k in cols]
    with _conn(db_path) as c:
        c.execute(f"""
            INSERT INTO books ({','.join(cols)})
            VALUES ({','.join('?'*len(cols))})
            ON CONFLICT(filename) DO UPDATE SET
                size_bytes    = excluded.size_bytes,
                modified_date = excluded.modified_date,
                source_path   = excluded.source_path
        """, vals)


def update_book(db_path: Path, book_id: int, data: dict):
    allowed = {"title", "authors", "tags", "category",
               "read_status", "rating", "notes"}
    fields = {k: _encode(v) for k, v in data.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k}=?" for k in fields)
    with _conn(db_path) as c:
        c.execute(f"UPDATE books SET {set_clause} WHERE id=?",
                  list(fields.values()) + [book_id])


def get_stats(db_path: Path) -> dict:
    with _conn(db_path) as c:
        total   = c.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        by_fmt  = c.execute("SELECT extension, COUNT(*) n FROM books GROUP BY extension ORDER BY n DESC").fetchall()
        by_cat  = c.execute("SELECT COALESCE(NULLIF(category,''),'uncategorized') cat, COUNT(*) n FROM books GROUP BY cat ORDER BY n DESC").fetchall()
        by_stat = c.execute("SELECT read_status, COUNT(*) n FROM books GROUP BY read_status").fetchall()
        total_gb = c.execute("SELECT COALESCE(SUM(size_bytes),0)/1e9 FROM books").fetchone()[0]
    return {
        "total": total,
        "total_gb": round(total_gb, 2),
        "by_format": [dict(r) for r in by_fmt],
        "by_category": [dict(r) for r in by_cat],
        "by_status": {r["read_status"]: r["n"] for r in by_stat},
    }
