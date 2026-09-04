# Builder 2 — RM Intelligence Workbench and Winning Demo

## Assignment

Build the complete **JB Clarity** desktop workbench. Priscilla Ong must be able to identify whom to call, understand why, inspect the evidence, and approve a Meeting Brief in under 60 seconds.

This is an execution brief. Implement the application, interaction state, tests, and demo path. Do not stop at wireframes or a plan.

**Promise:** Know who to call, why, and how to begin.

**Thesis:** AI should not replace wealth advice; it should make every RM conversation timely, personal, and defensible.

The judges must immediately understand:

1. who Priscilla should contact first;
2. why that client’s situation matters now;
3. how financial signals and relationship memory connect;
4. what evidence and uncertainty sit behind the conclusion;
5. how the RM—not AI—controls the next conversation.

## Why this wins

| Judging dimension | What the interface must prove |
|---|---|
| Client-centric innovation | Show personal objectives, obligations, sensitivities, and unfinished relationship threads—not generic alerts. |
| User experience | Complete Queue → Case → Evidence → Meeting Brief in under 60 seconds with plain language first. |
| Feasibility | Make deterministic evidence, confidence, source traceability, human approval, offline mode, and target-bank controls visible. |
| Strategic impact | Show a repeatable whole-Book workflow that strengthens the RM relationship rather than replacing it. |

Do not lead with a dashboard tour or architecture diagram. Lead with Priscilla’s attention problem and a client story.

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
9. `git show prototype/infrastructure-state:.scratch/jb-clarity/infrastructure-state-prototype.html`

Use the exact terms in `CONTEXT.md`. This is an RM Intelligence Workbench, not a chatbot, robo-adviser, trading terminal, or generic portfolio dashboard.

## Ownership and fixed decisions

You own `web/`: Next.js/TypeScript application, visual system, artifact adapter, presentation state, components, tests, accessibility, and demo documentation. Builder 1 owns `engine/`, schema evolution, financial calculations, queue order, facts, citations, stress scenarios, and `artifacts/workbench.json`.

The browser may format, filter, select, compare, and maintain temporary RM state. It must not calculate financial facts, change rank, infer missing evidence, translate figures independently, or read raw CSV files.

- Build against `artifacts/workbench.fixture.json` immediately.
- Switch to generated `artifacts/workbench.json` through the same adapter when available.
- Fixture mode is visibly marked development data and may contain only Hartono.
- Schema mismatch blocks adoption and retains the last compatible artifact.
- All core behavior works without network or AI credentials.
- No trade, order, email, message, calendar action, open chat, or persistent workflow is implemented.

## Required technical shape

Use current stable Next.js App Router, TypeScript strict mode, React, Ajv for JSON Schema validation, Vitest + Testing Library, and Playwright for the golden path. Use npm. Prefer CSS Modules or a small token stylesheet over a large component framework. Build charts with accessible HTML/SVG/CSS unless a dependency clearly saves time.

Create:

```text
web/
  package.json
  README.md
  next.config.ts
  tsconfig.json
  public/data/workbench.json
  scripts/sync-workbench.mjs
  src/app/{layout,page,globals.css}.tsx
  src/app/architecture/page.tsx
  src/lib/workbench/{types,schema,adapter,format,selectors}.ts
  src/lib/state/{model,reducer,selectors}.ts
  src/components/layout/CommandCentre.tsx
  src/components/queue/{PriorityQueue,QueueFilters,QueueItem,FactorBreakdown}.tsx
  src/components/case/{ClientCasePanel,CaseHeader,SignalList,OpenLoops,GovernanceClocks,SnapshotComparison}.tsx
  src/components/work-surface/{WorkSurface,EvidenceChain,StressTest,MeetingBrief,ClientReadyView}.tsx
  src/components/common/{StatusBadge,ConfidenceBadge,CitationLink,EmptyState,ErrorState}.tsx
  src/components/architecture/TargetArchitecture.tsx
  src/styles/tokens.css
  src/tests/
  e2e/hartono-golden-path.spec.ts
```

