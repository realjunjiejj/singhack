"""Urgency scoring.

The severest single Advisory Insight sets the base score. Independent signals
add capped escalation on top of it, so a compound situation ranks above a
simple one without ever diluting a severe issue by averaging it away.
"""

from __future__ import annotations

from dataclasses import dataclass

from jb_clarity.domain.enums import ScoringFactor, UrgencyTier
from jb_clarity.domain.models import FactorContribution, SafetyOverride, Urgency
from jb_clarity.evidence.claims import DetectedSignal
from jb_clarity.phrasing import count_noun

FACTOR_ORDER = (
    ScoringFactor.THRESHOLD_HISTORY,
    ScoringFactor.TIME_URGENCY,
    ScoringFactor.SUITABILITY_MISMATCH,
    ScoringFactor.RELATIONSHIP_SIGNAL,
    ScoringFactor.FINANCIAL_EXPOSURE,
)


@dataclass
class UrgencyResult:
    urgency: Urgency
    contributions: list[FactorContribution]


def exposure_contribution(total_usd: float, config: dict) -> FactorContribution:
    """Financial exposure banded against client wealth, from configuration."""
    settings = config["urgency"]["factors"][ScoringFactor.FINANCIAL_EXPOSURE]
    points = float(settings["bands"][-1]["points"])
    band_floor = 0.0
    for band in settings["bands"]:
        if total_usd >= float(band["atLeastUsd"]):
            points = float(band["points"])
            band_floor = float(band["atLeastUsd"])
            break
    return FactorContribution(
        factor=str(ScoringFactor.FINANCIAL_EXPOSURE),
        points=points,
        reason=(
            f"Client wealth of USD {total_usd:,.0f} falls in the configured band at or "
            f"above USD {band_floor:,.0f}."
        ),
        evidence_item_ids=[],
    )


def score_client(
    signals: list[DetectedSignal], total_usd: float, config: dict
) -> UrgencyResult:
    """Combine every signal's contribution into one visible Urgency score."""
    urgency_config = config["urgency"]
    bonus = float(urgency_config["additionalContributionBonus"])

    grouped: dict[str, list[DetectedSignal]] = {}
    for signal in signals:
        if signal.factor is None or signal.points <= 0:
            continue
        grouped.setdefault(str(signal.factor), []).append(signal)

    contributions: list[FactorContribution] = []
    for factor in FACTOR_ORDER:
        if factor == ScoringFactor.FINANCIAL_EXPOSURE:
            contributions.append(exposure_contribution(total_usd, config))
            continue

        members = grouped.get(str(factor), [])
        if not members:
            continue
        settings = urgency_config["factors"][str(factor)]
        members = sorted(members, key=lambda s: (-s.points, s.signal_id))
        points = members[0].points + bonus * (len(members) - 1)
        points = min(points, float(settings["max"]))
        reason = members[0].points_reason
        if len(members) > 1:
            reason += (
                f" A further {count_noun(len(members) - 1, 'independent signal')} "
                "in this factor adds capped points."
            )
        contributions.append(
            FactorContribution(
                factor=str(factor),
                points=round(points, 2),
                reason=reason,
                evidence_item_ids=sorted(
                    {item_id for member in members for item_id in member.item_ids}
                )[:12],
            )
        )

    if contributions:
        ordered = sorted(contributions, key=lambda c: -c.points)
        base = ordered[0].points
        escalation = min(
            sum(c.points for c in ordered[1:]),
            float(urgency_config["compoundEscalationCap"]),
        )
        score = min(base + escalation, float(urgency_config["maxScore"]))
    else:
        score = 0.0

    override = _safety_override(signals)
    if override is not None:
        tier = UrgencyTier.CRITICAL
    elif score >= float(urgency_config["highTierThreshold"]):
        tier = UrgencyTier.HIGH
    else:
        tier = UrgencyTier.WATCH

    return UrgencyResult(
        urgency=Urgency(tier=tier, score=round(score, 2), safety_override=override),
        contributions=contributions,
    )


def _safety_override(signals: list[DetectedSignal]) -> SafetyOverride | None:
    """The first override by rule identifier, so the result is deterministic."""
    overrides = [s.safety_override for s in signals if s.safety_override is not None]
    if not overrides:
        return None
    return sorted(overrides, key=lambda o: (o.rule_id, o.reason))[0]
