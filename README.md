# Swedish vocabulary decks

Public, data-only source of truth for the Swedish vocabulary decks used by
[Svenska Flashcards](https://github.com/glevanov/flashcards), an offline Android
app for studying Swedish at B1/B2 level, partly following the Rivstart
curriculum.

This repository holds CSV deck files and nothing else: no application code, no
SRS/review state, no personal study history. Review progress stays on the device;
only the cards are shared here.

## Layout

```
vocab/
├── core/       # themed everyday vocabulary
└── rivstart/   # one deck per Rivstart chapter
```

- **`core/`** — themed everyday vocabulary: adjectives, describing words,
  feelings and opinions, personality, common nouns, common verbs, connectors and
  fixed phrases. Start here.
- **`rivstart/`** — one deck per Rivstart chapter, aligned to that chapter's
  theme. All 18 chapters are populated.

27 decks in total (9 core, 18 Rivstart chapters).

## CSV contract

Every deck is a single CSV file. The Android app's parser depends on this exact
format, so `scripts/validate_vocab.py` and CI enforce it:

- **Encoding** — UTF-8, LF line endings, no byte-order mark.
- **Header** — the first line is exactly `swedish,english,example`. The app
  would tolerate a missing header, but this repository requires it so every file
  is self-describing.
- **Columns** — exactly three, in this order: `swedish`, `english`, `example`.
  `swedish` and `english` are the two card faces; `example` is a full Swedish
  sentence that puts the word in context.
- **One card per physical line** — fields containing commas are wrapped in
  straight double quotes (standard CSV), and a doubled `""` inside a quoted
  field is a literal quote. A quoted field must **never** span lines: the app
  parses line by line, so a card split across two lines breaks it.
- **Blank and comment lines** — blank lines are ignored, as are lines whose
  first cell starts with `#` (handy for section comments inside a deck).
- **No empty fields** — `swedish`, `english` and `example` must all be non-blank.

Example (`vocab/core/adjectives.csv`):

```csv
swedish,english,example
stor,big,"Det är ett stort hus."
liten,small,"Vi har en liten lägenhet."
```

## Deck IDs and card keys

- **Deck ID** = the path under `vocab/` without `.csv`, `/`-separated:
  `core/adjectives`, `rivstart/kapitel-01`.
- **Card key** = `<deck>::<swedish>`: `core/adjectives::stor`,
  `rivstart/kapitel-01::en fritid`.

The card key is the app's stable primary key, and each card's SRS state is
stored against it. Renaming a deck or editing a `swedish` term therefore orphans
that card's review history; fixing a typo in `english` or `example` is free.

The same Swedish term may legitimately appear in several decks (for example
`en skatt` in `rivstart/kapitel-06` and `rivstart/kapitel-17`), because the deck
is part of the key. Only duplicate `<deck>::<swedish>` keys are rejected, never
a term repeated across decks.

## Consuming these decks

The flashcards repository consumes this one from a sibling checkout:

```
code/
├── flashcards/      # Android app
└── swedish-vocab/   # this repository
```

`../flashcards/scripts/sync-decks.sh` rsyncs `vocab/**/*.csv` from that sibling
checkout into the app's `app/src/main/assets/vocab/`, preserving the directory
structure and deleting stale files. Deck files under the app are build
artifacts: edit them here, re-run the sync, and never edit the copies in the app
repository.

## Adding or changing cards

1. Edit the relevant CSV under `vocab/`, appending new cards at the end.
2. Run `python3 scripts/validate_vocab.py`.
3. Commit on a branch, open a pull request; CI runs the same validation.

To start a new chapter deck, copy a populated one
(`cp vocab/rivstart/kapitel-01.csv vocab/rivstart/kapitel-19.csv`) and replace
the rows.

## Validation and CI

`scripts/validate_vocab.py` is a dependency-free Python 3 stdlib script that
checks every deck under `vocab/` against the contract above: UTF-8 without BOM,
LF line endings, the exact header, exactly three columns, non-blank values, no
quoted field spanning lines, and unique `<deck>::<swedish>` keys. It prints one
`file:line: problem` line per violation and exits non-zero if anything fails.

```bash
python3 scripts/validate_vocab.py
```

The GitHub Actions workflow in `.github/workflows/validate.yml` runs the same
script on every push and pull request.