`sync-workbench.mjs` must select `../artifacts/workbench.json` when present and valid, otherwise the fixture; copy it to `public/data/workbench.json`; print source path, schema version, and artifact kind. It must never convert or repair incompatible data.

Required commands:

```bash
cd web
npm install
npm run sync-data
npm run dev
npm test
npm run test:e2e
npm run build
```

Document exact clean-checkout and offline-demo commands in `web/README.md`.

## State model—implement before styling

Use one reducer with this conceptual state:

```ts
type WorkbenchState = {
  source: { status: 'loading' | 'ready' | 'error'; artifactKind?: 'fixture' | 'generated'; schemaVersion?: string; error?: string }
  activeCaseId: string | null
  filters: { query: string; signalTypes: string[]; bookingCentres: string[]; urgencyTiers: string[]; confidenceLevels: string[] }
  rightSurface: 'none' | 'evidence' | 'stress-test' | 'meeting-brief' | 'client-ready'
  activeEvidenceItemId: string | null
  selectedSnapshots: [string, string]
  selectedStressScenarioId: string | null
  openLoopStates: Record<string, { state: 'candidate' | 'confirmed' | 'deferred' | 'assigned' | 'dismissed'; note?: string }>
  meetingBriefs: Record<string, { revision: number; status: 'draft' | 'approved'; approvedRevision: number | null; fields: EditableBrief }>
  caseResolutions: Record<string, { state: 'unresolved' | 'conversation-prepared' | 'information-requested' | 'specialist-involved' | 'dismissed'; reason?: string; briefRevision?: number }>
}
```

Required invariants:

- A case can be selected only after a compatible artifact loads.
- Right-surface content always belongs to the active case.
- Financial facts remain immutable.
- Meeting Brief starts at revision 1, draft.
- Explicit approval stores the current approved revision.
- Editing an approved brief increments revision, returns to draft, clears approval, and invalidates `conversation-prepared`.
- `conversation-prepared` is legal only for the currently approved revision.
- Open Loop decisions affect presentation state, never source evidence.
- Filters never reorder rows; they only hide/show the artifact’s stable order.
- Quick access to demo clients selects or finds them without ranking changes.
- A mismatched artifact is rejected rather than coerced.

Write reducer tests before integrating screens. The prototype branch is the reference behavior.

## Build sequence and completion gates

### 1. Application and typed boundary

Scaffold the app, define tokens, implement the data-sync command, hand-write or safely generate TypeScript types from the repository schema, validate with Ajv at the boundary, and expose one adapter API. No component imports JSON directly.

The error state must say what failed, expected schema version, received version when known, and how to regenerate/sync the artifact. In fixture mode show a quiet “Demo fixture · partial Book” label.

**Gate:** fixture loads through the adapter; malformed shape and wrong version show actionable errors; components receive typed data only.

### 2. Command Centre shell

Build a persistent desktop three-column layout:

- **Left, 300–340px:** Priority Queue.
- **Centre, min 440px:** active Client Case.
- **Right, 380–460px:** contextual work surface.

At typical presentation widths around 1440px, all three remain visible. At narrower laptop widths, the right surface may overlay as a drawer while Queue and Case remain usable. Below tablet width, stack deliberately; mobile optimization is not required.

Top bar: JB Clarity identity, as-of date, RM name, artifact status, and architecture link. Do not fill it with generic KPIs.

**Gate:** selection and surfaces work with fixture data, no horizontal overflow at 1440×900 and 1280×800, and regions retain the sequence choose → understand → prepare.

### 3. Priority Queue

Each row shows, in this order:

1. rank and client;
2. Critical/High/Watch Urgency with score;
3. one- or two-line Priority Rationale;
4. current state text such as Active, Near trigger, or Historical—resolved;
5. signal/Open Loop/Governance summaries;
6. Confidence as a separate badge/value;
7. expandable factor contributions with points and reasons.

Group visually by tier without altering rank. Implement query, signal type, booking centre, Urgency, and Confidence filters from artifact-provided values. Add quick-find chips/bookmarks for Hartono, Cheung, and Margarethe; label them “Demo cases,” not “Top clients.”

