# Builder 1 — Intelligence engine and Workbench contract

## Your mission

Build the deterministic intelligence engine behind **JB Clarity**. Your work must turn the supplied synthetic Julius Baer challenge data into one versioned, validated Workbench JSON artifact that Builder 2 can render without interpreting raw financial data.

The product promise is: **Know who to call, why, and how to begin.**

The pitch is: **AI should not replace wealth advice; it should make every RM conversation timely, personal, and defensible.**

Execute the implementation and tests. Do not stop after producing a plan.

## Read before editing

Read these sources in this order:

1. `AGENTS.md`
2. `CONTEXT.md`
3. `.scratch/jb-clarity/spec.md`
4. `contracts/workbench.schema.json`
5. `artifacts/workbench.fixture.json`
6. `.scratch/jb-clarity/infrastructure-state-prototype.html` from branch `prototype/infrastructure-state`
7. Every ADR in `docs/adr/`
8. `singhacks-jb-wealth-intelligence/README.md`
9. `singhacks-jb-wealth-intelligence/docs/DATA_DICTIONARY.md`

Use the glossary's exact terms in code, schemas, tests, and generated copy. In particular: Client Case, Priority Queue, Priority Rationale, Evidence Chain, Evidence Packet, Anticipatory Signal, Open Loop, Governance Clock, Meeting Brief, Urgency, Confidence, Safety Override, Eligible Liquidity, Guided Action, Client-Ready View, and Case Resolution.

Treat `event_log.csv` as the **Controlled Event Source** for every claim about a 2026 external event. Model memory and invented news are not evidence.

## Product outcome

Priscilla Ong manages a Book of 20 clients and 24 portfolios. Existing tools show holdings; JB Clarity must tell her which client conversation requires attention, why it matters to that client, what evidence supports it, what remains uncertain, and how to prepare.

The engine must rank all 20 clients honestly, while producing unusually deep Client Cases for:

- `CL-0001` — Hartono Wijaya Kusuma
- `CL-0012` — Cheung Kwok Wing
- `CL-0003` — Margarethe Voss-Brenner

The selected demo clients must never be artificially promoted in the Priority Queue.

## Ownership and collaboration boundary

You own:

- `engine/` — Python package, ingestion, validation, calculations, detectors, ranking, packet construction, and cached language data
- compatible evolution of `contracts/workbench.schema.json` — the shared JSON Schema already starts at v1.0.0
- `artifacts/workbench.json` — reproducible generated output for the fixed challenge dataset
- Engine tests and engine-facing documentation

Builder 2 owns `web/` and all interface code. Do not edit that directory.

The v1 contract and `artifacts/workbench.fixture.json` are already present, so Builder 2 can start immediately. Preserve the fixture as a stable UI development input. Your first usable milestone is a schema-valid generated `artifacts/workbench.json` with `meta.artifactKind: "generated"` and `meta.schemaVersion: "1.0.0"`.

## Infrastructure you are fitting into

The main integration seam has already been established:

1. `contracts/workbench.schema.json` defines the only data boundary between builders.
2. `artifacts/workbench.fixture.json` is a partial Hartono fixture for Builder 2's parallel start. It is clearly marked `artifactKind: "fixture"` and does not claim to contain the full Queue.
3. Your engine publishes `artifacts/workbench.json` with `artifactKind: "generated"`, all 20 clients, and the same schema version.
4. Builder 2 validates `schemaVersion` before adopting the generated artifact. A mismatch is a blocked integration, never an invitation for the UI to guess.
5. Builder 2 owns temporary RM workflow state; your artifact owns financial facts, calculations, citations, allowed actions, and cached language.

The runnable state harness at `.scratch/jb-clarity/infrastructure-state-prototype.html` on branch `prototype/infrastructure-state` records these invariants. Inspect it with `git show prototype/infrastructure-state:.scratch/jb-clarity/infrastructure-state-prototype.html`, or switch to that branch and open it directly in a browser.

Treat v1 as frozen for required fields and meanings. Add optional fields when necessary. If a breaking change is truly unavoidable, coordinate it before implementation, increment the major version, update the schema and fixture together, and leave the old path usable until Builder 2 adopts the new version.

### Your integration checkpoints

- **Checkpoint 1 — engine skeleton:** generation command exists and emits a JSON document with the v1 top-level shape.
- **Checkpoint 2 — contract-valid artifact:** `artifacts/workbench.json` validates, identifies itself as generated v1.0.0, and contains 20 ranked Client Cases.
- **Checkpoint 3 — evidence completeness:** the three deep cases and supporting Book cases satisfy their regression tests and every claim resolves to an Evidence Packet item.
- **Checkpoint 4 — UI hand-off:** tell Builder 2 the exact command, artifact path, schema version, and any optional fields added. Builder 2 should need no raw dataset access.

## Highest behavioral seam

Expose one primary behavior equivalent to:

`build_workbench(data_source, as_of_date) -> WorkbenchModel`

