# Continuation Handoff — Multi-Agent Intelligence Entry Point

## Status

This work is **in progress and not ready to commit or merge**.

The first implementation slice exists locally, but an independent review found
contract, model-egress, data-quality, and evidence-audit gaps. New regression
tests were added for several of those gaps and the focused test file is
currently red: **5 failures, 8 passes**.

No commit or push was made for this change.

The unrelated untracked `.pptx-build/` directory belongs to the user. Leave it
untouched and exclude it from any future commit.

## Product decision already made

The two deep specialist directions are:

1. **Hidden Risk** — the strongest differentiated capability because it finds
   risk that is invisible in an individual portfolio but visible after
   whole-client aggregation, custody inclusion, or structured-product
   look-through through `instruments.underlying_reference`.
2. **Prioritisation** — converts every detected condition into the RM's scarce
   attention decision: who to call first, why, how confident the evidence is,
   and which deterministic factors defend the rank.

Explanation is a supporting capability used across cases. Tax-aware analysis
and geopolitical scenarios are deferred because the current data lacks the
household/jurisdiction and factor-mapping controls needed to make them robust.

Preserve these fixed boundaries:

```text
source data
  → explicit dataset adapter
  → deterministic calculations and detectors
  → versioned Evidence Packets
  → specialist analysis
  → optional bounded language
  → RM review and approval
```

AI may explain evidence. It must not calculate financial facts, select
authoritative data, assign ranks, alter Safety Overrides, resolve conflicts,
contact clients, or execute Advisory Actions.

## Public seam

The intended application interface is:

```python
analyse_dataset(
    data_source: Path | str,
    as_of_date: date = date(2026, 8, 26),
    *,
    clock: Callable[[], datetime] | None = None,
    narrative_provider: NarrativeProvider | None = None,
) -> IntelligenceRun
```

The matching CLI is:

```bash
PYTHONPATH=engine/src python -m jb_clarity.cli analyse \
  --data singhacks-jb-wealth-intelligence/data \
  --as-of 2026-08-26 \
  --generated-at 2026-09-05T00:00:00+08:00 \
  --output artifacts/intelligence.json
```

The current adapter recognises the supplied challenge bundle. Unknown source
shapes return `needs-mapping` with a file/header/hash profile rather than
guessing financial semantics. A recognised bundle with invalid columns returns
`blocked`. An as-of date earlier than the newest snapshot is blocked so future
records do not leak into an earlier analysis.

## Files added

- `engine/src/jb_clarity/intelligence/__init__.py`
  - exports `analyse_dataset` and `IntelligenceRun`.
- `engine/src/jb_clarity/intelligence/models.py`
  - Pydantic contracts for dataset profiles, diagnostics, findings, agent
    reports, and the complete Intelligence Run.
- `engine/src/jb_clarity/intelligence/intake.py`
  - profiles CSV/JSON files using headers, row counts, byte sizes, and SHA-256;
    selects adapter `jb-wealth-challenge-v1` only when all canonical files are
    present.
- `engine/src/jb_clarity/intelligence/entrypoint.py`
  - implements `analyse_dataset`, adapter selection, as-of protection, run ID,
    Workbench construction, and team execution.
- `engine/src/jb_clarity/intelligence/team.py`
  - runs five roles in stable order:
    1. Dataset Steward
    2. Hidden Risk Specialist — deep
    3. Advisory Context Analyst — supporting
    4. Prioritisation Specialist — deep
    5. Evidence Auditor
- `engine/src/jb_clarity/intelligence/provider.py`
  - optional narrative-provider seam and output validation. This is the main
    unfinished security area; see the blockers below.
- `engine/tests/test_intelligence_entrypoint.py`
  - public-seam tests for supported/unsupported data, hidden risk,
    prioritisation, evidence bounds, CLI output, as-of safety, schema errors,
    optional model output, and material data-integrity behavior.
- `docs/architecture/multi-agent-intelligence.md`
  - architecture and UI integration notes. Review and correct its model-safety
    claims after implementing the blockers.
- `artifacts/intelligence.json`
  - generated 1.5 MB integration fixture with 20 clients, 14 Hidden Risk
    findings, 20 supporting explanation findings, 20 priority findings, and
    the embedded Workbench. **This artifact is currently invalid against the
    frozen Workbench schema and must be regenerated after the serializer fix.**

## Files modified

- `engine/src/jb_clarity/__init__.py`
  - exports `analyse_dataset` alongside `build_workbench`.
- `engine/src/jb_clarity/cli.py`
  - adds the `analyse` command and writes an Intelligence Run JSON artifact.
