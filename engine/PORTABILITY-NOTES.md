# Dataset portability — implementation notes

Working notes for the portability slice. Records what the red test found
before production code changed, and what each change was for.

## Step 1 — red portability test, findings

`engine/tests/portability.py` rebuilds the supplied Book under a hostile
identity scheme: identifier *shapes* change, not only their digits, so anything
pattern-matching `CL-0001` or `SYN-EQ-0007` fails loudly. It rewrites every
client, portfolio, instrument, facility, commitment, need, transaction, note
and mandate identifier, the RM id and name, client names, booking-centre
labels, and moves one client's portfolios to a different base currency,
recomputing base-currency values at each snapshot's own supplied rate.

Run against the engine as it stood at `81820a0`:

| Axis | Result |
|---|---|
| Full identifier remap, 20 clients | **PASS** — builds, schema-valid, 0 SingHacks identifiers present in the artifact |
| RM identity | **PASS** — new RM id and name carried through |
| Booking-centre relabelling | **PASS** |
| Base-currency switch for one client (USD → SGD) | **PASS** — totals still reconcile |
| **Snapshot count other than five** | **FAIL** |

### The failure

A Book with three snapshots instead of five still produced RM-facing text
asserting five:

```
Wealth fell 3.99% across the five supplied snapshots (USD 939,313).
... The dataset supplies five dated snapshots, not a return series ...
```

102 occurrences of "five" reached the artifact for a three-snapshot Book, in
`clientCases[].conclusion`, `whyNow`, Anticipatory Signal summaries and
Evidence Packet uncertainty claims. Every one of them is a false statement
shown to a Relationship Manager, and the engine's whole claim is that it does
not say things the data does not support.

Sites in production code at the time of the finding:

- `calculations/timeline.py` — docstring
- `detectors/explanation.py` — signal summary, and the attribution caveat
- `detectors/suitability.py` — the drawdown-horizon caveat
- `ingestion/loader.py` — `snapshot_dates` docstring

The identifier layer was already portable. The time layer was not.

### Conflict with ADR 0010

`docs/adr/0010-preserve-time-and-ranking-integrity.md` says Client Cases
"expose the five supplied snapshots". That wording is specific to the SingHacks
Book. Step 5 of the portability brief requires count-aware language derived
from the data. Surfacing rather than silently overriding, per `AGENTS.md`: the
ADR's *intent* — a replayable timeline that compares selected dates and states
its endpoints — is preserved exactly; only the hardcoded count changes. No ADR
decision is reversed.

## Step 2 — canonical source contract

`ingestion/source_contract.py` encodes each canonical table once: default
filename, grain, required and optional columns, identifier columns, types,
primary key, foreign keys, and snapshot-dependent wide-column families. The
loader and validator consume it instead of repeating column lists.

Identifier columns are read as strings at parse time via the contract's dtype
map, so a stable record key can never become a float through type inference.

## Step 5 — snapshot assumptions removed

Snapshot dates are discovered from canonical holdings and validated: at least
two distinct ISO dates, strictly ordered, unique, current = greatest. RM-facing
wording is generated from the actual count, and period claims name their
endpoints rather than implying a fixed grid.

## Step 8 — presentation assumptions removed

`web/src/components/queue/PriorityQueue.tsx` keeps the Hartono/Cheung/
Margarethe shortcuts labelled "Demo cases" when those clients are present, and
otherwise derives up to three "Featured cases" from Priority Queue order using
real client names. Absent identifiers are never rendered as disabled chips.

## Step 10 — second Book

`engine/tests/fixtures/portability_book/` is a hand-written four-client Book
exercising the same rules through different facts. See
`test_second_book.py` for the assertions it must satisfy.

## Step 11 — operator command (added after the cut line passed)

`validate-data` checks a Book and reports whether it will build, without
writing an artifact. Added only after all five cut-line gates were green.

## Judge-facing demonstration (about 30 seconds)

1. Show the SingHacks Book in the Workbench — the main pitch is unchanged.
2. `python -m jb_clarity.cli validate-data --data artifacts/second-book/data`
3. `python -m jb_clarity.cli build --data artifacts/second-book/data --as-of 2026-03-31 --output artifacts/second-book/workbench.json`
4. Point out the new RM (Ingrid Solberg), four clients, four snapshots, and
   that the shortcuts now read "Featured cases" with this Book's own names.
5. Open one Evidence Chain and show `EV-MW-...` identifiers resolving to
   Meridian records.
6. Return to the SingHacks artifact.

## Out of scope in this slice

Steps 3, 4, 6, 7 and 9 remain post-submission hardening per the brief's
hackathon cut line. In particular:

- **No manifest layer.** Source files must already use canonical filenames and
  column names. Mapping a bank's own column names onto the canonical contract
  is the next adapter layer. Path B in the brief is not implemented.
- **No multi-RM filtering.** A dataset containing several relationship managers
  is refused with the list of RM identifiers rather than filtered. `--rm-id`
  does not exist yet. This is deliberately a refusal, not a silent first-row
  default, which is what the code did before.
- **Capability absence is only partly graceful.** Missing optional tables are
  reported by `validate-data`, but the engine still requires all twelve
  canonical files to be present; an empty capability table is not yet
  synthesised.
- **Taxonomies are not externalised.** Event transmission channels, theme
  keywords and liquidity tiers still live in code. Unknown values are now
  reported rather than approximated, but adding a mapping requires a code
  change, not configuration.
- **Translation validation compares token sets, not ordered occurrences.** A
  translation that swapped two amounts of equal multiset would still pass.
