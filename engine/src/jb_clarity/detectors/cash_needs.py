"""Obligations and whether they can actually be funded on time."""

from __future__ import annotations

from jb_clarity.calculations.liquidity import EligibleLiquidity
from jb_clarity.domain.enums import (
    CaseStatus,
    SafetyOverrideRuleId,
    ScoringFactor,
    SignalType,
)
from jb_clarity.domain.models import Measure
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder
from jb_clarity.ingestion.normalization import CashNeedOccurrence

NEEDS_FILE = "planned_cash_needs.csv"
COMMITMENTS_FILE = "commitments.csv"
COVERAGE_FORMULA = "eligible liquidity / obligation amount x 100"


def detect(context) -> list[DetectedSignal]:
    signals: list[DetectedSignal] = []
    liquidity_by_need = {item.need_id: item for item in context.liquidity}

    for occurrence in context.occurrences:
        if occurrence.days_remaining < 0:
            continue
        assessment = liquidity_by_need.get(occurrence.need_id)
        if assessment is None:
            continue
        signals.append(_need_signal(context, occurrence, assessment))

    commitment_signal = _commitments_signal(context)
    if commitment_signal is not None:
        signals.append(commitment_signal)
    return signals


def _need_signal(
    context, occurrence: CashNeedOccurrence, assessment: EligibleLiquidity
) -> DetectedSignal:
    horizon_days = context.config["liquidity"]["safetyOverrideHorizonDays"]
    covered = assessment.is_fully_covered
    status = CaseStatus.ACTIVE if (not covered and occurrence.days_remaining <= horizon_days) else (
        CaseStatus.NEAR if occurrence.days_remaining <= horizon_days else CaseStatus.NORMAL
    )

    builder = SignalBuilder(
        context.client_id,
        SignalType.CASH_NEED,
        status=status,
        discriminator=occurrence.need_id,
    )

    need_item = builder.item(
        "need",
        f"Planned cash need {occurrence.need_id}",
        {
            "description": occurrence.description,
            "amount": occurrence.amount,
            "currency": occurrence.currency,
            "certainty": occurrence.certainty,
            "recurrence": occurrence.recurrence,
            "dueFrom": occurrence.window_from.isoformat(),
            "dueTo": occurrence.window_to.isoformat(),
        },
        file=NEEDS_FILE,
        record_key=occurrence.need_id,
    )
    eligible_item = builder.item(
        "eligible",
        "Eligible Liquidity by liquidity tier",
        {
            "eligibleByTier": assessment.eligible_by_tier,
            "restrictedByTier": assessment.restricted_by_tier,
            "excludedByTiming": assessment.excluded_by_timing,
            "eligibleAmount": {
                "amount": assessment.eligible_amount,
                "currency": assessment.currency,
            },
        },
        file="holdings.csv",
        record_key=f"{context.client_id}|{context.snapshot}",
        field_name="liquidity_tier|market_value_usd",
    )

    builder.metric(
        f"coverage-{occurrence.need_id}",
        "Eligible Liquidity coverage",
        COVERAGE_FORMULA,
        {
            "eligibleLiquidity": assessment.eligible_amount,
            "obligationAmount": occurrence.amount,
            "currency": occurrence.currency,
            "daysRemaining": occurrence.days_remaining,
        },
        Measure(value=round(assessment.coverage_pct, 2), unit="percent"),
        context.snapshot,
    )

    builder.fact(
        "due",
        f"{occurrence.description} of {occurrence.currency} {occurrence.amount:,.0f} is "
        f"recorded as {occurrence.certainty.lower()} and next falls due on "
        f"{occurrence.next_due.isoformat()}, {occurrence.days_remaining} days from the "
        f"as-of date.",
        [need_item],
    )
    builder.fact(
        "coverage",
        _coverage_sentence(occurrence, assessment),
        [eligible_item, need_item],
    )

    for assumption in assessment.fx_assumptions:
        builder.assumption("policy", assumption, [eligible_item])

    if assessment.restricted_total:
        builder.uncertainty(
            "restricted",
            f"A further USD {assessment.restricted_total:,.0f} sits in gated or "
            "illiquid holdings. It is part of the client's wealth but is not counted "
            "as guaranteed funding for this obligation.",
            [eligible_item],
        )

    if assessment.excluded_by_timing:
        excluded = ", ".join(
            f"{tier} (USD {value:,.0f})"
            for tier, value in sorted(assessment.excluded_by_timing.items())
        )
        builder.uncertainty(
            "timing",
            f"{excluded} could not settle inside the {occurrence.days_remaining} days "
            "remaining under the prototype notice rules.",
            [eligible_item],
        )

    if assessment.has_shared_pool:
        builder.uncertainty(
            "overlap",
            "The same liquid assets are also counted toward "
            f"{', '.join(assessment.competing_need_ids)}. Each obligation is assessed "
            "against the whole eligible pool, so these coverages overlap and cannot all "
            "be met from the same assets.",
            [eligible_item],
        )

    if assessment.fx_incomplete:
        builder.deduct_confidence(
            "A direct currency pair for this obligation is not supplied, so the "
            "conversion relies on a USD pivot.",
            context.config["confidence"]["deductions"]["missingFxPair"],
        )

    if not covered:
        builder.interpretation(
            "shortfall",
            f"On these rules the obligation is short by {occurrence.currency} "
            f"{assessment.shortfall:,.0f}. Meeting it in full would require selling "
            "assets that cannot settle in time, drawing credit, or moving the date.",
            [eligible_item, need_item],
        )

    if (
        occurrence.is_confirmed
        and occurrence.days_remaining <= horizon_days
        and not covered
    ):
        builder.override(
            SafetyOverrideRuleId.UNCOVERED_NEAR_OBLIGATION,
            f"{occurrence.description} of {occurrence.currency} "
            f"{occurrence.amount:,.0f} is confirmed, falls due in "
            f"{occurrence.days_remaining} days, and Eligible Liquidity covers only "
            f"{assessment.coverage_pct:.0f}% of it.",
        )

    points, reason = _score(context, occurrence)
    if points:
        builder.score(ScoringFactor.TIME_URGENCY, points, reason)

    severity = _severity(occurrence, covered, horizon_days)

    return builder.finish(
        summary=(
            f"{occurrence.description}: {occurrence.currency} {occurrence.amount:,.0f} "
            f"{occurrence.certainty.lower()}, due in {occurrence.days_remaining} days, "
            + (
                "fully covered by assets that can settle in time."
                if covered
                else f"only {assessment.coverage_pct:.0f}% covered by assets that can "
                "settle in time."
            )
        ),
        time_horizon=f"{occurrence.days_remaining} days",
        days_remaining=occurrence.days_remaining,
        severity_rank=int(severity),
    )


