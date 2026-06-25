import os
from pathlib import Path

# Change BOOKS_DIR env var to point to a different folder after moving books
BOOKS_DIR = Path(os.environ.get("BOOKS_DIR", Path.home() / "Books"))
DB_PATH   = BOOKS_DIR / "library.db"
PORT      = int(os.environ.get("PORT", 7878))
