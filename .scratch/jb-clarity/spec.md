# JB Clarity build specification

**Status:** final local specification — ready to decompose into builder tickets

## Problem Statement

Priscilla Ong is responsible for a Book of 20 clients, 24 portfolios, five dated portfolio snapshots, 1,015 holding records, market events, credit facilities, future obligations, mandates, and free-text relationship notes. Existing portfolio tools describe balances and performance but leave her to determine whom to contact, what changed, why it matters to that client, what may happen next, and how to conduct a defensible conversation.

Important financial warnings can emerge from several sources at once: a facility approaching its margin-call threshold, a confirmed obligation approaching without suitable liquidity, a gated redemption, a mandate breach, or a client objective contradicted by the portfolio. Important relationship work is even less visible: unanswered questions, repeatedly deferred decisions, promises to revisit a subject, and approaching governance deadlines remain buried in RM notes and administrative data.

The prototype must let an RM move from a whole-Book view to a grounded, editable Meeting Brief in under 60 seconds while retaining responsibility for advice.

## Solution

JB Clarity is a desktop-first RM Intelligence Workbench. It converts the supplied synthetic challenge data into a deterministic Workbench model containing a Priority Queue, Client Cases, Evidence Packets, Anticipatory Signals, Open Loops, Governance Clocks, timeline explanations, and Meeting Brief inputs.

The Priority Queue ranks Client Cases across all 20 clients using visible Urgency factors. Confidence is displayed separately so incomplete or conflicting evidence does not hide an urgent case. Critical Urgency is reserved for auditable Safety Overrides. Every conclusion links to an Evidence Chain; claims about 2026 events use the Controlled Event Source.

The three fully developed Client Cases are:

1. Cheung Kwok Wing: retirement income, rising yields, duration losses, increased medical spending, unwillingness to sell at a loss, and Traditional Chinese client communication.
2. Hartono Wijaya Kusuma: historical LTV breaches, self-curing collateral, cross-portfolio energy concentration, structured-product look-through, a future property deposit, and family-governance constraints.
3. Margarethe Voss-Brenner: inherited-portfolio suitability mismatch, a confirmed German inheritance-tax instalment, sensitive relationship context, conflicting portfolio totals, and a German Client-Ready View.

Supporting Book-wide examples include Nguyen Thi Bao Tran's gated redemption and near-term USD obligations; Chalermchai Suphanburi's unanswered deposit question; Tan Boon Huat's fourth deferred succession discussion and KYC due date; Andreas Lindqvist's repeatedly agreed but unexecuted deployment plan; and facilities near their LTV triggers.

AI is optional language generation operating on one bounded Evidence Packet at a time. It does not calculate metrics, select source facts, rank clients, execute transactions, or contact clients. Cached validated output keeps the demonstration functional without a live model.

## User Stories

