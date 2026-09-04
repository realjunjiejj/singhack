# Agent brief — make JB Clarity reusable across client-book datasets

## Assignment

Make JB Clarity accept and correctly process a second wealth-management client book without changing the existing SingHacks demonstration, weakening evidence traceability, or adding client-specific logic.

This is a portability vertical slice across ingestion, deterministic analytics, the Workbench artifact, and the small amount of presentation that currently assumes the demonstration dataset.

The product promise remains:

> Know who to call, why, and how to begin.

The result is complete only when an independently generated second dataset passes ingestion, produces a schema-valid Workbench artifact, renders in the existing UI, and proves through tests that its conclusions came from the new records.

## Hackathon priority

This work is **not required to demonstrate the core challenge solution**. The challenge explicitly rewards depth in selected capabilities rather than breadth across every possible input format. The current 20-client Book already proves the product story.

For the hackathon, the useful claim is narrower:

> JB Clarity is reusable across client books through a documented canonical data contract. A source-system adapter maps each bank's data into that contract.

The minimum judge-facing proof is:

1. the existing SingHacks Book still works;
2. a second synthetic Book with different client, portfolio, instrument and RM identifiers also works;
3. changing a source record changes the resulting Client Case for the documented reason;
4. no component requires the three demonstration-client identifiers to render the new Book.

Complete the minimum proof before attempting convenient spreadsheet import, automatic schema inference, multi-bank connectors, or live data ingestion.

### Hackathon cut line

If the submission deadline is close, deliver only this cut:

- complete Steps 1, 2, 5, 8 and 10;
- keep the existing canonical filenames and columns;
- demonstrate the independently generated second Book;
- document that source-system column mapping is the next adapter layer;
- preserve every current test and demo path.

Treat Steps 3, 4, 6, 7, 9 and 11 as post-submission hardening unless the core demonstration has already been rehearsed successfully. A reliable second-Book proof is strategically stronger than a partially working “upload anything” feature.

## Required reading before editing

Read these files completely:

- `AGENTS.md`
- `CONTEXT.md`
- `.scratch/jb-clarity/spec.md`
- `docs/adr/0004-use-deterministic-prioritisation-and-ai-explanation.md`
- `docs/adr/0005-make-uncertainty-and-ai-grounding-visible.md`
- `docs/adr/0007-separate-analytics-presentation-and-language-generation.md`
- `docs/adr/0010-preserve-time-and-ranking-integrity.md`
- `docs/adr/0012-lead-with-client-value-then-prove-trust.md`
- `engine/README.md`
- `web/README.md`
- `singhacks-jb-wealth-intelligence/README.md`
- `singhacks-jb-wealth-intelligence/docs/DATA_DICTIONARY.md`
- `contracts/workbench.schema.json`

If the work is tracked in a GitHub Issue, also follow `docs/agents/issue-tracker.md` and `docs/agents/triage-labels.md`. Treat the published issue as authoritative if it conflicts with this brief.

## Current state to preserve

The repository currently has two intentionally separate contracts:

1. **Canonical source dataset → engine.** The Python engine reads 11 CSV files and one JSON notes file from a directory.
2. **Workbench artifact → UI.** The Next.js application reads `artifacts/workbench.json` through the versioned JSON Schema and adapter.

The frontend boundary is already portable: any valid Workbench artifact with schema version `1.0.0` can render. The main work is making the source-data boundary explicit, configurable and demonstrably independent of the supplied Book.

Preserve these verified behaviors:

- deterministic Priority Queue ordering;
- separate Urgency and Confidence;
- only the three auditable Safety Overrides may assign Critical Urgency;
- full Evidence Chains with source file, record key, field, calculation and uncertainty;
- `event_log.csv` or its canonical equivalent remains the Controlled Event Source;
- no model knowledge may supply a market or geopolitical fact;
- no browser-side financial calculation, ranking or translation;
- RM review and approval remain required;
- no trade, message, client contact or other autonomous Advisory Action;
- current Hartono, Cheung and Margarethe behavior and screenshots remain valid;
- generated artifacts remain reproducible when `--generated-at` is fixed;
- the application continues to run without an AI key or external network request.