def _severity(
    occurrence: CashNeedOccurrence, covered: bool, horizon_days: int
) -> int:
    """How strongly this obligation competes to lead the Client Case."""
    if not covered and occurrence.days_remaining <= horizon_days:
        return 90
    if occurrence.days_remaining <= 30:
        return 60
    if occurrence.days_remaining <= horizon_days:
        return 45
    if occurrence.days_remaining <= 180:
        return 30
    return 20


def _coverage_sentence(occurrence: CashNeedOccurrence, assessment: EligibleLiquidity) -> str:
    """Coverage stated in plain terms.

    Above full coverage a raw percentage reads oddly, so the multiple is given
    instead. The exact percentage stays in the derived metric either way.
    """
    if assessment.is_fully_covered:
        multiple = (
            assessment.eligible_amount / occurrence.amount if occurrence.amount else 0.0
        )
        return (
            f"Assets that can settle within {occurrence.days_remaining} days cover the "
            f"obligation in full — {occurrence.currency} "
            f"{assessment.eligible_amount:,.0f} against {occurrence.currency} "
            f"{occurrence.amount:,.0f}, or {multiple:.1f} times the amount required."
        )
    return (
        f"Assets that can settle within {occurrence.days_remaining} days cover only "
        f"{assessment.coverage_pct:.0f}% of the obligation ({occurrence.currency} "
        f"{assessment.eligible_amount:,.0f} against {occurrence.currency} "
        f"{occurrence.amount:,.0f})."
    )


def _score(context, occurrence: CashNeedOccurrence) -> tuple[float, str]:
    settings = context.factor(ScoringFactor.TIME_URGENCY)
    points = float(settings["beyondBandPoints"])
    band_label = "beyond 180 days"
    for band in settings["confirmedBands"]:
        if occurrence.days_remaining <= band["withinDays"]:
            points = float(band["points"])
            band_label = f"within {band['withinDays']} days"
            break

    multiplier = float(
        settings["certaintyMultipliers"].get(occurrence.certainty, 0.3)
    )
    scored = min(points * multiplier, float(settings["max"]))
    reason = (
        f"{occurrence.need_id} is {occurrence.certainty.lower()} and falls due "
        f"{band_label} ({occurrence.days_remaining} days)."
    )
    if multiplier < 1.0:
        reason += (
            f" A {occurrence.certainty.lower()} need carries "
            f"{multiplier:.0%} of the confirmed weighting."
        )
    return scored, reason


def _commitments_signal(context) -> DetectedSignal | None:
    """Uncalled private-markets commitments are future obligations, not cash."""
    commitments = context.data.client_commitments(context.client_id)
    if commitments.empty:
        return None

    builder = SignalBuilder(
        context.client_id, SignalType.CASH_NEED, status=CaseStatus.NORMAL,
        discriminator="COMMITMENTS",
    )
    total_uncalled = 0.0
    item_ids = []
    for _, row in commitments.iterrows():
        uncalled = float(row["uncalled"])
        total_uncalled += uncalled
        item_ids.append(
            builder.item(
                str(row["commitment_id"]),
                f"{row['fund_name']} uncalled commitment",
                {
                    "committed": float(row["committed"]),
                    "calledToDate": float(row["called_to_date"]),
                    "uncalled": uncalled,
                    "currency": str(row["currency"]),
                    "expectedCallWindow": str(row["expected_call_window"]),
                },
                file=COMMITMENTS_FILE,
                record_key=str(row["commitment_id"]),
            )
        )

    currency = str(commitments.iloc[0]["currency"])
    builder.fact(
        "uncalled",
        f"{currency} {total_uncalled:,.0f} of private-markets commitments remain "
        f"uncalled across {len(commitments)} fund(s).",
        item_ids,
    )
    builder.assumption(
        "not-cash",
        "Uncalled commitments are obligations that may be drawn inside their stated "
        "window. They are not treated as a dated cash need until the manager calls "
        "them, and they are never counted as available liquidity.",
        item_ids,
    )
    return builder.finish(
        summary=(
            f"{currency} {total_uncalled:,.0f} of uncalled private-markets commitments "
            "may be called inside their stated windows."
        ),
        time_horizon="within the stated call windows",
        severity_rank=25,
    )