- `engine/README.md`
  - documents the new function, CLI, and architecture note.
  - currently says the full suite has 192 tests, which was true before the
    latest red regression tests were added. Update only after the final full
    run.

## Behavior that was green before the safety-review tests

The focused entry-point suite reached **10 passing tests** before the review
regressions were added. It proved:

- the challenge dataset produces the same semantic Workbench as
  `build_workbench`;
- the team runs in stable order;
- Hartono's Hidden Risk finding exposes 44.99% combined energy exposure,
  whole-client aggregation, structured-product underlying evidence, and the
  missing-component-weight limitation;
- Prioritisation preserves the deterministic 20-client queue;
- unknown data returns `needs-mapping` rather than guessed insights;
- earlier as-of requests are blocked;
- malformed known schemas are blocked;
- every finding cites items inside its declared Evidence Packets;
- the CLI writes a single UI-ready artifact;
- invalid model figures/citations fall back to deterministic wording.

The full pre-review engine suite then passed:

```text
192 passed, 2 warnings in 32.58s
```

The two warnings are environment-level pandas optional-dependency warnings:
the installed `numexpr` and `bottleneck` versions are older than pandas prefers.
They did not fail the suite.

Formatting was also green before the latest test edits:

```bash
black --check engine/src/jb_clarity/intelligence \
  engine/src/jb_clarity/cli.py \
  engine/tests/test_intelligence_entrypoint.py
```

Run it again after completing the fixes.

## Current red state

Run:

```bash
PYTHONPATH=engine/src python -m pytest \
  engine/tests/test_intelligence_entrypoint.py -q
```

Latest result:

```text
5 failed, 8 passed
```

The five expected failures are:

1. `test_embedded_workbench_keeps_its_frozen_contract`
   - `IntelligenceRun.to_contract_dict()` removes required null fields from the
     nested Workbench.
2. `test_material_data_integrity_issue_blocks_outward_insights`
   - the Dataset Steward reports material issues but still returns completed.
3. `test_optional_model_provider_can_only_enrich_bounded_deep_findings`
   - the test now passes `narrative_policy`, which is not implemented yet.
4. `test_unsafe_model_output_is_rejected_without_losing_deterministic_insights`
   - same missing `narrative_policy` interface.
5. `test_model_provider_requires_an_explicit_egress_policy`
   - a provider currently runs without an explicit authorization/redaction
     policy.

These tests are intentional specifications. Make the implementation green;
do not delete or weaken them merely to restore the test count.

## Independent review blockers

### 1. Preserve the frozen Workbench contract

`IntelligenceRun.to_contract_dict()` in
`engine/src/jb_clarity/intelligence/models.py` uses a generic
`model_dump(..., exclude_none=True)`. That bypasses
`WorkbenchModel.to_contract_dict()`, which deliberately preserves required-null
keys such as:

- `urgency.safetyOverride`
- `meetingBrief.specialistSuggestion`

The generated artifact had 38 nested Workbench schema errors.

Required fix:

- serialize the outer Intelligence Run separately;
- set `payload["workbench"] = self.workbench.to_contract_dict()` when a
  Workbench is present;
- keep the new schema-validation regression green;
- make the CLI validate before writing or fail closed;
- regenerate `artifacts/intelligence.json`.

Completion criterion: `payload["workbench"]` validates against
`contracts/workbench.schema.json` with zero errors.

### 2. Add an explicit model-egress policy or remove live invocation

The current provider receives raw client/case identifiers, canonical portfolio
language, and evidence identifiers. That is not a bank-safe egress path.

The next agent must choose one of these honest approaches:

**Recommended for this prototype:** keep the model adapter optional but require
an explicit `narrative_policy`/control-envelope projection whenever
`narrative_provider` is supplied. The policy must authorize the purpose,
minimise fields, pseudonymise identifiers, redact sensitive content, and return
the bounded request. No permissive production default should exist.

**Smaller alternative:** remove live provider invocation from this slice and
emit only deterministic specialist findings plus a future controlled-model task
contract. Update docs and tests accordingly.

In either approach, model output needs a stronger semantic structure. The
current validator can reject unknown citations and changed figures, but an
allowed citation can accompany unsupported nonnumeric claims such as fraud
accusations or immediate sell instructions. Prefer claim-level structured
output tied to canonical claim IDs, with fixed allowed task types and no
free-form Advisory Action.

Completion criterion: the provider cannot run without an explicit egress
policy, cannot see unprojected Book data, cannot alter figures/rank, and cannot
publish unsupported claims or autonomous advice.