1. As an RM, I want to see all clients ordered by Urgency, so that I know where to direct my attention first.
2. As an RM, I want Critical, High, and Watch tiers, so that urgency is legible without interpreting raw scores.
3. As an RM, I want the numeric score and factor contributions visible, so that I can defend why one Client Case ranks above another.
4. As an RM, I want Confidence shown separately from Urgency, so that incomplete evidence does not conceal an urgent issue.
5. As an RM, I want to filter the Priority Queue by signal type, booking centre, urgency, and confidence, so that I can prepare a focused work session.
6. As an RM, I want quick access to Cheung, Hartono, and Margarethe, so that their complete demo cases are easy to inspect without falsifying their ranks.
7. As an RM, I want one Client Case to combine related Advisory Insights, so that I do not receive several disconnected alerts about one client.
8. As an RM, I want each Client Case to lead with a plain-language conclusion, so that I understand its significance quickly.
9. As an RM, I want calculations and source records progressively disclosed, so that I can inspect details without being overwhelmed initially.
10. As an RM, I want active, near, and historical-resolved conditions distinguished, so that I never represent an old breach as current.
11. As an RM, I want an LTV Anticipatory Signal before a facility reaches its trigger, so that I can act before the client experiences a margin call.
12. As an RM, I want a facility's LTV history displayed across all snapshots, so that I can understand its direction and prior breaches.
13. As an RM, I want Hartono's unchanged borrowing and rising collateral value shown together, so that I can see why the breach resolved.
14. As an RM, I want a transparent Collateral Stress Test for Hartono, so that I can explore explicit what-if assumptions without presenting them as forecasts.
15. As an RM, I want confirmed obligations displayed with time remaining, currency, certainty, and source, so that approaching needs are not missed.
16. As an RM, I want Eligible Liquidity assessed against an obligation's timing and currency, so that portfolio value is not mistaken for available funding.
17. As an RM, I want redemption gates and other liquidity restrictions surfaced, so that I do not promise access to capital that cannot be delivered on time.
18. As an RM, I want current mandate-band breaches identified, so that I can distinguish portfolio drift from compliant allocation.
19. As an RM, I want binding exclusions distinguished from ordinary allocation drift, so that compliance-sensitive cases receive the right treatment.
20. As an RM, I want client-directed exceptions and waivers found in RM notes to be visible, so that a deliberate exception is not presented as an unexplained breach.
21. As an RM, I want structured-product underlying references included in concentration analysis, so that hidden exposure is not missed.
22. As an RM, I want exposure aggregated across all portfolios belonging to a client, so that custody and managed holdings contribute to the client's full risk picture.
23. As an RM, I want a client's source of wealth and stated objectives compared with portfolio exposure, so that concentration outside the report becomes visible.
24. As an RM, I want a replayable timeline across the five snapshots, so that I can explain what changed rather than describe only today's portfolio.
25. As an RM, I want event explanations grounded in `event_log.csv`, so that I can defend external-event claims in a compliance review.
26. As an RM, I want Open Loop candidates extracted from dated RM notes with their supporting excerpts, so that relationship commitments are not forgotten.
27. As an RM, I want to confirm, defer, assign, or dismiss an Open Loop candidate, so that the system does not treat an AI interpretation as fact.
28. As an RM, I want unanswered messages called out, so that the client does not need to chase the bank.
29. As an RM, I want repeated unresolved discussions recognised, so that the next meeting continues the relationship rather than restarting it.
30. As an RM, I want KYC shown as due soon or overdue relative to the as-of date, so that governance wording is accurate.
31. As an RM, I want a Meeting Brief combining the timely issue, Evidence Chain, Open Loops, Governance Clock, questions, and possible next steps, so that preparation is consolidated.
32. As an RM, I want the Meeting Brief to be editable, so that I retain responsibility for judgment and wording.
33. As an RM, I want to approve the Conversation Plan explicitly, so that AI-drafted language cannot become client communication by accident.
34. As an RM, I want a Client-Ready View in the client's reporting language, so that the conversation respects the client's communication needs.
35. As an RM, I want the canonical and translated versions shown side by side, so that I can review translation without losing traceability.
36. As an RM, I want figures and evidence references preserved across translations, so that language generation cannot alter the underlying conclusion.
37. As an RM, I want guided actions such as Explain, Show evidence, and Prepare conversation, so that AI interaction is predictable and grounded.
38. As an RM, I want every generated factual claim to cite an Evidence Packet item, so that unsupported language is visible and rejectable.
39. As an RM, I want Evidence Conflicts surfaced with reduced Confidence, so that uncertainty is handled honestly.
40. As an RM, I want cached validated language available when a model is unavailable, so that the core workbench and demonstration remain usable.
41. As a risk or compliance stakeholder, I want deterministic calculations separated from generated language, so that the system boundary is auditable.
42. As a product stakeholder, I want a target architecture showing identity, entitlements, encryption, audit, and deployment boundaries, so that feasibility in a private bank is credible.
43. As a judge, I want the interface to reveal client understanding rather than arithmetic alone, so that I can assess client-centric innovation.
44. As a judge, I want the live demo to work without external connectivity, so that the product value is observable under presentation conditions.

## Implementation Decisions

### System boundary

- Python and pandas ingest the supplied CSV and JSON files, validate their relationships, derive metrics, apply detectors, build Evidence Packets, and emit a versioned Workbench model.
- Next.js with TypeScript renders the desktop workbench from the Workbench model.
- The browser never interprets raw financial data with a general language model.
- The prototype uses the supplied synthetic files and a fixed default as-of date of 2026-08-26.
- Production security capabilities are represented in a target-architecture view; authentication, entitlement infrastructure, and bank deployment are not implemented.

