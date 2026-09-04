# Open-source leverage for JB Clarity

**Research date:** 2026-09-04  
**Decision:** Borrow three narrow patterns, not an application or portfolio engine.

## Executive recommendation

Use these sources now:

1. **Advisor Desktop** for selected React presentation patterns around a prioritised action feed, filtering, case cards, and meeting preparation.
2. **AI WealthPilot** for its offline golden-fixture pattern and its separation of computational core, transport schema, and web presentation.
3. **Anthropic Financial Services' Meeting Prep Agent** as a prompt/content checklist for the Meeting Brief: relationship history, holdings, open items, relevant context, suggested agenda, draft-only staging, and no client-facing send.

Do **not** adopt a whole repository. JB Clarity already has the correct challenge-specific architecture: deterministic Python analytics produce `contracts/workbench.schema.json`; the Next.js workbench renders that artifact; optional language generation receives a bounded Evidence Packet. Replacing that architecture would consume hackathon time and weaken the product's strongest differentiator.

Defer Riskfolio-Lib unless the core demonstration is complete. Treat Ghostfolio and Wealthfolio as conceptual references only because they are AGPL-3.0 and solve a transaction-ledger problem that the supplied five-snapshot dataset does not. Do not copy Navam Invest before legal review: its actual license is Business Source License 1.1, not MIT. Do not use the Financial Machine Learning project for Queue ranking: the available dataset cannot train or validate such a model, and learned ranking would contradict JB Clarity's deterministic, visible Priority Rationale.

## Identity, license, and maintenance check

“Last push” is a maintenance signal from GitHub metadata, not proof of quality, security, or production readiness. Repository age and adoption matter here because several projects are very new.