### 3. Block material data-integrity failures

`_dataset_steward()` in `team.py` currently marks every run completed. A
material issue such as `DQ-TOTALS-DISAGREE` must block outward publication or
follow an explicitly documented safe-partial policy.

Required fix:

- mark the Dataset Steward `blocked` when any issue severity is `material`;
- when any control report is blocked, return no outward Workbench and no
  specialist findings;
- copy the blocking diagnostics to `IntelligenceRun.diagnostics`;
- preserve non-material stale private-market valuations as visible warnings,
  not blockers.

Completion criterion: the mutated-total regression returns `status="blocked"`,
`workbench=None`, zero outward findings, and diagnostic
`DQ-TOTALS-DISAGREE`.

### 4. Strengthen Evidence Auditor ownership checks

The auditor currently checks packet existence and item membership only. It
must also verify:

- every cited packet belongs to the finding's `client_id` and `case_id`;
- every canonical and model-narrative citation belongs to those packets;
- no cross-client packet or item can pass because it exists globally;
- a blocked audit suppresses outward Workbench/findings instead of returning
  them alongside `status="blocked"`.

Completion criterion: every outward finding is client/case-bounded and a
forced ownership mismatch fails closed.

### 5. Make Prioritisation a genuine deep audit

The current specialist mostly copies queue fields into findings. Preserve the
existing deterministic ranking, but independently verify:

- ranks are unique and contiguous;
- every Critical case has an approved Safety Override and every override is
  Critical;
- all override cases precede non-override cases;
- within those groups, scores are descending, with documented tie behavior;
- every factor has a reason and bounded evidence;
- the displayed score follows the configured base-plus-capped-escalation rule;
- Urgency and Confidence remain independent.

The agent explains the result but never changes it.

Completion criterion: the report states which invariants it verified and
blocks when a deliberately corrupted Queue violates one.

### 6. Version the run identity

The current `run_id` hashes only the as-of date and source-file hashes. Add at
least these inputs:

- Intelligence Run schema version;
- engine version;
- adapter ID/version;
- scoring configuration version or file hash;
- specialist-team version;
- prompt/task version when model language is used.

Completion criterion: changing a governed analysis input changes `run_id`;
changing only the generation clock does not.

## Recommended continuation order

1. Read `AGENTS.md`, `CONTEXT.md`, every relevant ADR, and this handoff.
2. Run the focused red suite and confirm the same five failures.
3. Fix nested Workbench serialization and CLI validation.
4. Block material data-integrity failures and suppress blocked outward data.
5. Strengthen Evidence Auditor ownership and fail-closed behavior.
6. Decide and implement the model-egress approach; update its tests and docs.
7. Deepen the Prioritisation audit without changing the ranking engine.
8. Version `run_id` using every governed input.
9. Regenerate `artifacts/intelligence.json` with the fixed timestamp.
10. Run formatting, the focused suite, then the complete engine suite.
11. Inspect `git diff --check` and stage only the files named in this handoff;
    exclude `.pptx-build/` and any teammate-owned UI work.

## Final verification commands

```bash
black --check engine/src/jb_clarity/intelligence \
  engine/src/jb_clarity/cli.py \
  engine/tests/test_intelligence_entrypoint.py
```

```bash
PYTHONPATH=engine/src python -m pytest \
  engine/tests/test_intelligence_entrypoint.py -q
```

```bash
PYTHONPATH=engine/src python -m pytest engine/tests -q
```

```bash
PYTHONPATH=engine/src python -m jb_clarity.cli analyse \
  --data singhacks-jb-wealth-intelligence/data \
  --as-of 2026-08-26 \
  --generated-at 2026-09-05T00:00:00+08:00 \
  --output artifacts/intelligence.json
```

```bash
git diff --check
git status --short
```

## Current working-tree scope

Expected task-owned changes:

```text
M  engine/README.md
M  engine/src/jb_clarity/__init__.py
M  engine/src/jb_clarity/cli.py
?? HANDOFF-MULTI-AGENT-INTELLIGENCE.md
?? artifacts/intelligence.json
?? docs/architecture/multi-agent-intelligence.md
?? engine/src/jb_clarity/intelligence/
?? engine/tests/test_intelligence_entrypoint.py
```

User-owned and out of scope:

```text
?? .pptx-build/
```

The continuation is complete only when the focused and full suites are green,
the embedded Workbench validates against its frozen schema, blocked runs expose
no financial findings, the optional model path is explicitly controlled, and
the regenerated artifact matches the documented interface.