### Highest behavioral seam

- The primary test seam accepts a challenge data source and as-of date and returns the complete Workbench model.
- The Workbench model contains Book summary data, ordered Client Cases, urgency and confidence, factor contributions, Evidence Packets, and selected-case detail.
- Calculation components may have narrower tests when their boundary is independently meaningful, but implementation details of pandas operations are not tested directly.

### Evidence Packet contract

- Every Evidence Packet has a stable case identifier, client identifier, as-of date, signal type, status, urgency inputs, confidence inputs, plain-language facts, derived metrics, source references, conflicts, assumptions, and allowed Guided Actions.
- A source reference identifies the source file and stable record key or row identity needed to reproduce the claim.
- Derived metrics name their formula, inputs, units, and snapshot date.
- Facts, interpretations, and uncertainties are separate fields.
- Event-related claims reference only records from the Controlled Event Source.
- Generated language may cite packet item identifiers but cannot introduce a new source fact.

### Signal detection and status

- Facility signals distinguish active breach, near trigger, historical resolved breach, and normal status.
- Near-trigger thresholds are transparent configuration values, initially expressed as percentage-point distance from the facility trigger and trend across snapshots.
- Cash-need signals use due date, certainty, currency, recurrence, and Eligible Liquidity. Currency conversion follows the dataset's documented market conventions.
- Redemption-gate signals combine the gated position, the redemption or RM note, and the relevant obligation; a gate is not equivalent to total illiquidity.
- Mandate signals calculate current asset-class bands for managed portfolios, assess applicable single-position limits, and distinguish custody accounts.
- Binding sustainability exclusions are evaluated separately from ordinary band drift.
- Structured-product concentration uses `underlying_reference`; limitations of free-text look-through remain explicit.
- KYC status is calculated relative to the as-of date as due soon, due today, or overdue. On 2026-08-26 no client is labelled overdue.
- Open Loops are candidates with note date and excerpt. They require RM confirmation before becoming tracked relationship commitments.
- Data-quality checks include referential integrity, missing values relevant to a calculation, valuation-date lag, and material disagreements between client, portfolio, and holding totals.

### Urgency and confidence

- Critical Urgency is assigned only by a Safety Override: an active facility breach; a confirmed obligation beginning within 90 days with less than full Eligible Liquidity coverage; or an unwaived binding exclusion or compliance breach.
- Non-critical cases receive a transparent 0–100 score from time urgency, threshold proximity or historical breach, suitability or objective mismatch, financial exposure, and relationship signals.
- Exact point calibration is versioned configuration derived from the supplied dataset distribution, not learned or selected by an LLM.
- The highest-severity Advisory Insight establishes a Client Case's base priority. Independent additional signals add capped escalation points.
- Confidence is independent of Urgency and reflects source completeness, agreement, calculation quality, and whether human confirmation remains necessary.
- Queue ordering is deterministic, stable, and never manipulated to place the three demonstration clients first.

### Selected Client Cases

- Cheung's case connects rising yields and duration-sensitive holdings to his retirement-income objective and increased confirmed annual cash need. It distinguishes the objective's USD 1.1m wording from the USD 1.28m planned-cash record.
- Hartono's case shows LTV of 78.50% and 75.68% against a 70% trigger before resolution to 58.86%, alongside unchanged SGD 8m borrowing and increased lending value from the collateral portfolio. It aggregates direct energy exposure and the energy-linked structured product, and surfaces the SGD 9m property need and family constraint.
- Margarethe's case shows a Conservative profile against a strongly equity-weighted inherited portfolio, the confirmed EUR 3.4m obligation, relationship sensitivity, and the material disagreement between current portfolio AUM and holdings/client totals.

### Workbench interaction

