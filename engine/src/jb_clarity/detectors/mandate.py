"""Mandate governance: band drift, position limits and binding exclusions.

A breach with an evidenced client direction is a different conversation from an
unexplained one, so waivers found in the RM notes are surfaced beside the
breach. They never erase it.
"""

from __future__ import annotations

import re

from jb_clarity.calculations.mandate import BandBreach, ExclusionBreach, PositionBreach
from jb_clarity.domain.enums import (
    CaseStatus,
    SafetyOverrideRuleId,
    ScoringFactor,
    SignalType,
)
from jb_clarity.domain.models import Measure
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder
from jb_clarity.ingestion.loader import RmNote
from jb_clarity.ingestion.normalization import excerpt

MANDATES_FILE = "mandates.csv"
NOTES_FILE = "rm_notes.json"

_WAIVER_PATTERNS = (
    re.compile(r"waiver", re.IGNORECASE),
    re.compile(r"confirmed the instruction in writing", re.IGNORECASE),
    re.compile(r"client[- ]directed", re.IGNORECASE),
    re.compile(r"acknowledged (this|the point) and (confirmed|proceeded)", re.IGNORECASE),
)

# Words that tie a note to the asset class it is talking about.
_ASSET_CLASS_HINTS = {
    "Commodities": ("commodit", "gold", "bullion"),
    "Equity": ("equity", "shares", "stock"),
    "Fixed Income": ("bond", "fixed income", "duration"),
    "Alternatives": ("alternative", "private", "hedge fund", "property"),
    "Cash and Equivalents": ("cash", "deposit"),
    "Structured Products": ("structured", "note", "accumulator", "fcn"),
}


def find_waiver(notes: list[RmNote], hints: tuple[str, ...]) -> RmNote | None:
    """The most recent note that both waives something and names this subject."""
    candidates = [
        note
        for note in notes
        if any(pattern.search(note.note) for pattern in _WAIVER_PATTERNS)
        and any(hint in note.note.lower() for hint in hints)
    ]
    return max(candidates, key=lambda n: (n.note_date, n.note_id), default=None)


def detect(context) -> list[DetectedSignal]:
    assessment = context.mandates
    signals: list[DetectedSignal] = []

    if assessment.band_breaches or assessment.position_breaches:
        signals.append(_mandate_signal(context, assessment))
    if assessment.exclusion_breaches:
        signals.append(_exclusion_signal(context, assessment.exclusion_breaches))
    return signals


