# Builder 2 handoff — RM Intelligence Workbench

**Branch:** `builder-2/rm-workbench`  
**Verification date:** 2026-09-04  
**Artifact adopted:** `artifacts/workbench.fixture.json`  
**Artifact kind:** `fixture`  
**Schema version:** `1.0.0`  
**Data-quality status:** `clear`

## Delivered

- Strict Next.js/TypeScript App Router workbench with the persistent Priority Queue, active Client Case, and contextual work surface.
- One Ajv-validated adapter boundary with schema-version and cross-reference checks. Components do not import artifacts directly.
- Stable-order Queue search and artifact-provided filters, tier grouping, separate Urgency and Confidence, keyboard-native selection, factor contributions, and Demo cases access.
- Client Case composition for conclusions, why-now framing, typed claims, Anticipatory Signals, Open Loops, Governance Clocks, snapshot comparison, and bounded Guided Actions.
- Evidence Chain with source record, exact value, derived formula/inputs/result, interpretations, assumptions, uncertainties, and Evidence Conflicts.
- Artifact-only Collateral Stress Test selector with no browser formula or scenario generation.
- Reducer-controlled Open Loop decisions, editable Meeting Brief revisions, explicit approval, and Case Resolution invalidation.
- Cached/offline Client-Ready View with canonical and reporting-language drafts side by side.
- Demonstrated-versus-target private-bank architecture route.
- Loading, empty, fixture, generated, version/shape error, closed/open surface, draft/approved/invalidated, and optional-language-unavailable states.

## Verification evidence

Run from `web/`:

| Command | Result |
| --- | --- |
| `npm run sync-data` | Pass — fixture selected, schema `1.0.0`, kind `fixture` |
| `npx tsc --noEmit` | Pass |
| `npm test` | Pass — 6 files, 21 tests |
| `npm run test:e2e` | Pass — 3 Playwright tests |
| `npm run build` | Pass — `/` and `/architecture` statically generated |
| `npm audit --omit=dev --audit-level=high` | Pass — 0 vulnerabilities |

The Playwright suite verifies the Hartono Queue → Evidence Chain → supplied 15%-down scenario → edited Meeting Brief → approval → conversation-prepared path, followed by edit invalidation. It also verifies no page-level horizontal overflow at 1440×900, 1280×800, and 1000×800.

## Rehearsal screenshots

- `demo/screenshots/01-priority-queue.png`
- `demo/screenshots/02-hartono-evidence.png`
- `demo/screenshots/03-approved-meeting-brief.png`
- `demo/screenshots/04-responsive-1280.png`
- `demo/screenshots/05-responsive-1000-drawer.png`
- `demo/screenshots/06-target-architecture.png`

All six were visually inspected. At 1440px and 1280px the three regions remain visible. At 1000px the work surface becomes a contained right-side drawer while the Queue remains usable.

## Remaining integration evidence

Builder 1 has not published `artifacts/workbench.json` locally or on any current remote branch. Consequently, these final data-dependent checks remain pending and must not be represented as passed:

- rendering the actual 20-row generated Priority Queue;
- live inspection of Cheung, Margarethe, CL-0004, CL-0006, CL-0009, and CL-0011;
- real Traditional Chinese/German token parity against generated drafts (the generic behavior is covered by an automated bilingual test);
- Margarethe’s real two-source conflict screenshot;
- Cheung and Margarethe rehearsal screenshots;
- a timed non-developer Hartono rehearsal under 60 seconds.

No fixture-only case logic is embedded in the components. When Builder 1 publishes a compatible artifact, `npm run sync-data` will adopt it through the same adapter. Missing Evidence Packets, foreign packets, or unresolved citation IDs are treated as contract defects and block adoption.

## Attribution

Advisor Desktop was inspected for compact-card, expandable-detail, filtering, and presentation/service-boundary patterns. Anthropic Financial Services was inspected for Meeting Brief staging and no-send/human-review guardrails. This implementation is original; no third-party source code or text was materially copied, so `THIRD_PARTY_NOTICES.md` is not required.

## Repository process limitation

The `gh` CLI is not installed in this environment, so no GitHub Issue could be read, claimed, commented on, or closed. The local finalized specification and Builder 2 brief were used as the authoritative sources available here.
