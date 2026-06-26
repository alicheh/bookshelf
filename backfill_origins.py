"""
backfill_origins.py — populate books.origin_paths from the consolidation inventory.

The consolidation flattened every book into ~/Books/ and the scanner overwrote
source_path with the new location, losing provenance. This rebuilds it: for each
book in the DB we look up every original location (all copies) from
books-inventory.csv, so you can see where a file came from and decide about dupes.

Match: by filename basename (case-insensitive), falling back to a stripped
`_<n>` collision suffix. Stored as a JSON list, best-priority source first.

Usage:  .venv/bin/python backfill_origins.py
"""
import csv
import re
import json
from pathlib import Path
from collections import defaultdict

from config import DB_PATH
from database import _conn, init_db
from consolidate import INVENTORY, source_priority


def build_index():
    by_basename = defaultdict(list)
    with open(INVENTORY, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            by_basename[Path(r["path"]).name.lower()].append(r["path"])
    # best (lowest-priority-number) source first
    for k in by_basename:
        by_basename[k] = sorted(set(by_basename[k]), key=source_priority)
    return by_basename


def lookup(filename: str, index: dict) -> list:
    key = filename.lower()
    if key in index:
        return index[key]
    # strip a trailing _<n> collision suffix added by safe_dest_name()
    stem, ext = Path(filename).stem, Path(filename).suffix.lower()
    stripped = re.sub(r"_\d+$", "", stem) + ext
    return index.get(stripped.lower(), [])


def main():
    init_db(DB_PATH)   # ensures the origin_paths column exists
    index = build_index()
    matched = empty = 0
    with _conn(DB_PATH) as c:
        rows = c.execute("SELECT id, filename FROM books").fetchall()
        for r in rows:
            origins = lookup(r["filename"], index)
            if origins:
                matched += 1
            else:
                empty += 1
            c.execute("UPDATE books SET origin_paths=? WHERE id=?",
                      (json.dumps(origins, ensure_ascii=False), r["id"]))
    print(f"Backfilled origins: {matched} matched, {empty} with no inventory match "
          f"({len(rows)} total)")


if __name__ == "__main__":
    main()