def _mandate_signal(context, assessment) -> DetectedSignal:
    settings = context.factor(ScoringFactor.THRESHOLD_HISTORY)
    builder = SignalBuilder(context.client_id, SignalType.MANDATE, status=CaseStatus.ACTIVE)

    contributions: list[tuple[float, str]] = []

    for breach in assessment.band_breaches:
        item = builder.item(
            f"band-{breach.portfolio_id}-{breach.asset_class}",
            f"{breach.mandate_code} {breach.asset_class} band",
            {
                "actualPct": round(breach.actual_pct, 4),
                "minPct": breach.min_pct,
                "targetPct": breach.target_pct,
                "maxPct": breach.max_pct,
                "portfolioId": breach.portfolio_id,
                "serviceModel": breach.service_model,
            },
            file=MANDATES_FILE,
            record_key=f"{breach.mandate_code}|{breach.asset_class}",
            field_name="min_pct|target_pct|max_pct",
        )
        builder.metric(
            f"band-{breach.portfolio_id}-{breach.asset_class}",
            f"{breach.asset_class} share of {breach.portfolio_id}",
            "asset class market value / portfolio market value x 100",
            {
                "assetClass": breach.asset_class,
                "portfolioId": breach.portfolio_id,
                "minPct": breach.min_pct,
                "maxPct": breach.max_pct,
            },
            Measure(value=round(breach.actual_pct, 4), unit="percent"),
            context.snapshot,
        )
        builder.fact(f"band-{breach.portfolio_id}-{breach.asset_class}", breach.summary, [item])

        waiver = find_waiver(context.notes, _ASSET_CLASS_HINTS.get(breach.asset_class, ()))
        points = min(
            settings["mandateBandBase"]
            + settings["mandateBandPerPctPoint"] * breach.gap_pct_points,
            float(settings["mandateBandCap"]),
        )
        reason = (
            f"{breach.asset_class} in {breach.portfolio_id} is "
            f"{breach.gap_pct_points:.2f} percentage points outside its mandate band."
        )
        if waiver is not None:
            waiver_item = builder.item(
                f"waiver-{waiver.note_id}",
                f"Evidenced client direction ({waiver.note_date.isoformat()})",
                excerpt(waiver.note),
                file=NOTES_FILE,
                record_key=waiver.note_id,
                field_name="note",
            )
            builder.interpretation(
                f"waiver-{breach.portfolio_id}-{breach.asset_class}",
                f"The {waiver.note_date.isoformat()} note records a client direction and a "
                f"waiver covering this {breach.asset_class.lower()} position. The breach "
                "still stands and is still reported; the note explains why it exists and "
                "who accepted it.",
                [item, waiver_item],
            )
            builder.deduct_confidence(
                "Whether a waiver still covers the current position size is read from a "
                "dated free-text note and needs confirmation.",
                context.config["confidence"]["deductions"]["freeTextNoteInterpretation"],
            )
            points *= float(settings["evidencedWaiverMultiplier"])
            reason += " A client direction and waiver are evidenced in the RM notes."
        contributions.append((points, reason))

    for breach in assessment.position_breaches:
        item = builder.item(
            f"position-{breach.portfolio_id}-{breach.instrument_id}",
            f"{breach.instrument_name} weight in {breach.portfolio_id}",
            {
                "weightPct": round(breach.weight_pct, 4),
                "limitPct": breach.limit_pct,
                "marketValue": {
                    "amount": breach.market_value_base,
                    "currency": breach.currency,
                },
            },
            file="holdings.csv",
            record_key=f"{breach.portfolio_id}|{breach.instrument_id}|{context.snapshot}",
            field_name="market_value_base",
        )
        builder.fact(
            f"position-{breach.portfolio_id}-{breach.instrument_id}", breach.summary, [item]
        )
        contributions.append(
            (
                min(
                    settings["positionLimitBase"]
                    + settings["positionLimitPerPctPoint"] * breach.gap_pct_points,
                    float(settings["positionLimitCap"]),
                ),
                f"{breach.instrument_name} exceeds the {breach.limit_pct:.0f}% "
                f"single-position limit in {breach.portfolio_id}.",
            )
        )

    builder.assumption(
        "custody",
        "Only Discretionary and Advisory portfolios are measured against a mandate. "
        "Custody accounts are not managed by the bank and are excluded from these "
        "tests, though they still count toward the client's total exposure.",
        [],
    )
    builder.assumption(
        "limit-scope",
        "The single-position limit is applied only to instruments the dataset marks "
        "with concentration_limit_applies, so diversified funds, sovereign bonds and "
        "deposits are not treated as single-name exposures.",
        [],
    )

    points, reason = _combine(contributions, context, ScoringFactor.THRESHOLD_HISTORY)
    if points:
        builder.score(ScoringFactor.THRESHOLD_HISTORY, points, reason)

    band_count = len(assessment.band_breaches)
    position_count = len(assessment.position_breaches)
    parts = []
    if band_count:
        parts.append(f"{band_count} allocation band break{'s' if band_count != 1 else ''}")
    if position_count:
        parts.append(
            f"{position_count} single-position limit break{'s' if position_count != 1 else ''}"
        )

    return builder.finish(
        summary=f"Managed portfolios show {' and '.join(parts)}.",
        time_horizon="current",
        severity_rank=50 + min(band_count + position_count, 10),
    )