## Portability definition

Support two input paths.

### Path A — canonical dataset

A new Book using the canonical filenames, grains, columns and types must work by passing its directory to the existing build command. Different record counts, identifiers, currencies, snapshot dates and RM names are expected.

### Path B — mapped dataset

A new Book with different filenames or column names may provide a declarative mapping file. The mapping renames source tables and columns into the canonical dataset before validation and analytics.

Path B supports structural renaming, explicit types and declared values. It does not infer financial meaning or invent missing values.

## Non-goals

Keep these outside this slice:

- guessing an arbitrary spreadsheet's meaning;
- LLM-generated data mappings;
- OCR or PDF ingestion;
- vendor-specific live connectors;
- streaming or intraday processing;
- automated translation of Client-Ready content;
- household/entity resolution across unlinked identifiers;
- deriving missing lending values, mandate limits, FX rates or event transmission channels;
- silently repairing malformed financial records;
- weakening validation so more datasets appear to load.

When required information is absent, fail with an actionable validation message or mark the related capability unavailable. Prefer visible incompleteness to a plausible fabrication.

## Target architecture

Keep the existing boundary intact:

```text
source files
    ↓
explicit mapping + type coercion
    ↓
canonical source tables
    ↓
referential and arithmetic validation
    ↓
deterministic calculations and detectors
    ↓
Evidence Packets + Priority Queue
    ↓
schema-valid workbench.json
    ↓
existing frontend adapter and UI
```

The mapping layer belongs under `engine/src/jb_clarity/ingestion/`. Analytics and UI components must only see canonical field names.

## Implementation sequence

### 1. Establish the red portability test

Create a test helper that copies the supplied dataset into a temporary directory and systematically changes identity-level data:

- every client ID;
- every portfolio ID;
- every instrument ID;
- every facility, need, commitment, transaction and note ID;
- the RM ID and name;
- booking-centre labels;
- at least one base currency where the supplied FX table supports it.

Update every foreign key consistently. Build from the changed directory.

The initial test must fail only where the system contains a genuine portability assumption. Do not weaken the changed dataset until it happens to pass.

Completion criterion: the test demonstrates at least one current portability failure and records that failure in the implementation notes before production code is changed.

### 2. Define the canonical source contract

Add one authoritative, machine-readable description of every canonical table:

- canonical table name;
- default filename;
- grain;
- required columns;
- optional columns;
- identifier columns;
- string, numeric, boolean and ISO-date types;
- nullable fields;
- primary key;
- foreign keys;
- snapshot-dependent column families where applicable.

Recommended location:

```text
engine/src/jb_clarity/ingestion/source_contract.py
```

The existing challenge Data Dictionary is useful evidence but must not become executable code through duplicated prose. Encode the source contract once and make the loader and validator consume it.

At minimum, identifier columns must be read as strings at parse time rather than converted after pandas inference. Invalid numeric, boolean and date values must identify the file, row/record and field that failed.

Completion criterion: tests cover every required table and every canonical type family, and the current challenge data loads without changing any source file.

### 3. Add a dataset manifest

Support an optional `dataset.manifest.json` inside a data directory. Keep the existing CLI invocation backward compatible when no manifest exists.

Use a versioned shape similar to:

```json
{
  "schemaVersion": "1.0.0",
  "datasetId": "synthetic-book-two",
  "displayName": "Synthetic Book Two",
  "asOfDate": "2026-08-26",
  "rmId": "RM-NEW-001",
  "files": {
    "clients": "customers.csv",
    "portfolios": "accounts.csv",
    "holdings": "positions.csv"
  },
  "columns": {
    "clients": {
      "client_id": "customer_key",
      "client_name": "customer_name"
    },
    "portfolios": {
      "portfolio_id": "account_key",
      "client_id": "customer_key"
    }
  }
}
```

The exact schema may be refined, but retain these properties:

- versioned;
- explicit source-to-canonical direction;
- JSON Schema validated;
- unknown table or canonical field names rejected;
- duplicate canonical mappings rejected;
- one source column cannot ambiguously populate several canonical meanings;
- mapping performs rename/coercion only;
- error messages reference the source name the user recognizes;
- source references in Evidence Packets remain stable and honest.

