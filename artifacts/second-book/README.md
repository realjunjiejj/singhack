# Meridian Wealth — second Book

Generated output, checked in so the portability demonstration and the
`web/e2e/zz-second-book.spec.ts` browser tests run from a clean checkout
without a generation step.

- `data/` — a complete canonical Book: four clients, five portfolios, four
  snapshot dates, two currencies, one relationship manager (Ingrid Solberg,
  `RM-ZH-401`). It shares no identifier, name, instrument, event or date with
  the SingHacks Book.
- `workbench.json` — the Workbench artifact built from that Book.

Both are produced deterministically by
`engine/tests/fixtures/second_book.py`. Every derived figure is computed from
quantity, price and the snapshot's own FX rate, so the Book is internally
consistent by construction rather than by hand.

Regenerate:

```bash
python -c "import sys; sys.path.insert(0,'engine/tests'); from pathlib import Path; from fixtures import second_book; second_book.write_book(Path('artifacts/second-book/data'))"
python -m jb_clarity.cli validate-data --data artifacts/second-book/data
python -m jb_clarity.cli build --data artifacts/second-book/data --as-of 2026-03-31 --generated-at 2026-04-01T00:00:00+00:00 --output artifacts/second-book/workbench.json
```

This Book is test and demonstration material. It is synthetic, like the
SingHacks data, and describes no real person or institution.
