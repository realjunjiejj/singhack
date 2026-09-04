# Builder 1 — Intelligence Engine, Evidence Model, and Workbench Artifact

## Assignment

Build the complete deterministic intelligence layer for **JB Clarity**. Turn the supplied Julius Baer challenge files into one versioned, schema-valid Workbench artifact that Builder 2 renders without reading raw data or inventing financial logic.

This is an execution brief. Implement the code, artifact, tests, and handoff. Do not stop after planning.

**Promise:** Know who to call, why, and how to begin.

**Thesis:** AI should not replace wealth advice; it should make every RM conversation timely, personal, and defensible.

Your output must let Priscilla Ong answer:

1. Which client conversation needs attention first?
2. What changed or may happen soon?
3. Why does it matter to this client?
4. What evidence supports it, and what remains uncertain?
5. How can the RM begin a human-led conversation?

## Why this wins

| Judging dimension | What the engine must prove |
|---|---|
| Client-centric innovation | Join portfolio facts, objectives, obligations, and relationship notes into one Client Case. |
| User experience | Pre-shape concise “why now?” explanations so the UI does no analytics. |
| Feasibility | Deterministic calculations, typed output, Controlled Event Source, traceability, uncertainty, and offline operation. |
| Strategic impact | Rank the full Book while proving three deep, relationship-specific cases. |

The winning story is not model sophistication. It is that Priscilla sees the right client, understands the whole situation, proves each statement, and prepares the conversation before the client notices the problem.

## Read before editing

Read in this order:

1. `AGENTS.md`
2. `CONTEXT.md`
3. `.scratch/jb-clarity/spec.md`
4. every file in `docs/adr/`
5. `contracts/workbench.schema.json`
6. `artifacts/workbench.fixture.json`
7. `docs/research/open-source-leverage.md`
8. `singhacks-jb-wealth-intelligence/README.md`
9. `singhacks-jb-wealth-intelligence/docs/DATA_DICTIONARY.md`
10. `git show prototype/infrastructure-state:.scratch/jb-clarity/infrastructure-state-prototype.html`

Use the canonical terms in `CONTEXT.md`. `event_log.csv` is authoritative for every 2026 event claim. Outside knowledge and model memory are not evidence.

## Ownership and fixed decisions

You own `engine/`, compatible additions to `contracts/workbench.schema.json`, generated `artifacts/workbench.json`, engine tests, and `THIRD_PARTY_NOTICES.md` if code is copied. Builder 2 owns `web/`; do not edit it.

- Default as-of date: `2026-08-26`.
- Snapshots: `2025-12-31`, `2026-02-27`, `2026-03-31`, `2026-06-30`, `2026-08-26`.
- Rank all 20 clients honestly.
- Deep cases: Hartono `CL-0001`, Cheung `CL-0012`, Margarethe `CL-0003`.
- Deep-case richness never changes ranking.
- Urgency and Confidence are independent.
- Only Safety Overrides produce Critical.
- Cached validated language is mandatory; live AI is optional.
- AI never calculates, selects facts, ranks, contacts clients, or executes actions.

## Required implementation shape

Use Python 3.11+, pandas, Pydantic v2, pytest, and `jsonschema`. Keep dependencies small. Create:

```text
engine/
  pyproject.toml
  README.md
  src/jb_clarity/
    cli.py
    build.py
    config/scoring.v1.json
    domain/{models,enums}.py
    ingestion/{loader,normalization,validation}.py
    calculations/{fx,exposure,liquidity,ltv,mandate,timeline}.py
    detectors/{credit,cash_needs,liquidity_restrictions,concentration,suitability,mandate,governance,open_loops,evidence_conflicts}.py
    evidence/{ids,packets,claims}.py
    ranking/{urgency,confidence,queue}.py
    language/{cached,validator}.py
    language/fixtures/{cl-0001.en,cl-0012.en,cl-0012.zh-Hant,cl-0003.en,cl-0003.de}.json
  tests/
    test_build_workbench.py
    test_contract.py
    test_queue.py
    test_evidence_integrity.py
    test_credit_signals.py
    test_liquidity_signals.py
    test_mandate_and_concentration.py
    test_governance_and_open_loops.py
    test_deep_cases.py
    test_language_integrity.py
artifacts/workbench.json
```