For this prototype, the default `as_of_date` is `2026-08-26`. Provide a command that writes the serialized result to `artifacts/workbench.json` from the supplied dataset. Keep calculations pure or deterministic wherever possible.

Tests should call this highest seam with the real supplied fixture dataset. Add narrower tests only where a calculation has a meaningful independent boundary.

## Shared Workbench contract

Implement against the existing JSON Schema with this stable conceptual shape. You may add optional fields, but do not remove, rename, or change the meaning of these concepts without coordinating with Builder 2:

- `meta`
  - schema version
  - as-of date
  - generated timestamp
  - source snapshot dates
  - data-quality summary
- `book`
  - RM identity
  - client and portfolio counts
  - Book summary
  - available filter values
  - ordered Priority Queue
- `book.priorityQueue[]`
  - stable case and client identifiers
  - client name, booking centre, and reporting language
  - Urgency tier and 0–100 score
  - optional Safety Override with rule identifier and reason
  - Confidence level and reasons, separate from Urgency
  - concise Priority Rationale
  - visible factor contributions
  - signal, Open Loop, and Governance Clock summaries
  - current/historical status wording
- `clientCases[]`
  - conclusion and `whyNow`
  - facts, interpretations, and uncertainties as separate collections
  - factor breakdown
  - Anticipatory Signals
  - Open Loop candidates
  - Governance Clocks
  - five-snapshot timeline and comparison data
  - Evidence Packets
  - allowed Guided Actions
  - editable Meeting Brief seed content
  - cached internal and client-language drafts where applicable
  - optional Hartono Collateral Stress Test scenarios
- `evidencePackets[]`
  - stable packet and item identifiers
  - client and case identifiers
  - as-of date and signal type
  - status, facts, interpretations, uncertainties, conflicts, and assumptions
  - urgency and confidence inputs
  - derived metrics with formula, input values, units, and snapshot date
  - source references with file and stable record key or row identity
  - allowed Guided Actions

Represent currency values as numeric amount plus ISO currency. Preserve full precision in data and calculations; round only presentation fields. Dates use ISO 8601. Ratios must identify whether the unit is a decimal or percentage.

The engine should precompute bounded Hartono stress scenarios so the browser selects a deterministic result rather than inventing financial calculations. Include assumption, collateral value, lending value, LTV, distance to trigger, and status for each allowed scenario.

## Deterministic analysis requirements

### Data ingestion and quality

- Load all supplied CSV and JSON sources with explicit types and stable identifiers.
- Validate referential integrity across clients, portfolios, holdings, instruments, facilities, mandates, commitments, cash needs, transactions, notes, and events.
- Detect missing inputs relevant to a conclusion, stale valuation dates, and material disagreement between client, portfolio, and holding totals.
- Preserve conflicts. Do not silently choose whichever source supports a stronger story.
- Aggregate client exposure across all of that client's portfolios while distinguishing managed and custody accounts.

### Urgency and Confidence

- Keep Urgency and Confidence as independent axes.
- Reserve **Critical** for these auditable Safety Overrides only:
  1. an active facility breach;
  2. a confirmed obligation beginning within 90 days with less than full Eligible Liquidity coverage;
  3. an unwaived binding exclusion or compliance breach.
- Score other cases from 0–100 using visible, versioned factors: time urgency, threshold proximity or historical breach, suitability/objective mismatch, financial exposure, and relationship signals.
- The highest-severity Advisory Insight establishes the base priority. Independent signals add capped escalation points; never average signals in a way that dilutes a severe issue.
- Derive exact scoring weights from the dataset distribution, store them as versioned configuration, and emit each factor contribution.
- Use deterministic stable ordering, including a documented tie-breaker.
- Confidence reflects completeness, source agreement, calculation quality, and required human confirmation. Low Confidence must not hide high Urgency.

### Anticipatory Signals

Implement and source-cite at least:

- facility LTV: active breach, near trigger, historical-resolved breach, and normal;
- confirmed and likely cash needs, time remaining, currency, and Eligible Liquidity;
- redemption gates and liquidity restrictions without equating a gate to total illiquidity;
- mandate asset-class bands and managed-versus-custody applicability;
- binding exclusions separately from ordinary drift;
- single-position and client-level concentration;
- structured-product look-through using `underlying_reference`, with limitations explicit;
- KYC due soon, due today, and overdue relative to the selected as-of date;
- material suitability or objective mismatch;
- material source conflicts.

### Relationship intelligence

Extract source-cited Open Loop **candidates** from dated RM notes:

- unanswered client questions;
- promises or commitments to revisit a topic;
- recurring discussions that were agreed or deferred but remain unresolved;
- client constraints that change what an otherwise reasonable Advisory Action would mean.

Every candidate needs its note date, source excerpt, why it may be open, Confidence, and `confirmationRequired: true`. The engine proposes; the RM confirms, defers, assigns, or dismisses.

At the default as-of date, do not label any KYC review overdue. Due-soon cases include Tan Boon Huat on `2026-08-31`; calculate all wording from dates rather than hard-coding it.

