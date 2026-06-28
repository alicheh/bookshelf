"""
Import locally available Apple Books items into ~/Books/.

Apple Books stores user-added iCloud books in:
  ~/Library/Mobile Documents/iCloud~com~apple~iBooks/Documents

Many EPUBs are macOS package directories ending in ".epub", not regular files.
Run without flags for a dry-run report. Add --copy to copy missing items into
BOOKS_DIR and rescan the BookShelf database.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

from config import BOOKS_DIR, DB_PATH
from scanner import book_size, is_book_path, parse_filename, scan_folder


APPLE_BOOKS_SOURCES = [
    Path.home() / "Library/Mobile Documents/iCloud~com~apple~iBooks/Documents",
    Path.home() / "Library/Containers/com.apple.BKAgentService/Data/Documents/iBooks/Books",
]


@dataclass
class ImportPlan:
    source: Path
    target: Path
    size_bytes: int
    action: str


def iter_apple_books(paths: list[Path]):
    for folder in paths:
        if not folder.exists():
            continue
        try:
            children = list(folder.iterdir())
        except PermissionError as exc:
            print(f"Warning: cannot read Apple Books source {folder}: {exc}", file=sys.stderr)
            continue
        for path in children:
            if path.name.startswith(".") or path.name.endswith(".icloud"):
                continue
            if is_book_path(path):
                yield path


def unique_target(source: Path, target_dir: Path) -> Path:
    target = target_dir / source.name
    if not target.exists():
        return target

    stem = source.stem
    suffix = source.suffix
    i = 2
    while True:
        candidate = target_dir / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def build_plan(sources: list[Path], target_dir: Path) -> list[ImportPlan]:
    plans = []
    for source in iter_apple_books(sources):
        existing_target = target_dir / source.name
        try:
            size = book_size(source)
        except OSError as exc:
            print(f"Warning: cannot read {source}: {exc}", file=sys.stderr)
            continue
        if existing_target.exists():
            action = "skip-existing"
            target = existing_target
        else:
            action = "copy"
            target = unique_target(source, target_dir)
        plans.append(ImportPlan(source, target, size, action))
    return plans


def normalize_title(value: str) -> str:
    value = Path(value).stem
    value = value.casefold()
    value = re.sub(r"[^\w\s]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def existing_title_keys(db_path: Path) -> set[str]:
    if not db_path.exists():
        return set()
    with sqlite3.connect(db_path) as c:
        rows = c.execute("SELECT filename, title FROM books").fetchall()
    keys = set()
    for filename, title in rows:
        for value in (filename, title):
            key = normalize_title(value or "")
            if key:
                keys.add(key)
    return keys


def has_existing_title_match(plan: ImportPlan, keys: set[str]) -> bool:
    title, _ = parse_filename(plan.source.name)
    return normalize_title(plan.source.name) in keys or normalize_title(title) in keys


def copy_item(source: Path, target: Path):
    if source.is_dir():
        shutil.copytree(source, target, copy_function=shutil.copy2)
    else:
        shutil.copy2(source, target)


def format_size(size: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Apple Books into BookShelf")
    parser.add_argument("--copy", action="store_true", help="copy missing books into BOOKS_DIR")
    parser.add_argument("--limit", type=int, help="copy at most this many missing books")
    parser.add_argument(
        "--skip-title-matches",
        action="store_true",
        help="skip candidates whose normalized title already appears in the database",
    )
    parser.add_argument("--source", action="append", type=Path, help="additional Apple Books source folder")
    parser.add_argument("--target", type=Path, default=BOOKS_DIR, help="destination folder")
    args = parser.parse_args()

    sources = APPLE_BOOKS_SOURCES + (args.source or [])
    target_dir = args.target.expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)

    plans = build_plan(sources, target_dir)
    all_to_copy = [p for p in plans if p.action == "copy"]
    title_match_skips = []
    if args.skip_title_matches:
        keys = existing_title_keys(DB_PATH)
        filtered = []
        for plan in all_to_copy:
            if has_existing_title_match(plan, keys):
                title_match_skips.append(plan)
            else:
                filtered.append(plan)
        all_to_copy = filtered
    to_copy = all_to_copy[:args.limit] if args.limit is not None else all_to_copy
    skipped = [p for p in plans if p.action == "skip-existing"]
    total_bytes = sum(p.size_bytes for p in to_copy)

    mode = "COPY" if args.copy else "DRY RUN"
    print(f"Apple Books import ({mode})")
    print(f"Sources checked: {len(sources)}")
    print(f"Discovered: {len(plans)}")
    print(f"Already in target: {len(skipped)}")
    if args.skip_title_matches:
        print(f"Skipped title matches: {len(title_match_skips)}")
    if args.limit is not None:
        print(f"Copy limit: {args.limit} of {len(all_to_copy)} candidates")
    print(f"Will copy: {len(to_copy)} ({format_size(total_bytes)})")

    for plan in to_copy[:30]:
        print(f"  copy {plan.source.name} -> {plan.target.name} ({format_size(plan.size_bytes)})")
    if len(to_copy) > 30:
        print(f"  ... {len(to_copy) - 30} more")

    if not args.copy:
        print("No files copied. Re-run with --copy to import and rescan.")
        return 0

    for plan in to_copy:
        copy_item(plan.source, plan.target)

    added, updated = scan_folder(target_dir, DB_PATH)
    print(f"Imported {len(to_copy)} items. Scan complete: {added} new, {updated} updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
