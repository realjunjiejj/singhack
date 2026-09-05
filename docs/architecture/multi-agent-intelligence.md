# Multi-agent intelligence entry point

## Decision

The first deep specialist directions are **Hidden Risk** and
**Prioritisation**.

- Hidden Risk proves intelligence that a normal portfolio screen misses. It
  combines every portfolio owned by a client, includes custody in total
  exposure, and reads structured products through `underlying_reference`.
- Prioritisation converts all detected conditions into the RM's scarce-attention
  decision: who to call first and why. Its language explains the existing
  deterministic order; it cannot assign points, tiers, Safety Overrides, or
  ranks.

Explanation remains a supporting analyst capability shared across Client
Cases. Tax-aware optimisation and geopolitical scenario analysis are deferred
until the required jurisdiction, household, factor-mapping, and assumption
controls exist.

## Public interface

Application code calls one function:

```python
analyse_dataset(
    data_source: Path | str,
    as_of_date: date = date(2026, 8, 26),
    *,
    clock: Callable[[], datetime] | None = None,
    narrative_provider: NarrativeProvider | None = None,
) -> IntelligenceRun
```

The CLI exposes the same seam:

```bash
python -m jb_clarity.cli analyse \
  --data singhacks-jb-wealth-intelligence/data \
  --as-of 2026-08-26 \
  --output artifacts/intelligence.json
```

`IntelligenceRun.workbench` is the unchanged Workbench contract. A new UI can
therefore use the existing queue, Client Cases, Evidence Packets, and Meeting
Briefs, then use `agentReports` for specialist views without reading raw data.

## Meaning of “any dataset”

The engine accepts any dataset for which an explicit, reviewed adapter maps
the source into the canonical wealth roles. It does not ask a model to guess
whether an arbitrary field means market value, tax domicile, ownership, or an
obligation.

The first adapter recognises the published challenge bundle. Intake profiles
file names, media types, headers, row counts, byte sizes, and SHA-256 hashes.
When no adapter matches, the result is `needs-mapping`; when a known bundle has
the wrong schema, it is `blocked`. Neither state publishes partial financial
insights. A request dated before the latest supplied snapshot is also blocked,
so future observations cannot leak into an earlier analysis.

Add a new adapter by implementing a deterministic transformation from the
source schema to the same canonical entities used by `build_workbench`. Its
tests must cover identifiers, ownership joins, types, currencies, snapshot
cutoffs, duplicates, orphans, source fingerprints, and declared unsupported
capabilities.

## Analyst team

```text
Dataset directory
  → Dataset Steward
  → approved dataset adapter
  → deterministic Workbench and Evidence Packets
      ├─ Hidden Risk Specialist (deep)
      ├─ Advisory Context Analyst (supporting)
      └─ Prioritisation Specialist (deep)
  → Evidence Auditor
  → Intelligence Run
  → RM Workbench
```

| Role | Responsibility | May not do |
|---|---|---|
| Dataset Steward | Profile source shape and expose data-quality issues. | Guess financial semantics or repair source records silently. |
| Hidden Risk Specialist | Shape concentration, household aggregation, custody, source-of-wealth, and look-through evidence into findings. | Invent component weights or recalculate outside the deterministic engine. |
| Advisory Context Analyst | Add supported portfolio-change and Controlled Event Source context. | Claim measured performance attribution from five snapshots. |
| Prioritisation Specialist | Explain every case's visible factor contributions, Urgency, Confidence, and rank. | Set or alter any score, tier, override, or rank. |
| Evidence Auditor | Ensure each finding remains inside its declared Evidence Packets. | Resolve a conflict or approve advice. |

Every finding exposes `clientId`, `caseId`, its direction, limitations,
Evidence Packet identifiers, evidence-item identifiers, and any deterministic
metrics or factors needed by the UI. No agent transcript or chain-of-thought is
part of the interface.

## Optional model integration

Implement `NarrativeProvider.generate(NarrativeRequest) -> NarrativeDraft` in
the bank-approved model gateway and inject it into `analyse_dataset`.

The provider is called only for the two deep specialist reports. Each request
contains one client finding, a fixed task, canonical deterministic language,
and an allowlist of Evidence Packet and item identifiers. It never receives the
raw Book.

The validation gate rejects generated language when it:

- cites evidence outside the finding's allowlist;
- provides no evidence citation;
- introduces a financial figure absent from the canonical language; or
- omits a required narrative field.

Provider failure or invalid output leaves the deterministic finding intact.
Model language can change only `summary` and `whyItMatters`; calculations,
metrics, Urgency, Confidence, rank, and permitted RM actions are immutable.

## UI integration shape

```json
{
  "schemaVersion": "1.0.0",
  "runId": "RUN-…",
  "status": "completed",
  "adapterId": "jb-wealth-challenge-v1",
  "deepFocus": ["hidden-risk", "prioritisation"],
  "datasetProfile": { "files": [] },
  "agentReports": [],
  "workbench": {}
}
```

The UI should display specialist findings as explanations of evidence, not as
autonomous advice. Advisory Actions still require RM review and no route in
this module contacts a client or executes a transaction.
