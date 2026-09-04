"""Credit facility signals: active, near, historical-resolved and normal."""

from __future__ import annotations

from jb_clarity.calculations.ltv import (
    LTV_FORMULA,
    NEAR_BAND_PCT_POINTS,
    FacilityState,
)
from jb_clarity.domain.enums import CaseStatus, SafetyOverrideRuleId, ScoringFactor, SignalType
from jb_clarity.domain.models import Measure
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder

FACILITIES_FILE = "credit_facilities.csv"

_SEVERITY = {
    CaseStatus.ACTIVE: 100,
    CaseStatus.NEAR: 80,
    CaseStatus.HISTORICAL_RESOLVED: 55,
    CaseStatus.NORMAL: 10,
}


def detect(context) -> list[DetectedSignal]:
    signals = []
    for facility in context.facilities:
        signals.append(_facility_signal(context, facility))
    return signals


def _facility_signal(context, facility: FacilityState) -> DetectedSignal:
    settings = context.factor(ScoringFactor.THRESHOLD_HISTORY)
    builder = SignalBuilder(
        context.client_id,
        SignalType.CREDIT,
        status=facility.status,
        discriminator=facility.facility_id,
    )

    trigger_item = builder.item(
        "trigger",
        f"{facility.facility_id} margin-call trigger",
        facility.trigger_pct,
        file=FACILITIES_FILE,
        record_key=facility.facility_id,
        field_name="margin_call_ltv_pct",
    )

    snapshot_items: dict[str, str] = {}
    for snapshot in facility.snapshots:
        snapshot_items[snapshot.snapshot_date] = builder.item(
            f"ltv-{snapshot.snapshot_date}",
            f"Loan-to-value at {snapshot.snapshot_date}",
            round(snapshot.ltv_pct, 4) if snapshot.lending_value_usable else None,
            file=FACILITIES_FILE,
            record_key=facility.facility_id,
            field_name=f"ltv_pct_{snapshot.snapshot_date}",
        )

    current = facility.current
    drawn_item = builder.item(
        "drawn",
        "Drawn amount",
        {"amount": current.drawn, "currency": facility.currency},
        file=FACILITIES_FILE,
        record_key=facility.facility_id,
        field_name=f"drawn_{current.snapshot_date}",
    )
    collateral_item = builder.item(
        "collateral",
        "Collateral market value and lending value",
        {
            "collateralMarketValue": {
                "amount": current.collateral_market_value,
                "currency": facility.currency,
            },
            "lendingValue": {"amount": current.lending_value, "currency": facility.currency},
        },
        file=FACILITIES_FILE,
        record_key=facility.facility_id,
        field_name=(
            f"collateral_market_value_{current.snapshot_date}|"
            f"lending_value_{current.snapshot_date}"
        ),
    )

    if current.lending_value_usable:
        builder.metric(
            "current-ltv",
            "Current loan-to-value",
            LTV_FORMULA,
            {
                "drawnAmount": current.drawn,
                "lendingValue": current.lending_value,
                "currency": facility.currency,
            },
            Measure(value=round(current.ltv_pct, 4), unit="percent"),
            current.snapshot_date,
        )
        builder.fact(
            "current",
            f"{facility.facility_id} is drawn {facility.currency} "
            f"{current.drawn:,.0f} against a lending value of {facility.currency} "
            f"{current.lending_value:,.2f}, a loan-to-value of {current.ltv_pct:.2f}% "
            f"against a {facility.trigger_pct:.0f}% margin-call trigger.",
            [drawn_item, collateral_item, snapshot_items[current.snapshot_date], trigger_item],
        )
        builder.assumption(
            "lending-value",
            "Loan-to-value is measured against lending value, which is market value "
            "after per-asset advance-rate haircuts, not against raw collateral "
            "market value.",
            [collateral_item],
        )
    else:
        builder.conflict(
            "no-lending-value",
            f"{facility.facility_id} has no usable lending value at "
            f"{current.snapshot_date}, so its loan-to-value cannot be calculated.",
            [collateral_item],
        )
        builder.deduct_confidence(
            "A facility lending value is missing or non-positive, so its "
            "loan-to-value could not be calculated.",
            context.config["confidence"]["deductions"]["missingCalculationInput"],
        )

    breaches = facility.historical_breaches
    if breaches:
        breach_ids = [snapshot_items[s.snapshot_date] for s in breaches]
        dates = ", ".join(
            f"{s.snapshot_date} ({s.ltv_pct:.2f}%)" for s in breaches
        )
        builder.fact(
            "historical",
            f"The {facility.trigger_pct:.0f}% trigger was exceeded at {dates}.",
            breach_ids + [trigger_item],
        )
        if facility.status == CaseStatus.HISTORICAL_RESOLVED:
            first_drawn = facility.snapshots[0].drawn
            if facility.drawn_unchanged_since_breach:
                builder.interpretation(
                    "cure",
                    f"Borrowing did not change across the supplied history: it remained "
                    f"{facility.currency} {first_drawn:,.0f} throughout. The ratio "
                    f"returned below the trigger because lending value from the "
                    f"collateral portfolio rose, not because of any recorded client action.",
                    [drawn_item, collateral_item] + breach_ids,
                )
                builder.uncertainty(
                    "cure-durability",
                    "A breach that resolved through collateral appreciation can return "
                    "if that appreciation reverses, because the borrowing was never "
                    "reduced.",
                    [drawn_item, collateral_item],
                )
            else:
                builder.interpretation(
                    "cure-mixed",
                    "The ratio returned below the trigger. Both the drawn amount and "
                    "the lending value moved over the period, so the cure cannot be "
                    "attributed to collateral appreciation alone.",
                    [drawn_item, collateral_item],
                )

    points, reason = _score(facility, settings)
    if points:
        builder.score(ScoringFactor.THRESHOLD_HISTORY, points, reason)

    if facility.status == CaseStatus.ACTIVE:
        builder.override(
            SafetyOverrideRuleId.ACTIVE_FACILITY_BREACH,
            f"{facility.facility_id} is at {current.ltv_pct:.2f}% loan-to-value, at or "
            f"above its {facility.trigger_pct:.0f}% margin-call trigger.",
        )

    summary = " ".join(facility.reasons)
    horizon = {
        CaseStatus.ACTIVE: "current",
        CaseStatus.NEAR: "current, with history",
        CaseStatus.HISTORICAL_RESOLVED: "historical, resolved at the current snapshot",
        CaseStatus.NORMAL: "current",
    }[facility.status]

    return builder.finish(
        summary=summary,
        time_horizon=horizon,
        severity_rank=_SEVERITY[facility.status],
    )


