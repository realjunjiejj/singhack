"""Evidence Packet construction.

One packet per client and signal family. A packet is the only thing an
optional language model is ever shown, so it has to be complete on its own:
facts, interpretations, uncertainties, conflicts, assumptions, the metrics
behind them, and the source record for every item.
"""

from __future__ import annotations

from datetime import date

from jb_clarity.domain.enums import CaseStatus, GuidedAction, SignalType
from jb_clarity.domain.models import EvidencePacket, FactorContribution
from jb_clarity.evidence import ids
from jb_clarity.evidence.claims import DetectedSignal

_STATUS_SEVERITY = {
    CaseStatus.ACTIVE: 3,
    CaseStatus.NEAR: 2,
    CaseStatus.HISTORICAL_RESOLVED: 1,
    CaseStatus.NORMAL: 0,
}

PACKET_ACTIONS = [
    GuidedAction.EXPLAIN,
    GuidedAction.SHOW_EVIDENCE,
    GuidedAction.PREPARE_CONVERSATION,
    GuidedAction.REQUEST_INFORMATION,
    GuidedAction.INVOLVE_SPECIALIST,
]


def most_severe(statuses: list[CaseStatus]) -> CaseStatus:
    if not statuses:
        return CaseStatus.NORMAL
    return max(statuses, key=lambda s: _STATUS_SEVERITY[s])


def build_packets(
    client_id: str, signals: list[DetectedSignal], as_of: date
) -> list[EvidencePacket]:
    """Group a client's signals into one packet per signal family."""
    grouped: dict[SignalType, list[DetectedSignal]] = {}
    for signal in signals:
        grouped.setdefault(signal.signal_type, []).append(signal)

    packets: list[EvidencePacket] = []
    case = ids.case_id(client_id)

    for signal_type in sorted(grouped, key=str):
        members = sorted(grouped[signal_type], key=lambda s: s.signal_id)
        status = most_severe([m.status for m in members])

        urgency_inputs = [
            FactorContribution(
                factor=str(member.factor),
                points=round(member.points, 2),
                reason=member.points_reason,
                evidence_item_ids=member.item_ids[:12],
            )
            for member in members
            if member.factor is not None and member.points > 0
        ]

        confidence_inputs = sorted(
            {
                deduction.reason
                for member in members
                for deduction in member.confidence_deductions
            }
        )
        if not confidence_inputs:
            confidence_inputs = ["All claims in this packet resolve to a supplied record."]

        packets.append(
            EvidencePacket(
                packet_id=ids.packet_id(client_id, signal_type),
                case_id=case,
                client_id=client_id,
                as_of_date=as_of,
                signal_type=str(signal_type),
                status=status,
                facts=[claim for member in members for claim in member.facts],
                interpretations=[
                    claim for member in members for claim in member.interpretations
                ],
                uncertainties=[
                    claim for member in members for claim in member.uncertainties
                ],
                conflicts=[claim for member in members for claim in member.conflicts],
                assumptions=[claim for member in members for claim in member.assumptions],
                urgency_inputs=urgency_inputs,
                confidence_inputs=confidence_inputs,
                derived_metrics=[
                    metric for member in members for metric in member.derived_metrics
                ],
                items=[item for member in members for item in member.items],
                allowed_guided_actions=list(PACKET_ACTIONS),
            )
        )

    return packets