- The desktop information architecture is a persistent Command Centre: Priority Queue on the left, active Client Case in the centre, and contextual Evidence Chain or Meeting Brief on the right. This is a deliberate implementation constraint made without a separate UI-validation prototype.
- The default route is the Priority Queue with Book summary, filters, urgency tiers, confidence, and short Priority Rationales.
- Opening a Client Case shows its conclusion, why now, factor breakdown, selected timeline, Anticipatory Signals, Open Loops, Governance Clock, and Guided Actions.
- Evidence is progressively disclosed in a drawer or adjacent pane and always remains reachable from the corresponding claim.
- The timeline supports comparison between two of the five supplied snapshots.
- The Hartono Collateral Stress Test varies an explicit collateral-value assumption and recalculates lending value, LTV, distance to trigger, and status. It is labelled as a what-if calculation.
- Prepare conversation creates an editable Meeting Brief. Approval is an explicit in-memory state transition in the prototype.
- The Client-Ready View uses `reporting_language`, displays canonical and translated versions together, preserves quantities and source references, and labels generated text as a draft.
- Case Resolution supports prepare, request information, involve specialist, dismiss with reason, and Open Loop confirmation or deferral. It does not execute a trade or send a message.

### Language generation

- The language endpoint accepts one Evidence Packet and a fixed task type.
- Output follows a validated structured schema for summary, why-now explanation, uncertainty, opening question, discussion options, specialist suggestion, and cited packet item identifiers.
- Unsupported citations or changed figures invalidate the output and trigger cached fallback.
- Client-language generation translates the approved canonical content; it does not independently reinterpret evidence.
- The workbench is fully demonstrable from cached outputs and deterministic data when no API key or network is available.

### Presentation

- Product name: JB Clarity.
- Product thesis: AI should not replace wealth advice; it should make every RM conversation timely, personal, and defensible.
- Demo order: brief Priscilla framing; Priority Queue; Hartono; Cheung; Margarethe; architecture and governance; strategic impact.
- The primary challenge block is RM Intelligence Workbench, supported by Proactive Risk and Opportunity Detection and Intelligent Portfolio Explanations.

## Testing Decisions

- Tests assert observable financial and user-facing behavior, not dataframe operations, component internals, or incidental markup.
- The highest-value suite invokes the complete Workbench-model seam with the supplied fixture dataset and fixed as-of date.
- Contract tests validate every Evidence Packet and generated-language response against their schemas.
- Golden behavioral cases cover active, near, historical-resolved, and normal facility states; obligation-window boundaries; insufficient and sufficient Eligible Liquidity; custody-account handling; mandate drift; binding exclusions; KYC date boundaries; structured-product look-through; and Evidence Conflicts.
- Regression tests pin the verified Cheung, Hartono, Margarethe, Nguyen, Chalermchai, Tan, and Andreas facts used by the demonstration.
- Queue tests verify deterministic ordering, Safety Overrides, capped compound-signal escalation, separation of Confidence, and lack of demo-client manipulation.
- UI tests cover the golden path from Priority Queue to Evidence Chain to editable Meeting Brief to approval, including cached-language fallback.
- Accessibility checks cover keyboard navigation, visible focus, semantic labels, non-color urgency cues, readable financial formatting, and bilingual layout.
- A presentation smoke test runs the app from a clean checkout using the documented single command and no live AI credentials.
- There is no existing application-test prior art in the repository. The initial implementation establishes the highest behavioral seam and minimal browser-flow coverage.

## Out of Scope

- Autonomous investment advice, portfolio management, trade execution, or order creation
- Automatic client contact, email, messaging, or calendar integration
- An open-ended chatbot over the Book
- Live market data, live news, or model-memory claims about 2026 events
- A generic scenario engine; only Hartono's bounded collateral what-if is included
- Production authentication, authorization, encryption key management, banking integrations, or regulatory approval
- Definitive tax, legal, or suitability advice
- Automatic resolution of conflicting data
- Full semantic parsing of every possible structured-product payoff
- Fully developed experiences for all 20 clients
- A mobile client application
- Persistent workflow state or multi-user collaboration in the prototype

## Further Notes

- The source challenge explicitly rewards depth on two or three clients over shallow analysis of all twenty.
- Raw portfolio and holding values include intentional imperfections. The product gains credibility by identifying them and narrowing conclusions accordingly.
- The prototype's success criterion is whether a non-developer can determine whom to call, understand why, inspect the evidence, and reach an approved Meeting Brief in under 60 seconds.
- The Command Centre layout is intentionally a first-build constraint rather than a validated UX finding. Preserve enough layout separation that it can be revised after demo rehearsal without changing Workbench-model behavior.
- ADRs under `docs/adr/` are the decision record. This specification is the behavioral source of truth for implementation.