def _score(facility: FacilityState, settings: dict) -> tuple[float, str]:
    """Points for this facility's contribution to threshold urgency."""
    current = facility.current
    if not current.lending_value_usable:
        return 0.0, ""

    if facility.status == CaseStatus.ACTIVE:
        return (
            float(settings["facilityActiveBreach"]),
            f"{facility.facility_id} is at or above its margin-call trigger.",
        )

    if facility.status == CaseStatus.NEAR:
        near_band = NEAR_BAND_PCT_POINTS
        distance = max(current.distance_to_trigger_pct_points, 0.0)
        scaled = settings["facilityNearMax"] * (1.0 - min(distance / near_band, 1.0))
        points = max(scaled, float(settings["facilityNearFloor"]))
        reason = (
            f"{facility.facility_id} is {distance:.2f} percentage points below its "
            f"{facility.trigger_pct:.0f}% trigger."
        )
        if facility.historical_breaches:
            points = min(
                points + settings["nearAndHistoricalBonus"], float(settings["max"])
            )
            points = max(points, float(settings["facilityHistoricalResolved"]))
            reason += " It also breached the trigger earlier in the supplied history."
        elif facility.is_worsening:
            reason += (
                f" Loan-to-value rose {facility.trend_pct_points:.2f} percentage points "
                "over the latest interval."
            )
        return points, reason

    if facility.status == CaseStatus.HISTORICAL_RESOLVED:
        dates = ", ".join(s.snapshot_date for s in facility.historical_breaches)
        return (
            float(settings["facilityHistoricalResolved"]),
            f"{facility.facility_id} breached its trigger at {dates} and is now below it.",
        )

    return 0.0, ""