Never let high Confidence make a case look more urgent. Never display Hartono’s old breach as current.

**Gate:** generated artifact displays all 20 rows in artifact order; filtering and quick find preserve rank; keyboard selection works.

### 4. Client Case centre panel

Lead with the conclusion and “Why now,” not AUM. Then show:

- explicit current/historical status;
- Urgency and separate Confidence reasons;
- visible factor contribution bar/list;
- Anticipatory Signals;
- Open Loops with source date and candidate status;
- Governance Clocks with calculated wording;
- five-snapshot timeline/comparison;
- bounded Guided Actions from `allowedGuidedActions`.

Visually distinguish Fact, Interpretation, Assumption, Uncertainty, and Conflict. Every material claim has a citation control opening the relevant Evidence Chain without changing case selection.

Snapshot comparison lets the RM choose two available dates and shows supplied/precomputed metrics only. It does not calculate return attribution in the browser.

**Gate:** a user understands the case summary before expanding evidence; every displayed claim resolves to an artifact evidence ID.

### 5. Evidence Chain surface

Show a progressive path:

```text
source record → exact value → derived metric/formula → interpretation → advisory significance
```

For each evidence item show label, value, file, record key, and field. For derived metrics show formula, inputs, unit, snapshot date, and unrounded result with an appropriately rounded display value. Conflicts show both values/sources and explain their impact on Confidence.

Clicking a citation focuses the matching item. The Queue and case context stay visible. Offer a “Back to claim” affordance and do not expose filesystem paths or pretend source rows are live bank links.

**Gate:** Hartono’s LTV Evidence Chain visibly uses lending value and SGD; Margarethe’s evidence shows that the EUR-base and USD totals reconcile after applying the supplied FX rate.

### 6. Anticipatory Signals, Open Loops, and Governance

These are one joined Client Case, not three disconnected products.

- Signals show time horizon, status, summary, and evidence.
- Open Loops show excerpt/date/why-open/Confidence and actions to confirm, defer, assign, or dismiss.
- Require a small reason/note for dismissal or deferral.
- Governance Clocks show due date, days remaining, and due-soon/today/overdue/future.
- Never mutate the artifact; store decisions in reducer state.

Use the relationship framing: **“Your client is about to notice this”** for approaching financial issues, and **“The threads at risk of being dropped”** for Open Loops. Keep copy professional and avoid alarmist notification language.

**Gate:** CL-0004 unanswered deposit question, CL-0011 succession/KYC, CL-0009 unexecuted deployment, and CL-0006 liquidity/gate are inspectable from generated data.

### 7. Hartono stress test

Render only artifact-supplied scenarios. Use a selector, not a free-form numeric engine. Show:

- assumption/change in collateral;
- collateral market value;
- lending value;
- unchanged drawn amount;
- calculated LTV;
- 70% trigger;
- percentage-point distance;
- state.

Label the surface **Illustrative collateral what-if — not a forecast**. Do not imply the scenario probability or recommend a trade.

**Gate:** base and 15%-down scenarios render; the UI contains no LTV formula implementation or recalculation.

### 8. Meeting Brief and Case Resolution

“Prepare conversation” opens an editable RM brief containing:

- what changed;
- why it matters now;
- factual evidence citations;
- uncertainties/conflicts;
- Open Loops and Governance Clocks;
- respectful opening question;
- two or three discussion options;
- specialist suggestion;
- approved Guided Actions only.

Show a visible status header: Draft, Edited draft, or Approved revision N. Provide Edit, Reset to source seed, Approve, and Mark conversation prepared. Approval is never implicit. Editing after approval invalidates it and any prepared resolution. Dismissal requires a reason. No button sends content.

Adapt the content organization and no-send/human-review guardrails from Anthropic’s Meeting Prep Agent as recorded in `docs/research/open-source-leverage.md`; preserve JB Clarity terminology and attribution rules.

**Gate:** reducer and browser tests cover prepare → edit → approve → resolve and approve → edit → invalidated resolution.

### 9. Client-Ready View

