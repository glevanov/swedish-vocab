#!/usr/bin/env python3
"""Validate every deck CSV under vocab/.

The contract enforced here is documented in README.md and is relied on by the
Svenska Flashcards Android app:

- UTF-8, LF line endings, no byte-order mark.
- First line is exactly `swedish,english,example`.
- One card per physical line with exactly three columns; standard CSV quoting is
  allowed, but a quoted field must not span lines (the app parses line by line).
- Blank lines and lines whose first cell starts with `#` are ignored.
- swedish, english and example must all be nonblank.
- `<deck>::<swedish>` keys are unique across all decks. A Swedish term may
  legitimately appear in more than one deck.

Usage: python3 scripts/validate_vocab.py
Exit status is 0 when every deck passes, 1 otherwise.
"""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

VOCAB_ROOT = Path(__file__).resolve().parent.parent / "vocab"
HEADER = "swedish,english,example"
COLUMNS = ("swedish", "english", "example")
KEY_SEPARATOR = "::"


def deck_id(path: Path) -> str:
    """Deck identifier: path under vocab/ without .csv, e.g. core/adjectives."""
    return path.relative_to(VOCAB_ROOT).with_suffix("").as_posix()


def label(path: Path) -> str:
    """Repo-relative path used in error messages."""
    return path.relative_to(VOCAB_ROOT.parent).as_posix()


def read_text(path: Path, errors: list[str]) -> str | None:
    text = path.read_bytes()
    try:
        text = text.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{label(path)}: not valid UTF-8 ({exc.reason} at byte {exc.start})")
        return None
    if text.startswith("\ufeff"):
        errors.append(f"{label(path)}:1: file starts with a byte-order mark")
        return None
    if "\r" in text:
        errors.append(f"{label(path)}: contains CR; use LF line endings only")
        return None
    return text


def check_file(path: Path, seen_keys: dict[str, str], errors: list[str]) -> int:
    """Validate one deck file and return its card count."""
    name = label(path)
    deck = deck_id(path)
    text = read_text(path, errors)
    if text is None:
        return 0

    first_line = text.split("\n", 1)[0]
    if first_line != HEADER:
        errors.append(f'{name}:1: header must be exactly "{HEADER}", found "{first_line}"')
        return 0

    cards = 0
    line_number = 1
    for index, record in enumerate(csv.reader(io.StringIO(text, newline=""))):
        start = line_number
        line_number += 1 + sum(cell.count("\n") for cell in record)
        if index == 0:
            continue  # header, validated above
        if any("\n" in cell for cell in record):
            errors.append(
                f"{name}:{start}: quoted field spans lines; keep one card per physical line"
            )
            continue
        if not record or not any(cell.strip() for cell in record):
            continue
        if record[0].strip().startswith("#"):
            continue
        if len(record) != len(COLUMNS):
            errors.append(f"{name}:{start}: expected {len(COLUMNS)} columns, found {len(record)}")
            continue
        blanks = [column for column, cell in zip(COLUMNS, record) if not cell.strip()]
        if blanks:
            errors.append(f"{name}:{start}: blank {'/'.join(blanks)}")
            continue
        swedish = record[0].strip()
        key = f"{deck}{KEY_SEPARATOR}{swedish}"
        if key in seen_keys:
            errors.append(
                f"{name}:{start}: duplicate card key {key} (first seen in {seen_keys[key]})"
            )
        else:
            seen_keys[key] = name
        cards += 1

    if cards == 0:
        errors.append(f"{name}: deck contains no cards")
    return cards


def main() -> int:
    if not VOCAB_ROOT.is_dir():
        print(f"error: vocabulary directory not found: {VOCAB_ROOT}", file=sys.stderr)
        return 1

    decks = sorted(VOCAB_ROOT.rglob("*.csv"))
    if not decks:
        print(f"error: no CSV decks found under {VOCAB_ROOT}", file=sys.stderr)
        return 1

    errors: list[str] = []
    seen_keys: dict[str, str] = {}
    card_count = 0
    for path in decks:
        card_count += check_file(path, seen_keys, errors)

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"FAILED: {len(errors)} problem(s) in {len(decks)} deck(s)", file=sys.stderr)
        return 1

    print(f"OK: {len(decks)} decks, {card_count} cards, {len(seen_keys)} unique keys")
    return 0


if __name__ == "__main__":
    sys.exit(main())
