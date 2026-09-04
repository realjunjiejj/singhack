# Builder 2 — RM Intelligence Workbench and demo experience

## Your mission

Build the **JB Clarity** desktop workbench that lets Priscilla Ong identify whom to call, understand why, inspect the evidence, and approve a Meeting Brief in under 60 seconds.

The product promise is: **Know who to call, why, and how to begin.**

The pitch is: **AI should not replace wealth advice; it should make every RM conversation timely, personal, and defensible.**

Execute the application, tests, and demo flow. Do not stop after producing a mock-up or plan.

## Read before editing

Read these sources in this order:

1. `AGENTS.md`
2. `CONTEXT.md`
3. `.scratch/jb-clarity/spec.md`
4. `contracts/workbench.schema.json`
5. `artifacts/workbench.fixture.json`
6. `.scratch/jb-clarity/infrastructure-state-prototype.html` from branch `prototype/infrastructure-state`
7. Every ADR in `docs/adr/`
8. `singhacks-jb-wealth-intelligence/README.md` for challenge framing

Use the glossary's exact terms in UI copy and tests. This is an RM Intelligence Workbench, not a portfolio dashboard, chatbot, robo-adviser, or autonomous agent.

## Product outcome

The judges must see a direct answer to three questions:

1. Who should Priscilla contact first?
2. Why does that client's situation matter now?
3. How can she begin a grounded, human-led conversation?

The demonstration must combine financial intelligence with relationship memory:

- **Anticipatory Signals** — issues the client may notice soon, such as LTV proximity, tax obligations, redemption gates, mandate breaks, and governance deadlines.
- **Open Loops** — unanswered messages, promises, deferred discussions, and agreed actions that remain unresolved.
- **Meeting Brief** — one preparation surface joining the Client Case, Evidence Chain, Open Loops, Governance Clock, preferred language, questions, and possible actions.

## Ownership and collaboration boundary

You own:

- `web/` — Next.js, TypeScript, UI components, presentation adapters, state, tests, and workbench documentation
- the visual system and responsive desktop behavior
- the in-memory Guided Action, Meeting Brief edit, approval, Open Loop confirmation/deferral, and Case Resolution states
- the target-architecture presentation view

Builder 1 owns `engine/`, compatible evolution of `contracts/workbench.schema.json`, and `artifacts/workbench.json`. Do not alter calculations or raw-data interpretation in the browser.

Begin against the existing `artifacts/workbench.fixture.json` if the generated artifact is not yet available. Keep the fixture behind the same typed adapter used by the real artifact. Switch to `artifacts/workbench.json` as soon as it is available, then remove any contradictory hard-coded facts.

If the schema and interface need to change, coordinate the contract instead of silently forking its meaning.

## Infrastructure you are fitting into

The main integration seam already exists:

1. `contracts/workbench.schema.json` is the only source of truth for data crossing from the intelligence engine into the workbench.
2. `artifacts/workbench.fixture.json` is a partial, schema-shaped Hartono input that lets you build in parallel. Its `artifactKind: "fixture"` means the UI must identify it as development data and must not expect 20 Queue rows.
3. Builder 1 will publish `artifacts/workbench.json` with `artifactKind: "generated"`, all 20 cases, and `schemaVersion: "1.0.0"`.
4. Your boundary adapter validates the schema version and required shape before rendering. If validation fails or the version differs, show the actionable artifact-error state and retain the last compatible source.
5. Financial facts, ordering, factors, source references, allowed Guided Actions, stress scenarios, and cached language come from the artifact. Selection, pane state, filters, brief edits, approvals, Open Loop decisions, and Case Resolution live in your in-memory presentation state.

The runnable state harness at `.scratch/jb-clarity/infrastructure-state-prototype.html` on branch `prototype/infrastructure-state` demonstrates the agreed transitions and rejected shortcuts. Inspect it with `git show prototype/infrastructure-state:.scratch/jb-clarity/infrastructure-state-prototype.html`, or switch to that branch and open it directly in a browser. It is a primary design source, not production UI.

### State invariants to preserve

- A Client Case can be selected only after a compatible Workbench source is loaded.
- Evidence Chain and Meeting Brief surfaces always belong to the active Client Case.
- A Meeting Brief begins as draft and becomes approved only through an explicit RM action.
- Editing an approved brief increments its revision, returns it to draft, clears its approved revision, and invalidates the previous Case Resolution.
- `conversation-prepared` is legal only when the current brief revision is approved.
- Adopting a mismatched artifact is blocked; the UI does not coerce or reinterpret it.

### Your integration checkpoints

- **Checkpoint 1 — typed boundary:** load and validate `artifacts/workbench.fixture.json` through one adapter; no screen imports the JSON directly.
- **Checkpoint 2 — fixture workbench:** the Hartono golden path works from the fixture, including evidence, scenario selection, brief edit, approval, approval invalidation, and resolution.
- **Checkpoint 3 — generated artifact:** switch the adapter input to `artifacts/workbench.json`; render all 20 Queue rows without changing the workflow code.
- **Checkpoint 4 — integrated smoke test:** run the offline golden path and record the schema version and artifact kind shown by the application.