Show canonical English beside the client’s reporting-language draft. Cheung uses Traditional Chinese; Margarethe uses German. The view must:

- preserve every quantity, date, currency, and evidence ID;
- label both versions as drafts until RM approval;
- show cached/offline mode;
- let the RM compare content without sending it;
- remain readable with different text lengths.

Do not use browser translation or independently regenerate text. Render artifact payloads.

**Gate:** automated tests compare visible financial tokens/citations across versions and the layout is visually checked.

### 10. Target architecture

Create a concise presentation route that maps prototype to a credible private-bank system:

```text
governed bank sources + Controlled Event Source
  → deterministic analytics and evidence packets
  → optional bounded language gateway
  → RM review and approval
  → existing advisory channels
```

Clearly distinguish:

- **Demonstrated:** offline ingestion artifact, deterministic factors, citations, cached multilingual drafts, human approval.
- **Target controls:** identity, entitlements, encryption, secrets, audit persistence, model gateway, data residency, monitoring, deployment segregation, and bank integrations.

Do not claim target controls are implemented.

**Gate:** architecture can be explained in under 30 seconds and supports rather than interrupts the client story.

## Visual system

The interface should feel like a calm private-client casebook used by a busy RM.

- Deep ink/navy work surfaces; paper white/mineral gray reading surfaces; restrained copper accent.
- Urgency colors are semantic and always paired with text/icon.
- Use typography, spacing, and tonal surfaces before borders.
- Use tabular numerals for money, percentages, ranks, and dates.
- Make the signature visual a repeated case thread connecting Signal → Evidence → Conversation.
- Plain English first; formulas/source rows one action away.
- Avoid generic KPI-card grids, neon gradients, market tickers, glass effects, decorative charts, and chat bubbles.
- Use purposeful transitions under 300ms and respect reduced motion.
- Visible focus, semantic controls, meaningful headings, keyboard navigation, readable contrast, and 44px targets are required.

## Deep demo cases

### Hartono `CL-0001` — primary live walkthrough

Display only artifact values. The path must show:

1. honest Queue rank and rationale;
2. SGD facility and historical 78.50%/75.68% breaches against 70%;
3. current resolved state around 59.15%;
4. unchanged SGD 8m borrowing plus higher lending value as the cure;
5. direct energy/coal and energy FCN look-through with limitations;
6. SGD 9m 2027 property need and family/political selling constraint;
7. bounded scenario selector labelled not a forecast;
8. editable brief, explicit approval, and Case Resolution.

### Cheung `CL-0012`

Show bond/duration explanation, retired Income objective, USD 1.1m versus USD 1.28m conflict, increased medical costs, refusal to sell at a loss, 2045 maturity, and Traditional Chinese side-by-side draft. Use respectful language and no life-expectancy prediction.

### Margarethe `CL-0003`

Show Conservative profile versus inherited equity exposure, EUR 3.4m inheritance-tax need, widowhood/unfamiliarity as sensitive context, the honest EUR 20.31m-to-USD 22.18m FX reconciliation, and a German side-by-side draft.

## Supporting Book proof

Ensure generated data makes these discoverable:

- `CL-0006`: gated redemption and near-term USD tuition/capital calls against SGD assets;
- `CL-0004`: unanswered “move everything to deposits?” message;
- `CL-0011`: fourth succession attempt and KYC due soon;
- `CL-0009`: repeated agreement with no deployment;
- every near-trigger facility;
- every applicable mandate-band break.

## Judge-facing demo script

Optimize the product for this 4–5 minute sequence:

1. **Problem, 15 seconds:** “Priscilla already has portfolio reports. What she lacks is one place that tells her which client conversation matters now and remembers both the financial risk and the human context.”
2. **Queue, 30 seconds:** Show the full Book and explain deterministic Urgency versus separate Confidence.
3. **Hartono, 90 seconds:** Queue rationale → breach timeline → Evidence Chain → hidden concentration/property constraint → scenario → approve brief.
4. **Cheung, 45 seconds:** Explain the bond loss in his retirement context; reveal the cash-draw conflict and Traditional Chinese preparation.
5. **Margarethe, 45 seconds:** Reveal suitability mismatch, tax clock, sensitive context, and the correctly reconciled cross-currency totals.
6. **Architecture, 25 seconds:** Show deterministic core, bounded language, RM approval, and target controls.
7. **Close, 10 seconds:** “JB Clarity helps every RM conversation become more timely, personal, and defensible.”

