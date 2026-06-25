#!/bin/bash
# Start BookShelf web app.
# Optional: BOOKS_DIR=/path/to/books ./run.sh
set -e
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q fastapi "uvicorn[standard]"
fi
echo "📚 BookShelf starting on http://localhost:7878"
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 7878 --reload