## Technical baseline

- Use Next.js with TypeScript.
- Keep the prototype offline-first and runnable without an API key.
- Read the versioned Workbench JSON through one typed adapter and validate it at the boundary.
- The UI may format, filter, select, compare, and manage temporary interaction state. It must not infer source facts, calculate rankings, or invent evidence.
- Hartono's what-if control selects the deterministic scenarios supplied by Builder 1.
- Use cached validated explanation and translation payloads as the required demonstration path. A live model is optional and must never be required for the demo.
- Provide one documented start command, one test command, and one production build command.

## Information architecture

Use a persistent three-column **Command Centre** at desktop widths:

- **Left — Priority Queue:** whole Book, filters, tiers, Confidence, concise Priority Rationales.
- **Centre — active Client Case:** conclusion, why now, factors, timeline, Anticipatory Signals, Open Loops, and Governance Clock.
- **Right — contextual work surface:** Evidence Chain, Collateral Stress Test, Meeting Brief editor, or Client-Ready View.

The columns express a stable sequence: **choose the conversation → understand the case → prepare the action**. Preserve this sequence even if the narrow-screen presentation becomes stacked or drawer-based.

This layout was selected directly rather than validated through a separate UI prototype. Keep the three regions modular so their proportions can be adjusted after rehearsal without changing behavior.

## Visual direction

The interface should feel like a calm, premium private-client casebook used by a busy RM—not consumer fintech and not a trading terminal.

- Use deep ink/navy for the work surface, paper-white or mineral-gray reading surfaces, and a restrained copper accent for attention or primary action.
- Use color semantically and sparingly. Every status must also have text or iconography; color alone is insufficient.
- Prefer quiet tonal separation, typography, and spacing over heavy borders, gradients, glowing charts, or a grid of generic KPI cards.
- Make the signature element a visible **case thread** connecting signal → evidence → conversation. Repeat that relationship in the Queue rationale, Case timeline, cited evidence, and Meeting Brief.
- Use tabular numerals for financial values and dates.
- Keep source details progressively disclosed. Plain English leads; formulas and source rows remain one action away.
- Use purposeful motion under 300ms only for occasional pane transitions or confirmation. Respect reduced-motion settings.
- Provide visible focus, keyboard navigation, semantic controls, readable contrast, and at least 44px hit targets.

## Required screens and behavior

### Priority Queue

- Show all 20 Client Cases in honest deterministic order from the artifact.
- Clearly separate Critical, High, and Watch tiers.
- Display Urgency score/factors and Confidence separately.
- Show current, near, and historical-resolved status explicitly; never present Hartono's old breach as current.
- Support filters for signal type, booking centre, Urgency, and Confidence.
- Provide quick find or bookmarks for the three deep demo cases without altering their ranks.
- Each row must answer “why now?” in one or two lines and expose its factor contribution breakdown.

### Client Case workspace

- Lead with the client-specific conclusion, not an account balance.
- Show why now, the factor breakdown, selected timeline, Anticipatory Signals, Open Loops, Governance Clock, and Guided Actions.
- Allow comparison between two of the five dataset snapshots.
- Keep fact, interpretation, assumption, and uncertainty visually distinct.
- Every material claim has a visible path to the relevant Evidence Packet item.
- Evidence opens in the right-hand surface without losing the Queue or active case context.
- Source references show the source file and stable record key; formula views show inputs, units, date, and result.
- Evidence Conflicts lower displayed Confidence and remain prominent until reviewed.

### Guided Actions and human control

Offer bounded actions such as:

- Explain this case
- Show evidence
- Prepare conversation
- Request missing information
- Involve a specialist
- Confirm, defer, assign, or dismiss an Open Loop
- Dismiss/defer a Client Case with a reason

Do not provide open chat. Do not execute a trade, order, email, message, or calendar action.

### Meeting Brief

“Prepare conversation” opens an editable RM-facing brief containing:

- what changed and why it matters now;
- evidence citations;
- uncertainties and conflicts;
- relevant Open Loops and Governance Clocks;
- a respectful opening question;
- two or three possible discussion options;
- specialist involvement where relevant.

Draft and approved states must be unmistakable. Approval is an explicit in-memory action. Editing an approved brief returns it to draft. Show the resulting Case Resolution after approval. Label generated or cached language as a draft until the RM approves it.

### Client-Ready View

- Keep the canonical English content beside the client-language version.
- Use the client's `reporting_language` from the artifact.
- Cheung requires Traditional Chinese; Margarethe requires German.
- Quantities, dates, currencies, and evidence identifiers must remain identical between languages.
- Make this a preparation view; it does not send content to a client.

### Target architecture view

Add a concise presentation view showing how the prototype maps to a credible private-bank deployment:

- governed source systems and the Controlled Event Source;
- deterministic analytics and Evidence Packet construction;
- optional bounded language generation;
- RM review and approval;
- target identity, entitlements, encryption, audit trail, model gateway, and deployment boundary.