Rehearse until the Hartono path is under 60 seconds without narration stalls.

## Open-source leverage policy

Follow `docs/research/open-source-leverage.md`.

- Inspect Advisor Desktop’s `NBAFeed`, `NBACard`, service/hook boundary, and `MeetingPrepModal` for interaction patterns.
- Re-implement only small useful patterns against our Workbench adapter; keep our domain model and three-column Command Centre.
- Adapt Anthropic’s Meeting Prep checklist and human-review/no-send guardrails.
- Do not inherit composite confidence ranking, open chat, batch contact, trading, autonomous rules, or mock domain semantics.
- Do not copy AGPL Ghostfolio/Wealthfolio code or BSL Navam code.
- If MIT/Apache code or text is materially copied, record repository, commit SHA, files, modifications, and notices in `THIRD_PARTY_NOTICES.md`.

## Required states

Implement and polish: loading; compatible fixture; compatible generated artifact; schema/version error; no filter results; no case selected; active/near/historical-resolved/normal; low Confidence; Evidence Conflict; right surface closed/open; Open Loop candidate/confirmed/deferred/assigned/dismissed; Meeting Brief draft/edited/approved/invalidated; resolved/unresolved case; cached language; unavailable optional live language.

## Verification matrix

| Area | Observable requirement |
|---|---|
| Boundary | Valid fixture/generated artifacts load through one adapter; incompatible input fails visibly. |
| Queue | 20 rows in artifact order; filters and quick find never rerank. |
| Semantics | Urgency and Confidence remain separate; current/historical wording is correct. |
| Evidence | Every citation opens the correct item/source/formula without losing context. |
| Hartono | Complete queue-to-approved-brief golden path and scenario selector. |
| State | Editing approved brief increments revision and invalidates resolution. |
| Reconciliation | Margarethe displays both currency-denominated totals, the applied FX explanation, and no fabricated conflict. |
| Language | Chinese/German views preserve all financial tokens and citations. |
| Accessibility | Keyboard path, focus, semantic labels, non-color cues, contrast, reduced motion. |
| Responsive | Visual check at 1440×900 and 1280×800 plus one narrower width. |
| Offline | Core demo works with network disabled and no AI key. |
| Build | Unit/integration tests, Playwright golden path, and production build pass. |

Test behavior rather than component internals or incidental markup. Capture screenshots of Queue, Hartono Evidence Chain, approved Meeting Brief, Cheung bilingual view, Margarethe reconciliation, and architecture for rehearsal review.

## Builder 1 integration protocol

- Consume only the Workbench contract.
- Share exact requested optional fields rather than implementing UI-side approximations.
- On each artifact adoption, record source path, kind, schema version, and quality status.
- Remove fixture-only assumptions once generated data arrives.
- If a field meaning differs, block integration and coordinate; never silently reinterpret it.
- Report any claim without an evidence target to Builder 1 as a contract defect.

## Definition of done

- Clean checkout starts with documented commands.
- Generated artifact displays the 20-client Queue.
- A non-developer completes Hartono’s path in under 60 seconds.
- Cheung and Margarethe prove multilingual preparation and honest uncertainty.
- Signals, Open Loops, and Governance Clocks appear as one case workflow.
- Every important claim opens an Evidence Chain.
- Meeting Brief approval and Case Resolution remain visibly human-controlled.
- The demo works offline without credentials.
- Tests, Playwright golden path, and production build pass.
- Screens have been visually inspected at presentation sizes.
- Handoff records commands, results, screenshots, remaining uncertainties, contract requests, and attribution.

The workbench succeeds when judges stop seeing a portfolio dashboard and start seeing a better private-banking conversation.