def _exclusion_signal(context, breaches: list[ExclusionBreach]) -> DetectedSignal:
    settings = context.factor(ScoringFactor.THRESHOLD_HISTORY)
    builder = SignalBuilder(context.client_id, SignalType.EXCLUSION, status=CaseStatus.ACTIVE)

    item_ids = []
    for breach in breaches:
        item_ids.append(
            builder.item(
                f"excluded-{breach.instrument_id}",
                f"{breach.instrument_name} flagged as excluded",
                {
                    "weightPct": round(breach.weight_pct, 4),
                    "marketValue": {
                        "amount": breach.market_value_base,
                        "currency": breach.currency,
                    },
                    "portfolioId": breach.portfolio_id,
                },
                file="instruments.csv",
                record_key=breach.instrument_id,
                field_name="sustainability_excluded",
            )
        )
        builder.fact(f"excluded-{breach.instrument_id}", breach.summary, item_ids[-1:])

    mandate_item = builder.item(
        "mandate-notes",
        f"{breaches[0].mandate_code} binding exclusions",
        breaches[0].mandate_notes,
        file=MANDATES_FILE,
        record_key=breaches[0].mandate_code,
        field_name="mandate_notes",
    )

    waiver = find_waiver(context.notes, ("exclusion", "sustainab", "policy", "screen"))
    total = sum(b.market_value_base for b in breaches)
    currency = breaches[0].currency

    if waiver is None:
        builder.interpretation(
            "unwaived",
            f"{currency} {total:,.0f} is held in instruments the dataset flags as "
            f"excluded under the {breaches[0].mandate_code} mandate's binding "
            "exclusions, and the RM notes contain no waiver or client direction "
            "covering them. On the prototype's rules this is a compliance breach "
            "rather than allocation drift.",
            item_ids + [mandate_item],
        )
        builder.override(
            SafetyOverrideRuleId.UNWAIVED_BINDING_EXCLUSION,
            f"{len(breaches)} holding(s) fall inside the {breaches[0].mandate_code} "
            "mandate's binding exclusions with no evidenced waiver.",
        )
        points = float(settings["bindingExclusion"])
        reason = (
            f"{len(breaches)} unwaived holding(s) inside a binding mandate exclusion."
        )
    else:
        waiver_item = builder.item(
            f"waiver-{waiver.note_id}",
            f"Evidenced client direction ({waiver.note_date.isoformat()})",
            excerpt(waiver.note),
            file=NOTES_FILE,
            record_key=waiver.note_id,
            field_name="note",
        )
        builder.interpretation(
            "waived",
            "A dated note records a client direction covering these holdings. The "
            "breach is still reported; the note explains its origin.",
            item_ids + [waiver_item],
        )
        points = float(settings["bindingExclusion"]) * float(
            settings["evidencedWaiverMultiplier"]
        )
        reason = "Holdings inside a binding exclusion, with an evidenced client direction."

    builder.uncertainty(
        "screening",
        "Exclusion status is taken from the dataset's sustainability_excluded flag. "
        "The engine does not re-screen the underlying issuers.",
        [mandate_item],
    )
    builder.score(ScoringFactor.THRESHOLD_HISTORY, points, reason)

    holdings_phrase = "holding" if len(breaches) == 1 else "holdings"
    return builder.finish(
        summary=(
            f"The {breaches[0].mandate_code} mandate's binding exclusions cover "
            f"{len(breaches)} {holdings_phrase} worth {currency} {total:,.0f}."
        ),
        time_horizon="current",
        severity_rank=95 if waiver is None else 60,
    )


def _combine(
    contributions: list[tuple[float, str]], context, factor: ScoringFactor
) -> tuple[float, str]:
    """Highest contribution sets the base; the rest add a capped bonus."""
    if not contributions:
        return 0.0, ""
    settings = context.factor(factor)
    bonus = float(context.config["urgency"]["additionalContributionBonus"])
    contributions = sorted(contributions, key=lambda c: -c[0])
    total = contributions[0][0] + bonus * (len(contributions) - 1)
    total = min(total, float(settings["max"]))
    reason = contributions[0][1]
    if len(contributions) > 1:
        reason += f" A further {len(contributions) - 1} breach(es) add capped points."
    return total, reason