Expose:

```python
build_workbench(data_source: Path, as_of_date: date) -> WorkbenchModel
```

Required commands from repository root:

```bash
python -m pip install -e 'engine[dev]'
python -m jb_clarity.cli build --data singhacks-jb-wealth-intelligence/data --as-of 2026-08-26 --output artifacts/workbench.json
pytest engine/tests
```

Document them in `engine/README.md`.

## Build sequence and completion gates

### 1. Typed ingestion

Load all CSVs with explicit types and parse `rm_notes.json` into typed records. Index clients, portfolios, instruments, facilities, commitments, cash needs, transactions, notes, events, mandates, holdings by snapshot, and market series. Validate foreign keys and duplicate identifiers. Preserve or report orphans, missing calculation inputs, stale valuation dates, and contradictory totals; never silently discard them.

**Gate:** the loader reports 20 clients, 24 portfolios, five ordered snapshots, and a deterministic data-quality summary.

### 2. Workbench skeleton

Represent every required schema object with Pydantic. Generate:

- `meta.schemaVersion: "1.0.0"`;
- `meta.artifactKind: "generated"`;
- the fixed as-of date and ordered snapshots;
- one Queue item and one Client Case per client;
- stable IDs such as `CASE-CL-0001` and `PACKET-CL-0001-CREDIT`.

Use an injectable clock. `generatedAt` is the only intentionally variable field.

**Gate:** the generated artifact validates against `contracts/workbench.schema.json`, contains 20 unique cases, and repeats semantically with identical inputs.

### 3. Calculations

#### LTV

```text
LTV % = drawn amount / lending value × 100
distance to trigger = trigger % - LTV %
```

Never divide by raw collateral market value. Missing or non-positive lending value creates an Evidence Conflict.

- `active`: current LTV ≥ trigger.
- `near`: below trigger and within 5 percentage points, or moving toward it by at least 3 points over the latest comparable interval.
- `historical-resolved`: a prior snapshot breached and current LTV is below trigger.
- `normal`: none of the above.

When present state is near after a historic breach, show `near` and retain history in the signal/timeline.

#### Eligible Liquidity

For each confirmed or likely need calculate days to `due_from`, amount, currency, restricted assets, and coverage:

- include `Daily` holdings;
- include `Weekly` only with at least 14 days;
- include `Monthly` only with at least 45 days;
- exclude `Quarterly Gate` and `Illiquid` from guaranteed coverage and show them separately;
- convert with the as-of-date market-context pair using its documented quote convention;
- expose FX assumptions and lower Confidence if a direct pair is missing;
- do not count uncertain future calls as cash;
- do not allocate the same liquid asset twice without exposing the overlap.

Keep these conservative prototype rules in a named policy/configuration module.

#### Exposure, mandate, and suitability

- Aggregate `market_value_usd` across every client portfolio.
- Retain portfolio/service-model breakdowns.
- Include Custody in client concentration but exclude it from mandate compliance.
- Test mandate bands on applicable Discretionary/Advisory portfolios.
- Apply single-position limits only where `concentration_limit_applies == Y`.
- Use `underlying_reference` for structured-product look-through.
- When look-through weights are unavailable, name indicative underlying exposure without fabricating an amount.
- Evaluate binding sustainability exclusions separately from ordinary drift.
- Show evidenced waivers/client directions without erasing the underlying breach.
- Compare risk profile/objectives/source of wealth with actual exposure.

#### Time and events

- Calculate from exact values at all five snapshots.
- Preserve stale private-market valuation dates as caveats.
- Link events only when `primary_transmission` defensibly maps to the affected holding, sector, asset class, rate, commodity, region, or FX exposure.
- Phrase linkage as explanation supported by the event source, not certain causation.

**Gate:** pure calculation tests cover normal, boundary, missing-input, FX-direction, custody, stale-valuation, and look-through cases.

### 4. Signals, conflicts, and relationship memory

