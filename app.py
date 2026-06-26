import subprocess
from pathlib import Path
from typing import Any

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import BOOKS_DIR, DB_PATH
from database import (get_books, get_book, update_book, get_stats, init_db,
                     facet_groups, query_books)
from scanner import scan_folder


@asynccontextmanager
async def lifespan(_app):
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    init_db(DB_PATH)
    yield


app = FastAPI(title="BookShelf", docs_url=None, redoc_url=None, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── pages ─────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def index():
    return FileResponse("static/index.html")


# ── books API ─────────────────────────────────────────────────────────────────

@app.get("/api/books")
def list_books(
    q: str = "", format: str = "", status: str = "",
    sort: str = "title", page: int = 1, per_page: int = 60,
):
    books, total = get_books(
        DB_PATH, q=q, fmt=format, status=status,
        sort=sort, page=page, per_page=per_page,
    )
    return {"books": books, "total": total, "page": page, "per_page": per_page,
            "pages": max(1, -(-total // per_page))}


# ── faceted navigation (column view) ──────────────────────────────────────────

def _filters(format, author, initial, year, status, category):
    return {k: v for k, v in {
        "format": format, "author": author, "initial": initial,
        "year": year, "status": status, "category": category,
    }.items() if v}


@app.get("/api/facets")
def facets(
    facet: str = "format", q: str = "",
    format: str = "", author: str = "", initial: str = "",
    year: str = "", status: str = "", category: str = "",
):
    filters = _filters(format, author, initial, year, status, category)
    return {"facet": facet, "groups": facet_groups(DB_PATH, facet, filters, q)}


@app.get("/api/column-books")
def column_books(
    q: str = "", sort: str = "title", page: int = 1, per_page: int = 300,
    format: str = "", author: str = "", initial: str = "",
    year: str = "", status: str = "", category: str = "",
):
    filters = _filters(format, author, initial, year, status, category)
    books, total = query_books(DB_PATH, filters, q, sort, page, per_page)
    return {"books": books, "total": total}


@app.get("/api/books/{book_id}")
def book_detail(book_id: int):
    book = get_book(DB_PATH, book_id)
    if not book:
        raise HTTPException(404, "Not found")
    return book


@app.put("/api/books/{book_id}")
async def update_book_detail(book_id: int, request: Request):
    data = await request.json()
    book = get_book(DB_PATH, book_id)
    if not book:
        raise HTTPException(404, "Not found")
    update_book(DB_PATH, book_id, data)
    return get_book(DB_PATH, book_id)


# ── actions ───────────────────────────────────────────────────────────────────

@app.get("/api/file/{book_id}")
def serve_file(book_id: int):
    """Serve the raw book file inline (used by the in-pane PDF preview)."""
    book = get_book(DB_PATH, book_id)
    if not book:
        raise HTTPException(404, "Not found")
    path = (BOOKS_DIR / book["filename"]).resolve()
    # confine to BOOKS_DIR
    if BOOKS_DIR.resolve() not in path.parents or not path.exists():
        raise HTTPException(404, f"File not on disk: {book['filename']}")
    media = "application/pdf" if book["extension"] == "pdf" else "application/octet-stream"
    return FileResponse(path, media_type=media, headers={"Content-Disposition": "inline"})


@app.post("/api/open/{book_id}")
def open_book(book_id: int):
    book = get_book(DB_PATH, book_id)
    if not book:
        raise HTTPException(404, "Not found")
    path = (BOOKS_DIR / book["filename"]).resolve()
    if BOOKS_DIR.resolve() not in path.parents or not path.exists():
        raise HTTPException(404, f"File not on disk: {book['filename']}")
    subprocess.Popen(["open", str(path)])
    return {"ok": True}


@app.post("/api/scan")
def scan():
    added, updated = scan_folder(BOOKS_DIR, DB_PATH)
    return {"added": added, "updated": updated}


@app.get("/api/stats")
def stats():
    return get_stats(DB_PATH)


# ── dev entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    from config import PORT
    uvicorn.run("app:app", host="127.0.0.1", port=PORT, reload=True)
