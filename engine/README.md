# JB Clarity — Intelligence Engine

The deterministic layer behind JB Clarity. It reads the supplied Julius Baer
challenge files and emits one versioned, schema-valid Workbench artifact that
the RM Workbench renders without interpreting a single financial record.

**Promise:** Know who to call, why, and how to begin.

## Commands

From the repository root:

```bash
python -m pip install -e "engine[dev]"
```

```bash
python -m jb_clarity.cli build --data singhacks-jb-wealth-intelligence/data --as-of 2026-08-26 --output artifacts/workbench.json
```

```bash
python -m pytest engine/tests
```

The build validates its own output against `contracts/workbench.schema.json`
before writing, so an artifact that reaches disk is always contract-valid. Pass
`--generated-at 2026-09-04T00:00:00+00:00` to fix the timestamp for a
byte-reproducible file. No network access and no model credentials are used at
any point.

## Using it on another client book

JB Clarity is reusable across client books through a documented canonical data
contract. It does **not** accept arbitrary spreadsheets: a Book must already
use the canonical filenames and column names described below, and mapping a
bank's own column names onto that contract is the next adapter layer, not
something this engine does today.

The canonical contract lives in one place:

```text
engine/src/jb_clarity/ingestion/source_contract.py   (contract version 1.0.0)
```

It declares, for each of the twelve canonical tables, the default filename,
grain, required and optional columns, identifier columns, column types,
primary key, foreign keys and any snapshot-dependent wide-column families.
The loader and the validator both read it, so the column list exists once.

Check a Book before building anything:

```bash
python -m jb_clarity.cli validate-data --data /path/to/book
```

That reports the contract version, the resolved source filenames, the RM,
client/portfolio/holding/snapshot counts, which capabilities are enabled,
every data-quality warning, and whether generation may proceed. It prints
counts and identifiers only — never note text or client record contents.

Then build exactly as for the supplied Book:

```bash
python -m jb_clarity.cli build --data /path/to/book --as-of YYYY-MM-DD --output artifacts/workbench.json
```

### What varies freely

Identifiers and their shapes, client and RM names, booking centres, mandate
codes, instrument universes, currencies with supplied FX, record counts, the
number of snapshots and the dates themselves. None of these are assumed.

### What must hold

- Canonical filenames and column names, as declared in the source contract.
- At least two distinct, ISO-formatted snapshot dates in `holdings.csv`; the
  as-of snapshot is the latest supplied date. A one-snapshot Book is refused,
  because nothing can be said about what changed.
- Wide columns (`aum_<date>`, `drawn_<date>`, `price_<date>` and so on) present
  for the snapshot dates the Book declares.
- Market series covering any conversion an active calculation needs.
- One relationship manager per dataset directory. A Book containing several is
  refused with the list of RM identifiers rather than silently building the
  first one.

### Capabilities that depend on optional tables

`credit_facilities`, `commitments`, `planned_cash_needs`, `event_log` and
`rm_notes` power particular detectors. `validate-data` prints which are
enabled. Absent input means the capability is unavailable — never a guessed
substitute.

### Unknown vocabulary is reported, not approximated

Event transmission channels are mapped to holding attributes through a
declared table. A channel the engine does not recognise produces no
event-to-holding link and raises `DQ-UNMAPPED-EVENT-CHANNEL` naming it. The
supplied SingHacks Book has nine such channels; they were previously invisible.

### Tested source shapes

Portability is proven against two Books, not asserted in general:

| Book | Clients | Portfolios | Snapshots | Currencies |
|---|---:|---:|---:|---|
| SingHacks (`singhacks-jb-wealth-intelligence/data`) | 20 | 24 | 5 | SGD, USD, EUR, HKD, JPY |
| Meridian Wealth (`engine/tests/fixtures/second_book.py`) | 4 | 5 | 4 | USD, CHF |

Plus the supplied Book rebuilt under a completely different identifier scheme,
RM, booking centres and one switched base currency, and the same Book reduced
to three and four snapshots.

## The seam

```python
from datetime import date
from jb_clarity import build_workbench

model = build_workbench("singhacks-jb-wealth-intelligence/data", date(2026, 8, 26))
payload = model.to_contract_dict()
```

`build_workbench` is the highest behavioural seam and the one the test suite
exercises: challenge data and an as-of date in, a complete `WorkbenchModel`
out. Given the same inputs it produces semantically identical output; only
`meta.generatedAt` varies, and an injectable clock fixes that too.

## Layout

| Path | Responsibility |
| --- | --- |
| `ingestion/` | Typed loading, normalisation of recurrence and certainty, data-quality validation |
| `calculations/` | Pure maths: FX, LTV, exposure and look-through, Eligible Liquidity, mandate bands, timelines and event linkage |
| `detectors/` | General rules that turn calculations into source-cited signals |
| `evidence/` | Stable identifiers, claims, and Evidence Packet assembly |
| `ranking/` | Urgency, Confidence and Priority Queue ordering |
| `language/` | Cached Client-Ready drafts and the validator that gates them |
| `config/scoring.v1.json` | Every threshold and weight, versioned |

Detectors never name a client. The demonstration cases surface for the same
reasons every other case does.

## Rules worth knowing

**Loan-to-value uses lending value.** `drawn / lending value × 100`, never raw
collateral market value. A facility is `active` at or above its trigger,
`near` within 5 percentage points or closing on it by 3 or more over the latest
interval, `historical-resolved` when a prior snapshot breached and the present
does not, otherwise `normal`.

**Eligible Liquidity is not portfolio value.** Daily holdings always count,
Weekly needs 14 days of notice, Monthly needs 45. Quarterly Gate and Illiquid
holdings never count toward guaranteed coverage and are reported separately.
These are deliberately conservative prototype rules, stated in the artifact
next to every number they produce.

**Critical is reserved.** Only three auditable Safety Overrides can produce it:
an active facility breach, a confirmed obligation inside 90 days with less than
full coverage, or an unwaived binding exclusion. Everything else is scored
0–100 from five visible factors, where the severest signal sets the base and
independent signals add capped escalation. Signals are never averaged.

**Urgency and Confidence are independent.** Weak evidence lowers Confidence and
never suppresses an urgent case.

**Conflicts are preserved.** Where two sources disagree the engine reports both,
narrows the conclusion and lowers Confidence. It does not pick whichever
supports a better story.

**`event_log.csv` is the Controlled Event Source.** An event is linked to a
client only where a declared transmission channel maps to something they
actually hold, and the link is always phrased as an explanation the record
supports rather than proven causation.

## Language

Cached drafts in `language/fixtures/` carry reviewed wording for the deep cases
in the client's own reporting language. Every draft is validated on each build:
it must cite only evidence items that exist in that client's packets, and its
numeric tokens must match the canonical English version exactly. A draft that
fails is dropped rather than published, so the workbench cannot show a
translation that has quietly changed a figure.

An optional live model adapter would receive one bounded Evidence Packet and a
fixed task type and clear the same validator. A model never calculates, ranks,
selects evidence, contacts a client, or executes anything.

## Tests

`python -m pytest engine/tests` runs 144 tests against the real supplied
dataset. They assert observable behaviour — artifact shape, queue ordering,
signal states and boundaries, evidence-graph integrity, bilingual parity, and
pinned regression facts for the demonstrated clients — rather than pandas
internals.