Create general detectors for facility state, cash needs, commitments, redemption restrictions, mandate drift, exclusions, concentration, look-through, suitability mismatch, KYC, and material source conflict. Do not use a hand-authored client allowlist.

Create an Open Loop candidate only when a dated note supports an unanswered question, an unresolved promise, a repeated deferred/agreed discussion, or a still-relevant client constraint. Each candidate needs note date, short exact excerpt, why it may be open, Confidence, evidence IDs, `confirmationRequired: true`, and state `candidate`. Search later notes for resolution before emitting it.

Governance Clock rules:

- before as-of: `overdue`;
- equal to as-of: `due-today`;
- 1–30 days after: `due-soon`;
- later: `future`.

At the fixed date no KYC is overdue. Tan Boon Huat is due soon on `2026-08-31`.

Conflicting totals remain visible with both sources. Narrow the conclusion and lower Confidence rather than choosing the stronger story.

**Gate:** `CL-0006`, `CL-0004`, `CL-0011`, and `CL-0009` emerge from general rules with the correct signal/open-loop/governance context.

### 5. Deterministic ranking

Put thresholds and weights in `scoring.v1.json`. Safety Overrides are exclusively:

1. current facility breach;
2. confirmed obligation starting within 90 days with Eligible Liquidity coverage below 100%;
3. unwaived binding exclusion or compliance breach.

Initial non-critical factor budget:

| Factor | Max | Rule |
|---|---:|---|
| Time urgency | 30 | Confirmed ≤30 days: 30; ≤90: 25; ≤180: 15; later: 5. Likely needs get at most 70% of confirmed points. |
| Threshold/history | 35 | Near trigger up to 35; historical-resolved breach 30; worsening outside near band 15. |
| Suitability/objective mismatch | 20 | Strong mismatch receives more than ordinary drift. |
| Financial exposure | 10 | Transparent configured bands relative to client AUM. |
| Relationship signal | 10 | Recent unanswered question or repeated material deferral receives most. |

Cap at 100. Critical sorts first. Non-critical scores ≥65 are High; others are Watch. A severe signal establishes the base; independent signals add capped contributions. Never average signals.

Stable order: Safety Override; score descending; earliest confirmed need ascending with missing last; client ID ascending.

Confidence begins at 100 and applies named, configured deductions for missing inputs, material conflicts, conclusion-relevant stale values, indicative look-through, and human confirmation. Map to High/Medium/Low with documented thresholds. Confidence does not alter Urgency.

**Gate:** every displayed point equals an emitted factor, repeated builds have identical ranks, and deep-case status never enters scoring.

### 6. Evidence and language

Every material claim cites Evidence Packet items. Items contain source file and stable record key. Derived metrics also include formula, exact inputs, unit, result, and snapshot date.

Keep facts, interpretations, assumptions, uncertainties, and conflicts separate. Fail artifact generation when a claim cites a missing item, crosses client/case boundaries without a shared-event explanation, makes an event claim without `event_log.csv`, or exposes an unavailable Guided Action.

Prepare cached canonical English for all deep cases, Traditional Chinese for Cheung, and German for Margarethe. Numbers, dates, currencies, and evidence IDs must be identical across languages. All client-ready content remains draft.

An optional model adapter receives one bounded packet plus a fixed task type. Reject and fall back to cache if output changes/adds a figure, uses an unsupported citation, or fails validation.

Adapt Anthropic’s Meeting Prep output checklist and human-review boundary from `docs/research/open-source-leverage.md`; write original JB Clarity templates or preserve required attribution.

**Gate:** automated integrity tests resolve every claim → evidence item → source, and language tests prove financial-token/citation parity.

## Required regression stories

### Hartono — `CL-0001` (primary technical walkthrough)

- `CF-0005` is SGD, not USD.
- Trigger: 70%.
- Breaches: about 78.50% on `2025-12-31`, 75.68% on `2026-02-27`.
- Resolved: about 58.86% on `2026-03-31`.
- Current `2026-08-26`: drawn SGD 8,000,000; raw collateral SGD 26,618,144.28; lending value SGD 13,525,392.14; LTV about 59.15%.
- Current state is safe. The cure came from higher lending value with unchanged borrowing, not recorded client action.
- Aggregate direct legacy coal/energy and energy-linked FCN exposure, with look-through limitations.
- Surface the SGD 9m 2027 property need and political/family constraint on selling the legacy stake.
- Precompute base and 15%-down collateral scenarios. Hold borrowing and advance-rate structure constant. Label them calculations, not forecasts.