Clearly label which controls are demonstrated and which are target architecture. Do not claim production security is implemented.

## Required demo cases

Render facts from the Workbench artifact; do not duplicate financial calculations in UI constants.

### Hartono — primary live walkthrough

The judge-facing path must show:

1. Hartono's position in the Priority Queue and visible Priority Rationale.
2. The distinction between the 2025-12-31 and 2026-02-27 LTV breaches and the current resolved status.
3. The Evidence Chain showing that unchanged SGD 8m borrowing and a higher lending value from the collateral portfolio produced the cure.
4. Direct energy concentration plus the energy-linked FCN look-through, with limitations.
5. The SGD 9m 2027 property need and the family/political constraint on selling the legacy stake.
6. A bounded collateral what-if selector, explicitly labelled as a calculation rather than a forecast.
7. An editable Meeting Brief, explicit approval, and Case Resolution.

### Cheung

Show the bond/duration explanation, retirement-income objective, USD 1.1m versus USD 1.28m evidence conflict, increased medical spending, refusal to sell at a loss, 2045 maturity, and Traditional Chinese Client-Ready View. Keep the explanation respectful and avoid making a life-expectancy prediction.

### Margarethe

Show the Conservative-profile mismatch, inherited equity exposure, confirmed EUR 3.4m inheritance-tax need, sensitive widowhood context, material disagreement between portfolio and holding/client totals, reduced Confidence, and German Client-Ready View.

### Supporting Book stories

Ensure the Queue also makes these inspectable:

- `CL-0006` gated redemption and near-term USD tuition/capital calls;
- `CL-0004` unanswered “move everything to deposits?” question;
- `CL-0011` fourth deferred succession discussion and due-soon KYC;
- `CL-0009` repeatedly agreed but unexecuted deployment;
- facilities trending toward margin-call triggers;
- applicable mandate-band breaks.

## Demo sequence

Optimize for this short presentation order:

1. In one sentence, establish Priscilla's problem: critical financial signals and relationship commitments are fragmented across the Book.
2. Show the Priority Queue and explain deterministic Urgency versus separate Confidence.
3. Walk Hartono from rationale → history → evidence → stress scenario → Meeting Brief approval.
4. Use Cheung to demonstrate client-specific explanation and Traditional Chinese preparation.
5. Use Margarethe to demonstrate suitability mismatch, urgent tax need, sensitive context, and honest data conflict.
6. Show target architecture/governance.
7. End on strategic impact: more timely, personal, defensible RM conversations.

Do not spend the demo leading with architecture, model novelty, or a generic dashboard tour. The client problem and RM decision come first.

## States and resilience

Implement polished states for:

- initial load;
- schema or artifact error with actionable wording;
- no filter results;
- low Confidence / Evidence Conflict;
- selected and unselected case;
- draft, edited, approved, and approval-invalidated Meeting Brief;
- cached/offline language mode;
- unavailable optional live language mode.

The app must remain fully demonstrable with network access disabled and no model credentials.

## Tests and verification

Test external behavior rather than component internals or incidental markup:

- artifact boundary validation and actionable failure state;
- Queue renders all 20 cases in artifact order;
- Urgency and Confidence remain separate;
- filters and quick find do not alter ranking;
- Hartono golden path from Queue to evidence, what-if selection, Meeting Brief edit, approval, and Case Resolution;
- historical breach is never labelled current;
- Evidence Conflict display for Margarethe;
- bilingual side-by-side views preserve figures and evidence identifiers;
- cached language works without network or credentials;
- keyboard access, focus visibility, semantic labels, non-color status cues, and readable financial formatting;
- production build and a clean-start smoke test.

Visually verify the core flow at a typical presentation laptop width and at one narrower width. Fix overflow, truncated financial values, hidden evidence controls, and unreadable bilingual layouts before handoff.

## Out of scope

- raw-data analytics or ranking logic in the browser;
- autonomous investment advice, trading, orders, or outreach;
- open-ended chat;
- live market data or news;
- production authentication, permissions, integrations, or compliance approval;
- definitive tax, legal, or suitability advice;
- automatic resolution of evidence conflicts;
- a generic scenario engine;
- mobile client application;
- persistent or multi-user workflow.

## Definition of done

Your work is complete when:

- the app starts from a clean checkout using the documented command and consumes the schema-valid generated artifact;
- a non-developer can complete the Hartono walkthrough in under 60 seconds;
- Cheung and Margarethe demonstrate bilingual preparation and honest uncertainty;
- the Queue exposes financial signals, Open Loops, and Governance Clocks across the Book;
- every material claim can open its Evidence Chain;
- Meeting Brief editing, approval, and Case Resolution are visibly human-controlled;
- the demo works offline without AI credentials;
- relevant tests and production build pass;
- you leave a concise handoff stating commands run, test/build results, screenshots checked, remaining uncertainties, and any contract coordination needed from Builder 1.
