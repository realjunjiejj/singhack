# Wealth Intelligence

This context describes the advisory problem in the SingHacks 2026 Julius Baer challenge. The product exists to help a Relationship Manager turn portfolio and client evidence into timely, defensible client conversations.

## Language

**Relationship Manager (RM)**:
The bank professional responsible for understanding the client, reviewing evidence, and deciding what advice is appropriate. In this challenge, the RM is Priscilla Ong.
_Avoid_: Adviser bot, autonomous adviser

**Wealth Intelligence Layer**:
The capability between portfolio data and the RM that identifies what matters, explains why, anticipates plausible developments, and proposes actions for review.
_Avoid_: Portfolio dashboard, robo-adviser

**Advisory Insight**:
A client-specific, actionable finding supported by portfolio data, client context, and traceable assumptions or events. It communicates what changed, why it matters now, and what the RM may consider doing.
_Avoid_: Alert, notification, AI answer

**Evidence Chain**:
The inspectable path from source data and approved events through calculations and assumptions to an Advisory Insight.
_Avoid_: AI reasoning

**Controlled Event Source**:
The authoritative record used to ground claims about external events. For this challenge, `event_log.csv` overrides model memory about 2026 events.
_Avoid_: News feed, model knowledge

**Advisory Action**:
A possible next step that the RM may review, modify, reject, or use to prepare a client conversation. It is not autonomous financial advice.
_Avoid_: Automated trade, AI decision

**Book**:
All clients and portfolios for which an RM is responsible. In the challenge dataset, Priscilla's Book contains 20 clients and 24 portfolios.
_Avoid_: Portfolio

**Client Case**:
A prioritised bundle of related Advisory Insights about one client that warrants the RM's attention and preparation for a conversation.
_Avoid_: Alert, notification

**Priority Queue**:
An ordered view of Client Cases that helps the RM decide whom to contact first and why.
_Avoid_: Dashboard, client list

**Conversation Plan**:
An RM-editable preparation brief containing the client-specific explanation, evidence, uncertainties, and possible next steps for discussion.
_Avoid_: AI advice, automated recommendation

**Priority Rationale**:
The visible, deterministic reasons a Client Case occupies its position in the Priority Queue, including time urgency, threshold status, client impact, objective mismatch, and relationship signals. Evidence Confidence is displayed separately.
_Avoid_: AI score, black-box ranking

**Evidence Packet**:
The bounded set of source records, derived metrics, and approved events supplied to AI for one Client Case. Every generated factual claim must point back to an item in this packet.
_Avoid_: Prompt context, entire dataset

**Evidence Conflict**:
A material disagreement between sources that prevents the system from treating a conclusion as settled. It lowers displayed confidence and remains visible to the RM.
_Avoid_: Data cleanup, AI reconciliation

**Urgency**:
How soon and how seriously a Client Case requires RM attention, independent of whether all supporting evidence is complete.
_Avoid_: Confidence, risk tolerance

**Confidence**:
How strongly the available Evidence Packet supports a Client Case's interpretation. Confidence does not determine whether an urgent case deserves attention.
_Avoid_: Urgency, probability of loss

**Collateral Stress Test**:
A transparent what-if calculation showing how a defined change in collateral value would affect a credit facility's loan-to-value ratio and margin-call status.
_Avoid_: Market forecast, price prediction

**Safety Override**:
A deterministic condition that assigns a Client Case Critical Urgency regardless of its weighted score because an active breach or imminent unmet obligation requires immediate RM attention.
_Avoid_: AI escalation, high score

**Eligible Liquidity**:
Assets realistically available to meet a particular obligation within its required time window, after accounting for liquidity tier, currency, commitments, and known restrictions.
_Avoid_: Cash balance, portfolio value

**Case Resolution**:
The RM-recorded outcome of reviewing a Client Case: prepare a conversation, request information, involve a specialist, or dismiss the case with a reason.
_Avoid_: Automated action, trade execution

**Guided Action**:
A bounded request the RM can make of the Wealth Intelligence Layer, such as explaining a case, showing its evidence, or preparing a Conversation Plan.
_Avoid_: Open-ended chat, autonomous agent

**Client-Ready View**:
An RM-reviewed rendering of a Conversation Plan in the client's preferred reporting language, shown alongside the canonical internal version with unchanged figures and evidence references.
_Avoid_: Raw translation, autonomous client message

**Anticipatory Signal**:
A source-cited indication that a client is likely to encounter a material financial or governance issue soon, before the client raises it with the RM.
_Avoid_: Alert spam, market prediction

**Open Loop**:
An unresolved client question, commitment, or repeated discussion evidenced in RM notes and awaiting RM confirmation, resolution, deferral, or assignment.
_Avoid_: Fact, AI task

**Meeting Brief**:
An RM-facing preparation view that combines a Client Case's timely issue, Evidence Chain, Open Loops, preferred language, questions to ask, and possible next steps.
_Avoid_: Client report, automated outreach

**Governance Clock**:
The time-sensitive compliance and administrative obligations relevant to a Client Case, including a KYC review that is due soon or overdue.
_Avoid_: Overdue KYC when it is only due soon