| Name supplied | Resolved repository | Identity confidence | License verified from repository | Last pushed at research date | Assessment |
|---|---|---:|---|---:|---|
| Advisor Desktop | [`JoelLewis/advisor-desktop`](https://github.com/JoelLewis/advisor-desktop) | Exact | [MIT](https://github.com/JoelLewis/advisor-desktop/blob/main/LICENSE) | 2026-07-12 ([metadata](https://api.github.com/repos/JoelLewis/advisor-desktop)) | Recent but very young and lightly adopted; inspect rather than trust wholesale. |
| AI WealthPilot | [`Michelia-L/AI-WealthPilot`](https://github.com/Michelia-L/AI-WealthPilot) | Exact | [MIT](https://github.com/Michelia-L/AI-WealthPilot/blob/main/LICENSE) | 2026-09-03 ([metadata](https://api.github.com/repos/Michelia-L/AI-WealthPilot)) | Actively changing and very young; useful patterns, not a stable platform dependency. |
| Ghostfolio | [`ghostfolio/ghostfolio`](https://github.com/ghostfolio/ghostfolio) | Exact | [AGPL-3.0](https://github.com/ghostfolio/ghostfolio/blob/main/LICENSE) | 2026-09-03 ([metadata](https://api.github.com/repos/ghostfolio/ghostfolio)) | Mature and active, but license and architecture make direct reuse unattractive here. |
| Wealthfolio | [`wealthfolio/wealthfolio`](https://github.com/wealthfolio/wealthfolio) | Exact; the older `afadil/wealthfolio` location was transferred | [AGPL-3.0](https://github.com/wealthfolio/wealthfolio/blob/main/LICENSE) | 2026-09-04 ([metadata](https://api.github.com/repos/wealthfolio/wealthfolio)) | Active and well adopted, but direct copying creates AGPL obligations. |
| Navam Invest | [`navam-io/navam-invest`](https://github.com/navam-io/navam-invest) | Exact | [Business Source License 1.1](https://github.com/navam-io/navam-invest/blob/main/LICENSE), converting to Apache-2.0 on 2028-10-24 | 2025-10-24 ([metadata](https://api.github.com/repos/navam-io/navam-invest)) | Source-available, not conventionally open source; commercial use is restricted before its change date. |
| “Financial Machine Learning” | [`Jackirn/Fintech`](https://github.com/Jackirn/Fintech) is the probable match | **Probable, not exact**: the repository title differs, but its README contains the described client segmentation, NBA, suitability, and SHAP work | [MIT](https://github.com/Jackirn/Fintech/blob/main/LICENSE) | 2026-06-05 ([metadata](https://api.github.com/repos/Jackirn/Fintech)) | Research/course repository, not a reusable product service. Confirm the URL with the original recommender before copying. |
| Riskfolio-Lib | [`dcajasn/Riskfolio-Lib`](https://github.com/dcajasn/Riskfolio-Lib) | Exact | [BSD-3-Clause](https://github.com/dcajasn/Riskfolio-Lib/blob/master/LICENSE.txt) | 2026-08-18 ([metadata](https://api.github.com/repos/dcajasn/Riskfolio-Lib)) | Mature, active quantitative library; technically credible but outside the minimum winning slice. |
| Optional bonus: Anthropic Financial Services | [`anthropics/financial-services`](https://github.com/anthropics/financial-services) | Exact | [Apache-2.0](https://github.com/anthropics/financial-services/blob/main/LICENSE) | 2026-08-25 ([metadata](https://api.github.com/repos/anthropics/financial-services)) | High-value first-party workflow reference; adapt the Meeting Prep guardrails, not its external connectors. |

### License implications

- MIT sources permit reuse, modification, and distribution, but their copyright and permission notice must accompany copies or substantial portions.
- BSD-3-Clause similarly requires the copyright notice, conditions, and disclaimer and prohibits implied endorsement.
- AGPL-3.0 is strong copyleft with network-use provisions. Copying Ghostfolio or Wealthfolio code into a hosted JB Clarity derivative may require offering corresponding source under AGPL terms. This report is not legal advice; the low-risk hackathon choice is not to copy their code.
- Navam's BSL grants no-charge non-production, personal, internal-evaluation, and educational use, but requires a separate license for commercial use until the stated change date. A sponsored hackathon prototype may be educational, but its downstream use is uncertain, so avoid incorporating the code.
- Apache-2.0 permits adaptation subject to its license, notice, change-marking, and patent terms.

If MIT, BSD, or Apache source is copied, record the source repository, commit SHA, files, modifications, and required notices in a `THIRD_PARTY_NOTICES.md` file. Ideas and independently written code do not require copying an implementation.

## Repository-by-repository findings

### 1. Advisor Desktop — borrow UI seams now

**Verified facts.** The project is a client-side React 18/TypeScript/Vite application using MSW for mock APIs, Zustand for UI state, TanStack Query for server state, and a feature-oriented `src/` layout. Its README describes 20+ pages, an AI-prioritised next-best-action feed, meeting preparation, compliance workflows, client views, and a self-guided demo ([README](https://github.com/JoelLewis/advisor-desktop/blob/main/README.md)). Its concrete seams include:

- [`src/types/nba.ts`](https://github.com/JoelLewis/advisor-desktop/blob/main/src/types/nba.ts): the action/card domain shape, trigger signal, compliance status, and audit-entry vocabulary;
- [`src/features/dashboard/NBAFeed.tsx`](https://github.com/JoelLewis/advisor-desktop/blob/main/src/features/dashboard/NBAFeed.tsx): filtering, stable feed rendering, action routing, dismiss-reason flow, and grouped actions;
- [`src/components/ui/NBACard.tsx`](https://github.com/JoelLewis/advisor-desktop/blob/main/src/components/ui/NBACard.tsx): compact prioritised-case card presentation;
- [`src/features/dashboard/MeetingPrepModal.tsx`](https://github.com/JoelLewis/advisor-desktop/blob/main/src/features/dashboard/MeetingPrepModal.tsx): structured meeting-prep sections and editable notes;
- [`src/services/nba.ts`](https://github.com/JoelLewis/advisor-desktop/blob/main/src/services/nba.ts), [`src/hooks/use-nbas.ts`](https://github.com/JoelLewis/advisor-desktop/blob/main/src/hooks/use-nbas.ts), and [`src/mocks/handlers/nba.ts`](https://github.com/JoelLewis/advisor-desktop/blob/main/src/mocks/handlers/nba.ts): a presentation-to-service seam that keeps mock transport out of screens.

**JB Clarity fit (inference).** Builder 2 can port small visual/interaction patterns into Next.js, but must bind them to the existing Workbench adapter instead of adopting the mock API or domain model. This can save time on Queue ergonomics and meeting-prep affordances.

**Do not copy these semantics.** Advisor Desktop mixes `confidence` into a composite NBA score; JB Clarity deliberately keeps Urgency and Confidence independent. It also includes open chat, batch contact, trade execution, and autonomous standing rules, all outside the approved human-in-the-loop scope. Preserve JB Clarity's Client Case terminology, deterministic ordering, Evidence Chain, explicit brief approval, and no-send/no-trade boundary.

**Decision: BORROW SELECTIVELY.** Use it as a component-level reference. Do not fork the application or replace the chosen three-column Command Centre.

### 2. AI WealthPilot — borrow boundary and offline-demo patterns now

**Verified facts.** AI WealthPilot separates a Python computational core under `src/`, a thin FastAPI transport layer under `api/`, and a Next.js client under `web/`; its README states the browser reaches FastAPI through same-origin proxies and that the transport layer should contain no financial logic ([architecture in README](https://github.com/Michelia-L/AI-WealthPilot/blob/main/README.md#-system-architecture)). Its [`api/schemas.py`](https://github.com/Michelia-L/AI-WealthPilot/blob/main/api/schemas.py) uses explicit Pydantic response models, including fleet monitoring with `ok`, `breach`, and `unknown` states. Its [`src/agents/demo_mode.py`](https://github.com/Michelia-L/AI-WealthPilot/blob/main/src/agents/demo_mode.py) replays deterministic, fictional, bilingual fixtures with zero model calls while maintaining the real event shape. The repository includes tests for demo mode and advisory replay ([test tree](https://github.com/Michelia-L/AI-WealthPilot/tree/main/tests)).

**JB Clarity fit (inference).** This validates two decisions already present in the local specification:

- Builder 1 should expose an explicit typed model at the engine boundary, not pandas internals.
- The demo should use cached validated language and an offline golden path with exactly the same presentation contract as any optional live model path.

Use the pattern, not its data models. `contracts/workbench.schema.json` remains JB Clarity's source of truth; introducing AI WealthPilot's portfolio or IPS schema would create a competing contract.

Its fleet `breach`/`unknown` distinction is a useful reminder for mandate and evidence-conflict status, but JB Clarity needs the more specific current/near/historical-resolved states and separate Confidence. Its MVO, Black–Litterman, Monte Carlo, IPS multi-agent workflow, and rebalancing engine are unnecessary for the agreed demo and would add integration risk.

**Decision: BORROW SELECTIVELY.** Reproduce its fixture-parity and typed-boundary discipline; do not import the optimizer, multi-agent workflow, or its full service.

### 3. Ghostfolio — inspect data-quality tests; do not copy code

**Verified facts.** Ghostfolio is a TypeScript Nx monorepo with an Angular client and a NestJS/Prisma/PostgreSQL backend, Redis caching, multi-account transactions, imports, and portfolio calculations ([README and stack](https://github.com/ghostfolio/ghostfolio/blob/main/README.md#technology-stack)). Its source contains dedicated import validation and extensive portfolio-calculator tests, including multi-currency, partial-sale, split, fee, cash, liability, and missing-price cases ([portfolio calculator](https://github.com/ghostfolio/ghostfolio/tree/main/apps/api/src/app/portfolio/calculator), [import fixtures](https://github.com/ghostfolio/ghostfolio/tree/main/test/import)).

**JB Clarity fit (inference).** Those test categories can inspire Builder 1's edge-case checklist, especially missing FX/price data, duplicate records, partial histories, and stable snapshot calculations. The implementation itself is a poor fit: JB Clarity consumes five supplied snapshots rather than maintaining a retail transaction ledger, uses Python/pandas rather than NestJS/Prisma, and does not need database persistence for the prototype.

**Decision: REFERENCE ONLY.** Do not copy AGPL code or introduce its services.

### 4. Wealthfolio — reference adapter and validation ideas; do not copy code

**Verified facts.** Wealthfolio is an active local-first personal-finance product with a React frontend and a Rust core. Its source separates frontend adapters for web and Tauri and contains extensive import, FX, valuation, snapshot, allocation-target, and drift validation ([repository](https://github.com/wealthfolio/wealthfolio), [core portfolio source](https://github.com/wealthfolio/wealthfolio/tree/main/crates/core/src/portfolio), [frontend adapters](https://github.com/wealthfolio/wealthfolio/tree/main/apps/frontend/src/adapters)). Its addon architecture defines manifest versions, SDK compatibility, permissions, and a host-provided context rather than allowing arbitrary access ([addon architecture](https://github.com/wealthfolio/wealthfolio/blob/main/docs/addons/addon-architecture.md)).

**JB Clarity fit (inference).** Its adapter boundary and version-compatibility concepts resemble JB Clarity's schema-version handshake. Its drift and import test names are a useful review checklist. But JB Clarity already has a much smaller JSON adapter and no plugin requirement; bringing in Rust, Tauri, or the addon runtime would be counterproductive.

**Decision: REFERENCE ONLY.** Preserve `contracts/workbench.schema.json` and independently implement the small boundary already specified. Do not copy AGPL application code.

### 5. Navam Invest — avoid incorporation

**Verified facts.** Navam is a Python terminal-oriented retail-investment assistant with specialised agents and external data tools for SEC, Treasury, FRED, Yahoo Finance, and other providers ([README](https://github.com/navam-io/navam-invest/blob/main/README.md), [agents/tools mapping](https://github.com/navam-io/navam-invest/blob/main/docs/architecture/agents-tools-mapping.md)). It uses a broad conversational router and saves generated reports. Contrary to the supplied description, its checked-in [`LICENSE`](https://github.com/navam-io/navam-invest/blob/main/LICENSE) is Business Source License 1.1 with commercial-use restrictions until 2028-10-24.

**JB Clarity fit (inference).** The source-tracking and cache concepts are directionally relevant, but its open-ended agent routing, live public market data, and retail advisory orientation conflict with JB Clarity's bounded Guided Actions, Controlled Event Source, deterministic calculations, and RM approval. There is no unique seam worth the licensing and integration cost.

**Decision: AVOID CODE.** At most, use its list of tool-result provenance fields as inspiration after independently defining them in the Evidence Packet.

### 6. “Financial Machine Learning” / probable `Jackirn/Fintech` — do not use for ranking

**Verified facts.** The probable repository describes coursework/research projects covering client segmentation, next-best-action prediction, probability calibration, a hard suitability filter, and local/global SHAP explanations ([README](https://github.com/Jackirn/Fintech/blob/main/README.md)). The repository is MIT-licensed, but the supplied name does not uniquely identify it.

**JB Clarity fit (inference).** A SHAP waterfall is visually similar to the factor-contribution explanation JB Clarity needs, but the engine does not need SHAP: every Queue contribution is already a deterministic configured rule. Training an NBA model on this challenge's 20 synthetic clients would be statistically indefensible and would make the ranking harder to audit.

**Decision: AVOID FOR THE PROTOTYPE.** Independently build a small deterministic factor-contribution bar from the Workbench artifact. Do not introduce LightGBM, Optuna, SHAP, or learned suitability scores.

### 7. Riskfolio-Lib — credible but defer

**Verified facts.** Riskfolio-Lib is a BSD-3-Clause Python library for portfolio optimisation and quantitative asset allocation. Its repository exposes portfolio and hierarchical-portfolio classes, risk functions, and constraint functions ([source tree](https://github.com/dcajasn/Riskfolio-Lib/tree/master/riskfolio/src)); its current dependency set includes NumPy, SciPy, pandas, CVXPY, solvers, scikit-learn, statsmodels, and other quantitative packages ([`pyproject.toml`](https://github.com/dcajasn/Riskfolio-Lib/blob/master/pyproject.toml)).

**JB Clarity fit (inference).** It would be appropriate if a later scope required risk contribution, CVaR, Black–Litterman, or constrained rebalancing. None is necessary to prove the chosen problem. Hartono's Collateral Stress Test is a transparent ratio calculation using scenarios supplied by the engine, not a portfolio optimiser; mandate-band checks are also simple deterministic aggregation.

**Decision: DEFER.** Add it only after the complete 20-client Queue, three deep cases, Evidence Chain, and Meeting Brief flow work offline—and only for a specific judged use case.

### 8. Optional bonus: Anthropic Meeting Prep Agent — adapt its guardrails and brief structure

**Verified facts.** Anthropic's Financial Services repository provides reference workflows for financial-services agents and states that outputs are staged for qualified-human review rather than executing transactions or approving decisions ([README](https://github.com/anthropics/financial-services/blob/main/README.md)). Its [`meeting-prep-agent.md`](https://github.com/anthropics/financial-services/blob/main/plugins/agent-plugins/meeting-prep-agent/agents/meeting-prep-agent.md) produces a relationship summary, holdings snapshot, recent activity, open items, relevant market context, suggested agenda, and talking points. It explicitly treats client-provided communications as untrusted and forbids client-facing send.

**JB Clarity fit (inference).** This is the strongest external confirmation of the chosen Meeting Brief shape. Adapt the checklist into the cached language template, with two JB-specific changes:

- use Evidence Packet items and `event_log.csv`, not external CRM/CapIQ calls, for the offline challenge demo;
- include Evidence Conflicts, Open Loop confirmation state, Governance Clocks, preferred language, immutable figures/citations, and explicit RM approval.

Do not add an agent orchestration layer just to reproduce a prompt workflow. The value is the output contract and guardrails.

**Decision: ADAPT NOW.** Treat the prompt and workflow as an Apache-2.0 reference and preserve notices if text is copied materially.

## Minimal adoption plan for the two builders

### Builder 1 — Intelligence Engine

1. Keep the existing pandas-to-Workbench JSON architecture.
2. Reproduce AI WealthPilot's idea of explicit typed output models and offline fixture parity, but map only to `contracts/workbench.schema.json`.
3. Use Ghostfolio and Wealthfolio test categories as a checklist for FX, missing/stale data, duplicate/invalid records, and multi-account aggregation; write original tests against the supplied challenge files.
4. Do not add Riskfolio-Lib, ML models, LangGraph, live-market APIs, or a database for the core build.

### Builder 2 — RM Workbench

1. Inspect Advisor Desktop's `NBAFeed`, `NBACard`, service/hook boundary, and meeting-prep modal.
2. Port only interaction/presentation fragments that reduce build time. Replace its NBA model with JB Clarity's typed Workbench adapter and replace its single-card workflow with Queue → Client Case → Evidence Chain → Meeting Brief.
3. Adapt Anthropic's meeting-prep content checklist and draft/no-send guardrails into the existing Meeting Brief state machine.
4. Reject any borrowed feature that adds open chat, trade/contact execution, configurable AI ranking, or merges Confidence into Urgency.

## Concrete stop/go gate

Spend at most a short inspection session on external code. Proceed with a borrowed fragment only if all are true:

- it directly accelerates an acceptance criterion in the finalized specification;
- it can consume the existing Workbench contract without adding a second domain model;
- its license is compatible and attribution is recorded;
- it does not add network dependence to the demo;
- it preserves deterministic analytics, Evidence Chains, separate Urgency and Confidence, and explicit RM control;
- integrating it is faster than implementing the small seam locally.

Under this gate, the likely code reuse is limited to a few Advisor Desktop React presentation fragments. AI WealthPilot and Anthropic are primarily architectural and workflow references. The other repositories should not become dependencies in the hackathon prototype.