Decide and document whether Evidence Packet `sourceReference.file` stores the original source filename or canonical table filename. Prefer the original filename because an RM or reviewer must be able to locate the actual record. Whichever choice is made, test it.

Completion criterion: the same second dataset builds once with canonical names and once with renamed files/columns plus a manifest; the two artifacts are semantically equivalent apart from source-reference filenames and generation metadata.

### 4. Validate dataset capabilities explicitly

Classify source tables into:

- **core:** required to construct a Book and portfolio history;
- **capability inputs:** required only for a particular detector or surface.

Start conservatively. A missing core table blocks the build. For a missing capability input, either:

1. block the build with a precise message; or
2. supply a typed empty canonical table and publish a Data Quality issue stating that the capability is unavailable.

Choose option 2 only after verifying that every downstream calculation handles an empty table correctly. Do not broadly catch exceptions.

Examples of capability-specific absence:

- no facilities → no credit or Collateral Stress Test capability;
- no commitments → no uncalled-commitment assessment;
- no RM notes → no Open Loops or note-derived client constraints;
- no event log → no event-grounded explanations, with no fallback to model memory;
- no cached language fixture → English canonical Client-Ready draft only.

Add capability availability to artifact metadata only if the UI genuinely needs it. Any contract change requires a schema-version decision and corresponding adapter tests.

Completion criterion: each supported missing-capability case has one focused test proving graceful behavior, and unsupported absence fails before analytics begin.

### 5. Remove snapshot-count and date assumptions

Discover snapshot dates from canonical holdings after type validation. Require:

- at least two distinct ISO dates for change explanations;
- strictly ordered unique dates;
- current snapshot equal to the greatest supplied date unless the manifest explicitly selects an earlier as-of snapshot;
- market data required by an active calculation to exist for the relevant date;
- facility and instrument wide-column dates to be consistent with declared snapshot dates, or be normalized into a long canonical history before calculations.

Replace RM-facing phrases such as “five supplied snapshots” with count-aware language derived from the data. Replace any fixed date or snapshot-count assumption in tests with dataset-driven assertions unless the test intentionally pins a SingHacks regression fact.

Do not silently compare non-adjacent dates when a required intermediate point is absent. State the comparison endpoints in the Evidence Chain.

Completion criterion: one test dataset with three snapshots and one with six snapshots both produce truthful timeline labels, period calculations and evidence references.

### 6. Make RM scope explicit

The current build takes RM identity from the first client row. Replace that implicit assumption.

Support one of these explicit entry points:

- manifest `rmId`;
- CLI `--rm-id`;
- both, with the CLI taking precedence.

For a dataset containing several RMs, filter every source consistently to the selected RM's Book before calculations. If filtering cannot be proven safe because ownership is ambiguous, fail with a message listing the available RM identifiers.

Never combine clients from several RMs while displaying the identity of the first row.

Completion criterion: a two-RM test builds either RM independently, with the correct client count, RM identity and no cross-RM Evidence Packet.

### 7. Externalize dataset taxonomies

Move source-vocabulary assumptions that affect results into versioned configuration:

- event transmission-channel mappings;
- thematic concentration keywords;
- recognized liquidity tiers and settlement assumptions;
- boolean encodings if mapped sources use values other than the canonical encoding;
- asset-class aliases used by suitability and mandate logic.

Keep one canonical vocabulary inside the analytics layer. The adapter maps source labels into it.

Unknown values must produce a Data Quality issue and must not be assigned to the nearest-sounding category. For example, an unknown event transmission channel produces no event-to-holding link until mapped.

Completion criterion: a test adds one new source label through configuration and proves that the relevant detector begins working without a detector-code edit; the same label without configuration remains visibly unsupported.

### 8. Remove presentation assumptions about the demonstration Book

Update `web/src/components/queue/PriorityQueue.tsx` so the quick-access chips behave correctly for any artifact.

Required behavior:

- when Hartono, Cheung and Margarethe exist, retain the current hackathon shortcuts and order;
- otherwise show up to three artifact-derived featured cases, using Priority Queue order and real client names;
- label the section “Demo cases” only for the SingHacks Book; use “Featured cases” for other Books;
- never render a disabled shortcut for an identifier that is absent;
- keep the complete Priority Queue and filtering behavior unchanged.

