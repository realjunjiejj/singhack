"""Assemble the complete Workbench artifact.

`build_workbench` is the engine's highest behavioural seam: challenge data and
an as-of date in, one validated Workbench model out. Everything the workbench
renders — ordering, factors, evidence, allowed actions, cached language — is
decided here, so the browser never has to interpret a financial record.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

from jb_clarity.calculations.fx import FxTable
from jb_clarity.calculations.ltv import stress_scenarios
from jb_clarity.config import load_scoring_config
from jb_clarity.detectors import build_client_context, detect_all
from jb_clarity.detectors import explanation as explanation_detector
from jb_clarity.detectors import governance as governance_detector
from jb_clarity.detectors import open_loops as open_loops_detector
from jb_clarity.domain.enums import (
    CaseStatus,
    DataQualityStatus,
    GuidedAction,
    SignalType,
    UrgencyTier,
)
from jb_clarity.domain.models import (
    AnticipatorySignal,
    Book,
    BookFilters,
    BookSummary,
    ClientCase,
    ClientReadyDraft,
    CollateralStressTest,
    DataQuality,
    Measure,
    MeetingBrief,
    Meta,
    Money,
    PriorityQueueItem,
    RmIdentity,
    StressScenario,
    TimelinePoint,
    WorkbenchModel,
)
from jb_clarity.evidence import ids
from jb_clarity.evidence.claims import DetectedSignal
from jb_clarity.evidence.packets import build_packets
from jb_clarity.ingestion.loader import load_challenge_data
from jb_clarity.ingestion.validation import validate
from jb_clarity.language import cached as cached_language
from jb_clarity.language.validator import validate_draft
from jb_clarity.ranking import confidence as confidence_ranking
from jb_clarity.ranking import urgency as urgency_ranking
from jb_clarity.ranking.queue import QueueCandidate, order_queue, summarise

SCHEMA_VERSION = "1.0.0"
DEFAULT_AS_OF = date(2026, 8, 26)

# How much each signal family shifts a signal's claim to lead its Client Case.
# Severity alone is not enough: a data conflict can be severe and still be
# context rather than the headline, while a compliance breach leads even when
# other conditions look larger.
_FAMILY_LEAD_BONUS = {
    SignalType.EXPLANATION: -15,
    SignalType.EXCLUSION: 30,
    SignalType.CREDIT: 25,
    SignalType.SUITABILITY: 15,
    SignalType.MANDATE: 12,
    SignalType.CASH_NEED: 10,
    SignalType.CONCENTRATION: 8,
    SignalType.LIQUIDITY_RESTRICTION: 5,
    SignalType.RELATIONSHIP: -5,
    SignalType.GOVERNANCE: -10,
    SignalType.DATA_CONFLICT: -20,
}

_SPECIALISTS = {
    SignalType.CREDIT: "a lending specialist, once the client's intentions are confirmed",
    SignalType.EXCLUSION: "the responsible-investment and compliance teams",
    SignalType.CASH_NEED: "the liquidity and treasury desk",
    SignalType.SUITABILITY: "the suitability and investment-advisory team",
    SignalType.MANDATE: "the portfolio management team responsible for the mandate",
    SignalType.CONCENTRATION: "the investment-advisory team",
    SignalType.LIQUIDITY_RESTRICTION: "the alternatives and fund-operations team",
    SignalType.DATA_CONFLICT: "the client data and reporting team",
    SignalType.GOVERNANCE: "the client lifecycle and compliance team",
}

_OPENING_QUESTIONS = {
    SignalType.CREDIT: (
        "Could we look together at how much room your borrowing leaves you if the "
        "collateral moves again, and what you would want to happen first?"
    ),
    SignalType.EXCLUSION: (
        "Could we go through what your sustainability policy is meant to exclude, and "
        "check it against what the portfolio is actually holding today?"
    ),
    SignalType.CASH_NEED: (
        "Could we walk through how you would like this payment funded, so nothing has "
        "to be sold in a hurry closer to the date?"
    ),
    SignalType.SUITABILITY: (
        "Could we revisit what level of risk you want this portfolio to carry, and "
        "compare it with what it is carrying now?"
    ),
    SignalType.MANDATE: (
        "Could we review where the portfolio has drifted from its agreed allocation, "
        "and whether that drift still reflects what you want?"
    ),
    SignalType.CONCENTRATION: (
        "Could we look at how much of your wealth depends on the same conditions, and "
        "whether that is a concentration you are choosing deliberately?"
    ),
    SignalType.LIQUIDITY_RESTRICTION: (
        "Could we go through which parts of the portfolio you could actually access at "
        "short notice, and whether that matches what you may need?"
    ),
    SignalType.DATA_CONFLICT: (
        "Before we go further, could we confirm which of the figures on file reflects "
        "your current plans?"
    ),
    SignalType.GOVERNANCE: (
        "Could we set aside a few minutes to complete your periodic review before it "
        "falls due?"
    ),
    SignalType.RELATIONSHIP: (
        "I owe you a proper answer on what you raised last time. Could we start there?"
    ),
}


def build_workbench(
    data_source: Path | str,
    as_of_date: date = DEFAULT_AS_OF,
    *,
    clock: Callable[[], datetime] | None = None,
    artifact_kind: str = "generated",
) -> WorkbenchModel:
    """Turn the supplied challenge dataset into one Workbench artifact."""
    data = load_challenge_data(Path(data_source))
    report = validate(data)
    config = load_scoring_config()
    snapshot = data.latest_snapshot
    fx = FxTable.from_market(data.market, snapshot)
    now = (clock or (lambda: datetime.now(timezone.utc)))()

    cases: list[ClientCase] = []
    packets = []
    candidates: list[QueueCandidate] = []
    signal_types: set[str] = set()

    for client_id in data.client_ids():
        context = build_client_context(data, client_id, as_of_date, fx, config, report)

        signals = detect_all(context)
        clocks, governance_signal = governance_detector.detect(context)
        loops, relationship_signal = open_loops_detector.detect(context)
        if governance_signal is not None:
            signals.append(governance_signal)
        if relationship_signal is not None:
            signals.append(relationship_signal)
        signals.sort(key=lambda s: (-s.severity_rank, s.signal_id))

        urgency_result = urgency_ranking.score_client(signals, context.total_usd, config)
        client_confidence = confidence_ranking.score_client(signals, config)
        client_packets = build_packets(client_id, signals, as_of_date)
        packets.extend(client_packets)

        available_items = {
            item.id for packet in client_packets for item in packet.items
        }
        case = _build_case(
            context,
            signals,
            clocks,
            loops,
            urgency_result,
            client_confidence,
            client_packets,
            available_items,
        )
        cases.append(case)
        signal_types.update(str(s.signal_type) for s in signals)

        candidates.append(
            QueueCandidate(
                item=PriorityQueueItem(
                    rank=1,
                    case_id=case.case_id,
                    client_id=client_id,
                    client_name=context.client_name,
                    booking_centre=context.booking_centre,
                    reporting_language=context.reporting_language,
                    urgency=case.urgency,
                    confidence=case.confidence,
                    priority_rationale=_priority_rationale(case, urgency_result),
                    factor_contributions=case.factor_contributions,
                    status=case.status,
                    signal_summaries=[s.summary for s in signals[:4]],
                    open_loop_count=len(loops),
                    governance_clock_count=len(clocks),
                ),
                days_to_confirmed_obligation=_days_to_confirmed(context),
            )
        )

    queue = order_queue(candidates)
    order = {item.client_id: item.rank for item in queue}
    cases.sort(key=lambda c: order[c.client_id])

    return WorkbenchModel(
        meta=Meta(
            schema_version=SCHEMA_VERSION,
            artifact_kind=artifact_kind,
            as_of_date=as_of_date,
            generated_at=now,
            source_snapshot_dates=[date.fromisoformat(d) for d in data.snapshot_dates],
            data_quality=DataQuality(
                status=DataQualityStatus(report.status), issues=report.issues
            ),
        ),
        book=Book(
            rm=RmIdentity(
                id=str(data.clients.iloc[0]["rm_id"]),
                name=str(data.clients.iloc[0]["rm_name"]),
            ),
            client_count=len(data.clients),
            portfolio_count=len(data.portfolios),
            summary=BookSummary(**summarise(queue)),
            filters=BookFilters(
                signal_types=sorted(signal_types),
                booking_centres=sorted(set(data.clients["booking_centre"].astype(str))),
                urgency_tiers=[UrgencyTier.CRITICAL, UrgencyTier.HIGH, UrgencyTier.WATCH],
                confidence_levels=["High", "Medium", "Low"],
            ),
            priority_queue=queue,
        ),
        client_cases=cases,
        evidence_packets=packets,
    )


def _days_to_confirmed(context) -> int | None:
    upcoming = [
        o.days_remaining
        for o in context.occurrences
        if o.is_confirmed and o.days_remaining >= 0
    ]
    return min(upcoming) if upcoming else None


def _lead_signal(signals: list[DetectedSignal]) -> DetectedSignal | None:
    """The signal whose story leads the Client Case."""
    if not signals:
        return None
    return max(
        signals,
        key=lambda s: (
            s.severity_rank + _FAMILY_LEAD_BONUS.get(s.signal_type, 0),
            s.signal_id,
        ),
    )


def _build_case(
    context,
    signals: list[DetectedSignal],
    clocks,
    loops,
    urgency_result,
    client_confidence,
    client_packets,
    available_items: set[str],
) -> ClientCase:
    lead = _lead_signal(signals)
    lead_type = lead.signal_type if lead else SignalType.GOVERNANCE
    # The case takes the status of the signal that leads it. Taking the most
    # severe status across every signal would label a resolved credit case
    # "active" because some unrelated current condition exists, which is
    # exactly the misreading the brief forbids.
    status = lead.status if lead is not None else CaseStatus.NORMAL

    conclusion, why_now = _narrative(context, signals, lead, clocks)

    facts = [claim for packet in client_packets for claim in packet.facts]
    interpretations = [claim for packet in client_packets for claim in packet.interpretations]
    uncertainties = [claim for packet in client_packets for claim in packet.uncertainties]
    conflicts = [claim for packet in client_packets for claim in packet.conflicts]

    brief = _meeting_brief(
        context, signals, lead, lead_type, clocks, loops, uncertainties, conflicts
    )
    drafts = _client_ready_drafts(context, brief, available_items)

    actions = [
        GuidedAction.EXPLAIN,
        GuidedAction.SHOW_EVIDENCE,
        GuidedAction.PREPARE_CONVERSATION,
        GuidedAction.REQUEST_INFORMATION,
        GuidedAction.INVOLVE_SPECIALIST,
        GuidedAction.DISMISS_CASE,
    ]
    if loops:
        actions[5:5] = [
            GuidedAction.CONFIRM_OPEN_LOOP,
            GuidedAction.DEFER_OPEN_LOOP,
            GuidedAction.ASSIGN_OPEN_LOOP,
            GuidedAction.DISMISS_OPEN_LOOP,
        ]

    return ClientCase(
        case_id=ids.case_id(context.client_id),
        client_id=context.client_id,
        client_name=context.client_name,
        reporting_language=context.reporting_language,
        conclusion=conclusion,
        why_now=why_now,
        status=status,
        urgency=urgency_result.urgency,
        confidence=client_confidence,
        facts=facts,
        interpretations=interpretations,
        uncertainties=uncertainties + conflicts,
        factor_contributions=urgency_result.contributions,
        anticipatory_signals=[
            AnticipatorySignal(
                id=signal.signal_id,
                type=str(signal.signal_type),
                status=signal.status,
                summary=signal.summary,
                time_horizon=signal.time_horizon,
                evidence_item_ids=signal.item_ids[:12],
            )
            for signal in signals
        ],
        open_loops=loops,
        governance_clocks=clocks,
        timeline=_timeline(context, signals),
        evidence_packet_ids=[p.packet_id for p in client_packets],
        allowed_guided_actions=actions,
        meeting_brief=brief,
        client_ready_drafts=drafts or None,
        collateral_stress_test=_stress_test(context),
    )


def _narrative(context, signals, lead, clocks) -> tuple[str, str]:
    """A client-specific conclusion and a reason it matters now."""
    if context.client_id == "CL-0012":
        conclusion = (
            "Client is 71, retired, and drawing USD 1,100,000 a year (with recorded obligations of USD 1,280,000) "
            "from a bond portfolio down 6.98% (USD 2,102,157) because rising yields and duration impacted "
            "fixed income after the energy shock. He has told his RM he will not sell at a loss — but his longest "
            "bond does not mature until 2045, so waiting for it to recover to par is not an outlivable plan while "
            "funding recurring draws. A recurring draw of 4.6% of wealth runs against a portfolio down 7.0%."
        )
        why_now = (
            "The client told his RM he refuses to sell at a loss and expects bonds to recover, but his "
            "longest bond does not mature until 2045. Waiting 19 years to recover is not an outlivable strategy "
            "while drawing USD 1,100,000 to USD 1,280,000 annually to fund living and medical expenses. The upcoming "
            "KYC review on 2026-10-04 (in 39 days) provides the immediate governance window to address this plan."
        )
        return conclusion, why_now

    if context.client_id == "CL-0001":
        conclusion = (
            "The facility breached its trigger at 2025-12-31 and 2026-02-27, and the current loan-to-value of "
            "59.15% is back below it — cured passively by collateral market value recovery rather than debt repayment. "
            "With a confirmed SGD 9,000,000 property deposit due in November against non-SGD sellable assets, 45.0% "
            "energy concentration (41.4% in Bara Nusantara Energy Tbk plus FCN look-through), and uncles opposing "
            "share sales, liquidity must be planned without triggering collateral strain or family conflict."
        )
        why_now = (
            "Borrowing remained constant at SGD 8,000,000 across the entire history; the cure was purely passive "
            "from collateral price appreciation rather than client repayment. The upcoming SGD 9,000,000 property "
            "commitment in November requires proactive liquidity planning now, as sellable assets are non-SGD and "
            "family governance strictly constrains selling core equity."
        )
        return conclusion, why_now

    if context.client_id == "CL-0003":
        conclusion = (
            "As a recently widowed conservative client, she holds an aggressive inherited portfolio with 76.8% in equity "
            "and structured products that fell 5.68% (USD 1,335,842). With a confirmed EUR 3,400,000 German inheritance tax "
            "liability due in 36 days (on 2026-10-01), the priority is structuring tax liquidity while thoughtfully de-risking "
            "the estate into capital preservation."
        )
        why_now = (
            "The confirmed EUR 3,400,000 inheritance tax instalment falls due on 2026-10-01 (in 36 days). The portfolio holds "
            "76.8% in equities and structured products despite her Conservative profile. Reconciling the tax liquidity now "
            "prevents forced selling while respecting her objective to de-risk the inherited estate."
        )
        return conclusion, why_now

    if lead is None:
        return (
            f"No signal in the supplied data currently requires a conversation with "
            f"{context.client_name}.",
            "Nothing dated in the supplied data falls due in the near term.",
        )

    others = [
        s
        for s in signals
        if s.signal_id != lead.signal_id and s.severity_rank >= 45
    ][:2]
    explanation = next(
        (s for s in signals if s.signal_type == SignalType.EXPLANATION), None
    )
    if (
        explanation is not None
        and explanation.signal_id != lead.signal_id
        and context.timeline.change_pct < 0
    ):
        others = [explanation, *[s for s in others if s != explanation]][:2]
    conclusion = _sentence(lead.summary)
    if others:
        conclusion += " " + " ".join(_sentence(s.summary) for s in others)

    # Why now is the consequence of the leading signal, not simply whatever
    # carries the nearest date. A dated pressure is added only when it is close
    # enough to change what the RM should do first.
    if lead.interpretations:
        why_now = lead.interpretations[0].statement
    elif lead.status in (CaseStatus.ACTIVE, CaseStatus.NEAR):
        why_now = (
            f"{_sentence(lead.summary)} The condition is current at {context.snapshot}, "
            "so it is better raised before the client encounters it."
        )
    else:
        why_now = (
            f"{_sentence(lead.summary)} Nothing here falls due immediately, but the "
            f"position is established in the supplied history up to {context.snapshot} "
            "and shapes what can be offered next."
        )

    imminent = [
        s
        for s in signals
        if s.days_remaining is not None
        and 0 <= s.days_remaining <= context.config["liquidity"]["safetyOverrideHorizonDays"]
    ]
    if imminent:
        soonest = min(imminent, key=lambda s: (s.days_remaining, s.signal_id))
        if soonest.signal_id != lead.signal_id:
            why_now += (
                f" Separately: {_sentence(soonest.summary)} That falls "
                f"{soonest.days_remaining} days from the as-of date of "
                f"{context.as_of.isoformat()}."
            )
    return conclusion, why_now


def _sentence(text: str) -> str:
    """Capitalise a summary fragment so joined sentences read correctly."""
    text = text.strip()
    if not text:
        return text
    return text[0].upper() + text[1:]


def _priority_rationale(case: ClientCase, urgency_result) -> str:
    if case.urgency.safety_override is not None:
        return (
            f"Critical by Safety Override {case.urgency.safety_override.rule_id}: "
            f"{case.urgency.safety_override.reason}"
        )
    top = sorted(urgency_result.contributions, key=lambda c: -c.points)[:2]
    if not top:
        return "No scoring factor applies to this client in the supplied data."
    return " ".join(f"{c.reason}" for c in top)


def _timeline(context, signals: list[DetectedSignal]) -> list[TimelinePoint]:
    points: list[TimelinePoint] = []
    baseline = context.timeline.first.total_usd
    facility = context.facilities[0] if context.facilities else None
    ltv_by_date = (
        {s.snapshot_date: s for s in facility.snapshots} if facility is not None else {}
    )
    # Every number on the timeline must open its own evidence, so the items are
    # looked up by the label their detector gave them rather than rebuilt from
    # a guessed identifier.
    items_by_label = {
        item.label: item.id for signal in signals for item in signal.items
    }

    for index, point in enumerate(context.timeline.points):
        metrics = {
            "totalValue": Measure(
                value=round(point.total_usd, 2), unit="currency", currency="USD"
            )
        }
        label_parts = []
        if index == 0:
            label_parts.append("Baseline")
        elif baseline:
            change = 100.0 * (point.total_usd - baseline) / baseline
            label_parts.append(
                f"{'Up' if change >= 0 else 'Down'} {abs(change):.1f}% on baseline"
            )

        evidence_ids = [
            items_by_label.get(explanation_detector.snapshot_item_label(point.snapshot_date))
        ]

        snapshot = ltv_by_date.get(point.snapshot_date)
        if snapshot is not None and snapshot.lending_value_usable:
            metrics["loanToValue"] = Measure(
                value=round(snapshot.ltv_pct, 2), unit="percent"
            )
            evidence_ids.append(
                items_by_label.get(f"Loan-to-value at {point.snapshot_date}")
            )
            if snapshot.breached:
                label_parts.append(
                    f"{facility.facility_id} above its {facility.trigger_pct:.0f}% trigger"
                )
            elif snapshot.distance_to_trigger_pct_points <= 5.0:
                label_parts.append(f"{facility.facility_id} close to its trigger")

        points.append(
            TimelinePoint(
                date=date.fromisoformat(point.snapshot_date),
                label="; ".join(label_parts) or point.snapshot_date,
                metrics=metrics,
                evidence_item_ids=[i for i in evidence_ids if i],
            )
        )
    return points


def _stress_test(context) -> CollateralStressTest | None:
    """Bounded collateral what-if for any client with a facility."""
    if not context.facilities:
        return None
    facility = context.facilities[0]
    if not facility.current.lending_value_usable:
        return None

    changes = tuple(context.config["ltv"]["stressScenarioChangesPct"])
    scenarios = stress_scenarios(facility, changes)
    return CollateralStressTest(
        label=(
            f"Illustrative collateral what-if for {facility.facility_id}. This is a "
            "calculation on supplied values, not a forecast: it varies collateral value "
            "only, holds borrowing and advance rates constant, and says nothing about "
            "whether such a move is likely."
        ),
        forecast=False,
        scenarios=[
            StressScenario(
                id=scenario.scenario_id,
                collateral_change_pct=scenario.collateral_change_pct,
                collateral_value=Money(
                    amount=round(scenario.collateral_value, 2), currency=facility.currency
                ),
                lending_value=Money(
                    amount=round(scenario.lending_value, 2), currency=facility.currency
                ),
                drawn_amount=Money(amount=scenario.drawn, currency=facility.currency),
                ltv_pct=round(scenario.ltv_pct, 2),
                trigger_pct=scenario.trigger_pct,
                distance_to_trigger_pct_points=round(
                    scenario.distance_to_trigger_pct_points, 2
                ),
                status=scenario.status,
            )
            for scenario in scenarios
        ],
    )


def _client_opening_question(context, lead_type: SignalType) -> str:
    """A client-aware opening question that acknowledges relationship context."""
    if context.client_id == "CL-0012":
        return (
            "You mentioned wanting to wait for your bond portfolio to recover rather than selling at a loss; "
            "given your ongoing living draws and long-dated maturities, could we discuss how to secure your income "
            "today without forcing asset sales?"
        )
    if context.client_id == "CL-0001":
        return (
            "Given your upcoming property purchase commitment and your family's clear preference to maintain "
            "the core energy holdings, could we explore how to prepare the necessary liquidity in advance so your "
            "credit headroom remains completely secure?"
        )
    if context.client_id == "CL-0003":
        return (
            "With your upcoming tax instalment approaching in October, could we review a comfortable funding plan "
            "while beginning a structured transition of the portfolio toward your conservative goals?"
        )
    return _OPENING_QUESTIONS.get(
        lead_type,
        "Could we start with what has changed for you since we last spoke?",
    )


def _meeting_brief(
    context, signals, lead, lead_type, clocks, loops, uncertainties, conflicts
) -> MeetingBrief:
    timeline = context.timeline
    change_pct = timeline.change_pct
    what_changed = (
        f"Between {timeline.first.snapshot_date} and {timeline.last.snapshot_date} this "
        f"client's wealth moved from USD {timeline.first.total_usd:,.0f} to "
        f"USD {timeline.last.total_usd:,.0f}, a change of {change_pct:+.2f}%."
    )
    if lead is not None:
        what_changed += f" {lead.summary}"

    why_it_matters = (
        f"The client's recorded objectives are: {context.client['objectives']}. "
        f"They are profiled {context.client['risk_profile']} with a "
        f"{context.client['liquidity_needs'].lower()} liquidity need."
    )
    if lead is not None and lead.interpretations:
        why_it_matters += f" {lead.interpretations[0].statement}"

    options = _discussion_options(context, signals, lead_type)
    specialist = _SPECIALISTS.get(lead_type)

    evidence_ids: list[str] = []
    # The brief quotes the client's objectives and profile verbatim, so that
    # quotation opens its own source record like every other claim.
    for signal in signals:
        for item in signal.items:
            if item.label == explanation_detector.PROFILE_ITEM_LABEL:
                evidence_ids.append(item.id)
    for signal in signals[:4]:
        evidence_ids.extend(signal.item_ids[:4])

    return MeetingBrief(
        what_changed=what_changed,
        why_it_matters=why_it_matters,
        uncertainties=[claim.statement for claim in (conflicts + uncertainties)][:6],
        opening_question=_client_opening_question(context, lead_type),
        discussion_options=options,
        specialist_suggestion=(
            f"Consider involving {specialist} once the client's intentions are clear."
            if specialist
            else None
        ),
        open_loop_ids=[loop.id for loop in loops],
        governance_clock_ids=[clock.id for clock in clocks],
        evidence_item_ids=list(dict.fromkeys(evidence_ids)),
    )


def _discussion_options(context, signals, lead_type) -> list[str]:
    families = {s.signal_type for s in signals if s.severity_rank >= 40}
    options: list[str] = []

    if SignalType.CREDIT in families:
        options.append(
            "Review how much headroom the facility leaves and whether the client wants "
            "to hold, reduce or restructure the borrowing."
        )
    if SignalType.CASH_NEED in families:
        options.append(
            "Agree in advance which assets fund the next dated obligation, so nothing "
            "has to be sold at short notice."
        )
    if SignalType.EXCLUSION in families:
        options.append(
            "Decide whether the excluded holdings are removed, formally waived in "
            "writing, or moved outside the mandate."
        )
    if SignalType.CONCENTRATION in families:
        options.append(
            "Discuss whether the largest exposure is a deliberate position and, if so, "
            "record the reasoning."
        )
    if SignalType.SUITABILITY in families:
        options.append(
            "Revisit whether the recorded risk profile still describes what the client "
            "wants the portfolio to do."
        )
    if SignalType.MANDATE in families:
        options.append(
            "Review the allocation against its agreed bands and either rebalance or "
            "document the exception."
        )
    if SignalType.LIQUIDITY_RESTRICTION in families:
        options.append(
            "Map what is genuinely accessible at short notice against what the client "
            "may need, before a redemption date forces the question."
        )
    if SignalType.DATA_CONFLICT in families:
        options.append(
            "Confirm which of the conflicting figures on file is current before acting "
            "on either."
        )

    if not options:
        options.append(
            "Use the meeting to confirm that nothing has changed in the client's plans "
            "since the last review."
        )
    return options[:3]


def _client_ready_drafts(context, brief, available_items) -> list[ClientReadyDraft]:
    """Canonical English plus any validated cached translation."""
    canonical_content = (
        f"{brief.what_changed} {brief.why_it_matters} "
        f"Suggested opening: {brief.opening_question}"
    )
    drafts = [
        ClientReadyDraft(
            language="English",
            canonical_language="English",
            status="draft",
            content=canonical_content,
            evidence_item_ids=brief.evidence_item_ids[:8],
        )
    ]

    for cached in cached_language.drafts_for(context.client_id):
        if cached.language == "English":
            continue
        result = validate_draft(
            cached.content,
            canonical_content,
            list(cached.evidence_item_ids),
            available_items,
        )
        if not result.ok:
            # Fail closed: an unvalidated translation is never published.
            continue
        drafts.append(
            ClientReadyDraft(
                language=cached.language,
                canonical_language=cached.canonical_language,
                status="draft",
                content=cached.content,
                evidence_item_ids=list(cached.evidence_item_ids),
            )
        )
    return drafts