### Cheung — `CL-0012`

- Show portfolio decline from about USD 30.13m to USD 28.03m.
- Ground the rising-yield/duration explanation in event and holding evidence.
- Join retirement, Income objective, medical spending, refusal to sell at a loss, and 2045 longest maturity.
- Preserve the USD 1.1m objective versus USD 1.28m planned-cash conflict.
- Make no life-expectancy prediction; explain that waiting until 2045 does not answer the near-term income question.
- Provide English and Traditional Chinese drafts with identical financial tokens/citations.

### Margarethe — `CL-0003`

- Conservative profile versus strongly equity-weighted inherited portfolio.
- Confirmed EUR 3.4m German inheritance-tax instalment before year-end.
- Reconcile the EUR 20.31m portfolio-base total to about USD 22.18m using the supplied EURUSD rate; explicitly explain that denomination, rather than manufacture a conflict or reduce Confidence.
- Treat widowhood and unfamiliarity as sensitive conversation context, never scoring points.
- Provide English and German drafts with identical financial tokens/citations.

### Supporting Book

- `CL-0006`: gated private credit, roughly USD 5m tuition near 1 September, likely USD 3m capital calls near 1 October, SGD assets versus USD obligations.
- `CL-0004`: unanswered 19 August “move everything to deposits?” question.
- `CL-0011`: fourth succession attempt and due-soon KYC.
- `CL-0009`: deployment agreed repeatedly but unexecuted.
- Detect every near-trigger facility and applicable mandate break generally.
- Recalculate all approximations and assert precise source-derived values.

## Contract and integration rules

- v1.0.0 meanings are frozen; prefer optional additive fields.
- Update schema, fixture, model, artifact, and tests together for contract changes.
- Preserve `workbench.fixture.json` as partial UI input.
- Money is numeric amount plus ISO currency; dates are ISO 8601; percentages use explicit percent units.
- Preserve full calculation precision and round only presentation text.
- Source references use dataset-relative files and stable keys.
- Notify Builder 2 at each checkpoint with schema version, artifact path/kind, generation/test commands, added fields, quality issues, and a sample case/packet ID.

## Open-source policy

- Reproduce AI WealthPilot’s typed-boundary and offline-fixture parity idea using our schema.
- Use Ghostfolio/Wealthfolio only as edge-case checklists; write original code.
- Defer Riskfolio-Lib, optimization, ML ranking, SHAP, LangGraph, live APIs, and databases.
- Do not copy Navam Invest; it is BSL 1.1.
- Record source repository, commit SHA, files, modifications, and notices for copied MIT/BSD/Apache code.

## Required verification

Test: full build; JSON Schema; fixed-clock repeatability; 20 unique contiguous ranks; all Safety Override boundaries; Urgency/Confidence independence; LTV states and missing lending value; liquidity timing/FX/restrictions; mandate applicability and exclusions; concentration/look-through; five-snapshot time logic; KYC boundaries; evidence graph integrity; conflicts; Open Loop lifecycle inputs; bilingual parity; and zero-network operation.

Run both the generation and complete test commands from a clean checkout.

## Definition of done

- Generated artifact is offline, reproducible, schema-valid, and contains all 20 ranked cases.
- Three deep cases and four named supporting stories pass regression tests.
- Every score, Confidence reason, Safety Override, assumption, and conflict is inspectable.
- Every material claim has a complete Evidence Chain.
- Hartono’s LTV uses lending value, SGD, and correct historical/current wording.
- Cached bilingual content passes parity tests.
- Builder 2 adopts the generated artifact without workflow changes.
- Handoff records commands, results, schema, artifact path, additions, uncertainties, and attribution.

The engine succeeds when the workbench can tell a defensible client story without redoing one calculation.