Do not add client identifiers to other UI components. Test with an artifact containing none of the SingHacks IDs.

Completion criterion: frontend tests prove both the existing demonstration shortcuts and the generic fallback.

### 9. Preserve honest language behavior

Every client receives an English canonical Client-Ready draft derived from its Meeting Brief. Cached non-English drafts are optional and remain accepted only after financial-token and evidence-reference validation.

For a new Book without a cached translation:

- render the canonical English draft;
- clearly state that the reporting-language version is unavailable;
- keep the rest of the case usable;
- do not pretend the client's reporting language is English;
- do not call an external translation service during the core flow.

Strengthen translation validation while working in this area:

- compare ordered financial-token occurrences rather than sets;
- detect duplicated, omitted, reordered or swapped amounts where order changes meaning;
- require the translated draft to preserve the intended evidence references;
- fail closed to the canonical draft.

Completion criterion: tests cover a new unsupported reporting language, a correct cached translation, a swapped-figure translation, a duplicated-figure translation and an unknown evidence reference.

### 10. Prove a genuinely different Book

Create a compact synthetic portability fixture or deterministic fixture generator under the test tree. Keep it small enough to review.

It must contain:

- a different RM;
- at least four clients;
- different IDs and names;
- at least two portfolios for one client;
- three or more snapshots with dates different from the challenge dates;
- at least two currencies with supplied FX data;
- one facility approaching or crossing a trigger;
- one planned obligation;
- one mandate-band or exclusion issue;
- one genuine unanswered relationship thread and one answered question that must not become an Open Loop;
- one event with a configured transmission channel and matching holding;
- one unknown event channel that remains unlinked and visible as unsupported;
- one client reporting language without a cached translation;
- one intentionally lagged valuation disclosed as Data Quality attention.

Do not copy the SingHacks client stories and rename them. The fixture must exercise the same rules through different facts.

Assertions must prove:

- the expected client becomes Critical only through an allowed Safety Override;
- the queue changes when the facility or obligation is changed;
- event wording comes from the new Controlled Event Source;
- every displayed claim and timeline point resolves to evidence from the new dataset;
- no SingHacks client name, ID, event, date or RM appears in the new artifact;
- the artifact validates against the Workbench schema;
- the frontend renders and navigates the new Book;
- no external network request is made.

Completion criterion: these assertions pass against both canonical and manifest-mapped versions of the synthetic Book.

### 11. Add operator-facing commands

Add a validation command that checks a dataset without writing a Workbench artifact. A suitable interface is:

```bash
python3 -m jb_clarity.cli validate-data \
  --data /path/to/book \
  --manifest /path/to/dataset.manifest.json \
  --rm-id RM-NEW-001
```

The build command should accept the same dataset-selection options:

```bash
python3 -m jb_clarity.cli build \
  --data /path/to/book \
  --manifest /path/to/dataset.manifest.json \
  --rm-id RM-NEW-001 \
  --as-of YYYY-MM-DD \
  --output artifacts/workbench.json
```

Validation output must summarize:

- dataset and schema version;
- selected RM;
- client, portfolio, holding and snapshot counts;
- enabled and unavailable capabilities;
- warnings and blocking errors;
- resolved source filenames;
- whether generation may proceed.

Never print full RM notes or sensitive record contents in normal validation output.

Completion criterion: command-level tests cover successful validation, unsupported manifest version, missing core file, bad foreign key, invalid date, invalid numeric value and ambiguous multi-RM selection.

### 12. Document and demonstrate the portability claim

Update `engine/README.md` with:

- the canonical dataset contract location;
- manifest schema and example;
- canonical and mapped build commands;
- capability-availability behavior;
- multi-RM selection behavior;
- an explicit statement of unsupported arbitrary-format ingestion.

Update `web/README.md` only where the run sequence changes.

Add a short judge-facing demonstration note:

1. show the SingHacks Book;
2. run one command against the synthetic second Book;
3. refresh or restart the Workbench;
4. point out the new RM, new clients and changed snapshot count;
5. open one Evidence Chain;
6. return to the SingHacks artifact for the main pitch.