## Required regression stories

### Hartono — `CL-0001`

- Facility `CF-0005` breached its 70% trigger at the `2025-12-31` and `2026-02-27` snapshots: approximately 78.50% and 75.68% LTV.
- It resolved to approximately 58.86% at `2026-03-31`; the current status is safe, not an active breach.
- SGD 8m borrowing remained unchanged; the cure came from a higher lending value from the collateral portfolio, not recorded client action.
- Aggregate the direct coal/energy family exposure and energy-linked FCN look-through across portfolios. Keep look-through limitations visible.
- Surface the SGD 9m 2027 property need and the note-based family/political constraint against selling the legacy stake.
- Produce bounded, explicitly labelled what-if stress scenarios. They are calculations, not forecasts.

### Cheung — `CL-0012`

- Connect the energy-shock/rising-yield event evidence to duration-sensitive bond losses without claiming causation beyond the Controlled Event Source.
- Show the portfolio decline from roughly USD 30.13m to USD 28.03m and the long-dated US Treasury maturity in 2045.
- Preserve the conflict between the objective's USD 1.1m annual draw and the planned-cash record of USD 1.28m.
- Include retirement, medical spending, refusal to sell at a loss, and longevity/liquidity implications without making a life-expectancy claim.
- Supply cached canonical English and Traditional Chinese Client-Ready drafts with identical figures and evidence identifiers.

### Margarethe — `CL-0003`

- Show the Conservative profile against the strongly equity-weighted inherited portfolio.
- Surface the confirmed EUR 3.4m German inheritance-tax need before year-end.
- Preserve the material disagreement between current client/holding totals of roughly USD 22.18m and portfolio-record totals of roughly USD 20.31m; reduce Confidence accordingly.
- Treat widowhood and unfamiliarity with the inherited portfolio as sensitive relationship context, not a risk score.
- Supply cached canonical English and German Client-Ready drafts with identical figures and evidence identifiers.

### Supporting Book-wide stories

- `CL-0006`: gated private-credit exposure alongside a USD 5m tuition need around 1 September and likely USD 3m capital calls around 1 October, with SGD assets versus USD obligations.
- `CL-0004`: the unanswered 19 August question about moving everything to deposits.
- `CL-0011`: the fourth deferred succession discussion and KYC due in five days at the fixed as-of date.
- `CL-0009`: deployment was agreed more than once but remains unexecuted.
- Detect every facility trending near its trigger and every applicable mandate-band break from the data, not from a hand-written client allowlist.

Recalculate all stated approximations from source data and assert the precise values in tests.

## Meeting Brief and language payloads

For the three selected cases, emit editable seed content containing:

- what changed and why it matters now;
- factual evidence with packet item citations;
- interpretation separated from fact;
- uncertainty and Evidence Conflicts;
- a respectful opening question;
- two or three discussion options, phrased for RM review;
- specialist involvement where relevant;
- Open Loops and Governance Clocks;
- approved Guided Actions only.

Cached language is the required baseline. Any optional live model adapter must receive one bounded Evidence Packet and fixed task type, return structured output, cite only packet item identifiers, and fail closed to cached content if it changes a figure or uses an unsupported citation. A model never calculates, ranks, selects evidence, contacts a client, or executes a trade.

## Tests and verification

Build tests around observable behavior:

- full dataset → schema-valid Workbench artifact;
- repeat runs with the same inputs → identical semantic output;
- queue ordering, Safety Overrides, compound-signal caps, and Urgency/Confidence separation;
- active, near, historical-resolved, and normal LTV states;
- obligation window and Eligible Liquidity boundaries;
- managed/custody handling, mandate drift, exclusions, concentration, and look-through;
- KYC date boundaries;
- Evidence Conflicts and source traceability;
- regression facts for all named clients above;
- every language claim cites an existing packet item and every translated figure matches the canonical figure.

Do not test pandas implementation details. Provide one documented generation command and one documented test command. Run both before handoff.

## Out of scope

- autonomous advice, trading, orders, outreach, email, or calendar actions;
- live markets, live news, or external data;
- open-ended chat over the Book;
- production authentication, entitlements, encryption, deployment, or regulatory approval;
- definitive tax, legal, or suitability advice;
- automatic conflict resolution;
- a generic scenario engine beyond Hartono's bounded collateral what-if;
- persistence or multi-user workflow.

## Definition of done

Your work is complete when:

- Builder 2 has a stable JSON Schema and generated artifact containing all 20 ranked Client Cases;
- Hartono, Cheung, and Margarethe satisfy every regression story;
- all conclusions have a reproducible Evidence Chain;
- every score exposes its factor contributions and Confidence remains separate;
- Open Loops and Governance Clocks are present and date-correct;
- generation and tests pass from a clean checkout without network or AI credentials;
- you leave a concise handoff stating commands run, test results, schema version, generated artifact path, and remaining uncertainties.