Keep this optional demonstration under 30 seconds. The core Hartono–Cheung–Margarethe story remains the primary demo.

Completion criterion: a teammate unfamiliar with the implementation can follow the documented commands from a clean checkout and render both Books.

## Expected files

The exact decomposition may change, but the implementation will likely touch:

```text
engine/src/jb_clarity/cli.py
engine/src/jb_clarity/ingestion/loader.py
engine/src/jb_clarity/ingestion/validation.py
engine/src/jb_clarity/ingestion/source_contract.py
engine/src/jb_clarity/ingestion/manifest.py
engine/src/jb_clarity/config/
engine/src/jb_clarity/calculations/timeline.py
engine/src/jb_clarity/detectors/explanation.py
engine/src/jb_clarity/language/validator.py
engine/tests/
contracts/dataset-manifest.schema.json
web/src/components/queue/PriorityQueue.tsx
web/src/tests/
web/e2e/
engine/README.md
web/README.md
```

Avoid changing `contracts/workbench.schema.json` unless the UI needs new information. If it changes, bump the schema version, update the fixture and generated artifact, add backward/forward rejection tests, and coordinate the frontend adapter in the same branch.

## Verification commands

Run from the repository root unless a command changes directory:

```bash
python3 -m pip install -e 'engine[dev]'
python3 -m pytest engine/tests
python3 -m jb_clarity.cli validate-data --data singhacks-jb-wealth-intelligence/data
python3 -m jb_clarity.cli build \
  --data singhacks-jb-wealth-intelligence/data \
  --as-of 2026-08-26 \
  --generated-at 2026-09-04T13:54:07.411866+00:00 \
  --output artifacts/workbench.json
```

Then:

```bash
cd web
npm ci
npm run sync-data
npm test
npx tsc --noEmit
npm run build
npm run test:e2e
```

Also run the equivalent validation and build commands against the second synthetic Book and its mapped variant.

Every command must pass before handoff. Record exact test counts and any warning intentionally retained.

## Acceptance criteria

The work is accepted only when all of the following are true:

- [ ] The original SingHacks dataset produces a schema-valid artifact and preserves pinned regression facts.
- [ ] A second Book with different identities and dates produces a schema-valid artifact.
- [ ] The second Book works through both canonical filenames and a declarative mapping manifest.
- [ ] Source types are explicit and invalid values fail with actionable record-level errors.
- [ ] Snapshot count and RM-facing wording are data-driven.
- [ ] Multi-RM input requires an explicit RM and never mixes Books.
- [ ] Unknown taxonomies produce visible Data Quality output rather than guessed mappings.
- [ ] Timeline values and RM-facing claims resolve to source evidence.
- [ ] The existing three demonstration shortcuts remain for the SingHacks artifact.
- [ ] A different artifact receives real featured-case shortcuts without hardcoded IDs.
- [ ] Missing translated content degrades to canonical English without blocking the case.
- [ ] Translation validation rejects changed, swapped, duplicated or uncited financial content.
- [ ] The core frontend makes no external network request.
- [ ] All engine, frontend, type, build and browser tests pass.
- [ ] Documentation truthfully distinguishes canonical portability from arbitrary-format ingestion.

## Handoff format

When finished, report:

1. branch and final commit;
2. the canonical source-contract version;
3. manifest example path;
4. commands used for the original and second Books;
5. client/portfolio/snapshot counts produced for each;
6. exact automated-test results;
7. screenshots or recording of the second Book in the Workbench;
8. capability gaps for partially populated datasets;
9. remaining production risks;
10. any Workbench contract or UI behavior change requiring coordination.

Do not report “supports any dataset.” Report the precise source shapes, mappings and capability conditions that were actually tested.

## Definition of done

Dataset portability is done when the system proves this chain twice with two genuinely different Books:

```text
source record
→ explicit canonical mapping
→ validated calculation
→ source-cited Advisory Insight
→ deterministic Priority Queue
→ usable RM conversation preparation
```

The second proof must require no client-specific code, no manual artifact editing and no weakening of the current trust boundaries.
