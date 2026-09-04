"""Credit facility loan-to-value calculations.

Loan-to-value is measured against **lending value** — market value after
per-asset advance-rate haircuts — never against raw collateral market value.
Using the raw value understates the ratio and would hide a breach.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from jb_clarity.domain.enums import CaseStatus

# Distance from the trigger, in percentage points, inside which a facility is
# reported as `near`.
NEAR_BAND_PCT_POINTS = 5.0
# Movement toward the trigger, in percentage points over the latest interval,
# that makes a facility `near` even from outside the band.
WORSENING_PCT_POINTS = 3.0

LTV_FORMULA = "drawn amount / lending value x 100"


@dataclass(frozen=True)
class FacilitySnapshot:
    snapshot_date: str
    drawn: float
    collateral_market_value: float
    lending_value: float
    ltv_pct: float
    reported_ltv_pct: float
    distance_to_trigger_pct_points: float
    breached: bool
    lending_value_usable: bool


@dataclass
class FacilityState:
    """One facility's full history and its status at the as-of date."""

    facility_id: str
    client_id: str
    collateral_portfolio_id: str
    facility_type: str
    currency: str
    credit_limit: float
    trigger_pct: float
    snapshots: list[FacilitySnapshot] = field(default_factory=list)
    status: CaseStatus = CaseStatus.NORMAL
    reasons: list[str] = field(default_factory=list)
    trend_pct_points: float = 0.0

    @property
    def current(self) -> FacilitySnapshot:
        return self.snapshots[-1]

    @property
    def historical_breaches(self) -> list[FacilitySnapshot]:
        """Breaches at any snapshot before the current one."""
        return [s for s in self.snapshots[:-1] if s.breached]

    @property
    def is_worsening(self) -> bool:
        return self.trend_pct_points >= WORSENING_PCT_POINTS

    @property
    def drawn_unchanged_since_breach(self) -> bool:
        """True when borrowing never moved across the supplied history."""
        drawn_values = {round(s.drawn, 2) for s in self.snapshots}
        return len(drawn_values) == 1


def build_facility_state(row: pd.Series, snapshot_dates: list[str]) -> FacilityState:
    """Recompute a facility's LTV at every snapshot and classify it."""
    trigger = float(row["margin_call_ltv_pct"])
    snapshots: list[FacilitySnapshot] = []

    for snapshot in snapshot_dates:
        drawn = float(row[f"drawn_{snapshot}"])
        collateral = float(row[f"collateral_market_value_{snapshot}"])
        lending = float(row[f"lending_value_{snapshot}"])
        usable = lending > 0
        ltv = (drawn / lending * 100.0) if usable else float("nan")
        snapshots.append(
            FacilitySnapshot(
                snapshot_date=snapshot,
                drawn=drawn,
                collateral_market_value=collateral,
                lending_value=lending,
                ltv_pct=ltv,
                reported_ltv_pct=float(row[f"ltv_pct_{snapshot}"]),
                distance_to_trigger_pct_points=(trigger - ltv) if usable else float("nan"),
                breached=bool(usable and ltv >= trigger),
                lending_value_usable=usable,
            )
        )

    state = FacilityState(
        facility_id=str(row["facility_id"]),
        client_id=str(row["client_id"]),
        collateral_portfolio_id=str(row["collateral_portfolio_id"]),
        facility_type=str(row["facility_type"]),
        currency=str(row["facility_ccy"]),
        credit_limit=float(row["credit_limit"]),
        trigger_pct=trigger,
        snapshots=snapshots,
    )

    if len(snapshots) >= 2 and snapshots[-1].lending_value_usable and snapshots[-2].lending_value_usable:
        state.trend_pct_points = snapshots[-1].ltv_pct - snapshots[-2].ltv_pct

    state.status, state.reasons = _classify(state)
    return state


def _classify(state: FacilityState) -> tuple[CaseStatus, list[str]]:
    current = state.current
    reasons: list[str] = []

    if not current.lending_value_usable:
        reasons.append(
            f"{state.facility_id} has no usable lending value at "
            f"{current.snapshot_date}, so its loan-to-value cannot be calculated."
        )
        return CaseStatus.NORMAL, reasons

    if current.breached:
        reasons.append(
            f"Current loan-to-value of {current.ltv_pct:.2f}% is at or above the "
            f"{state.trigger_pct:.0f}% margin-call trigger."
        )
        return CaseStatus.ACTIVE, reasons

    within_band = current.distance_to_trigger_pct_points <= NEAR_BAND_PCT_POINTS
    if within_band:
        reasons.append(
            f"Current loan-to-value of {current.ltv_pct:.2f}% sits "
            f"{current.distance_to_trigger_pct_points:.2f} percentage points below the "
            f"{state.trigger_pct:.0f}% trigger, inside the "
            f"{NEAR_BAND_PCT_POINTS:.0f}-point watch band."
        )
    elif state.is_worsening:
        reasons.append(
            f"Loan-to-value rose {state.trend_pct_points:.2f} percentage points over the "
            "latest interval, moving toward the trigger."
        )

    if within_band or state.is_worsening:
        if state.historical_breaches:
            reasons.append(
                "The facility also breached its trigger earlier in the supplied history."
            )
        return CaseStatus.NEAR, reasons

    if state.historical_breaches:
        breach_dates = ", ".join(s.snapshot_date for s in state.historical_breaches)
        reasons.append(
            f"The trigger was breached at {breach_dates}, and the current "
            f"loan-to-value of {current.ltv_pct:.2f}% is back below it."
        )
        return CaseStatus.HISTORICAL_RESOLVED, reasons

    reasons.append(
        f"Loan-to-value of {current.ltv_pct:.2f}% is "
        f"{current.distance_to_trigger_pct_points:.2f} percentage points below the trigger."
    )
    return CaseStatus.NORMAL, reasons


@dataclass(frozen=True)
class StressScenarioResult:
    """A what-if calculation, not a forecast."""

    scenario_id: str
    collateral_change_pct: float
    collateral_value: float
    lending_value: float
    drawn: float
    ltv_pct: float
    trigger_pct: float
    distance_to_trigger_pct_points: float
    status: CaseStatus


def stress_scenarios(
    state: FacilityState, changes_pct: tuple[float, ...]
) -> list[StressScenarioResult]:
    """Vary collateral value only; hold borrowing and advance rates constant.

    Because advance rates are held constant, lending value moves in proportion
    to collateral value. Nothing here predicts a market move.
    """
    current = state.current
    results: list[StressScenarioResult] = []
    for change in changes_pct:
        factor = 1.0 + change / 100.0
        collateral = current.collateral_market_value * factor
        lending = current.lending_value * factor
        ltv = (current.drawn / lending * 100.0) if lending > 0 else float("nan")
        distance = state.trigger_pct - ltv
        if ltv >= state.trigger_pct:
            status = CaseStatus.ACTIVE
        elif distance <= NEAR_BAND_PCT_POINTS:
            status = CaseStatus.NEAR
        else:
            status = CaseStatus.NORMAL
        label = "BASE" if change == 0 else f"{'DOWN' if change < 0 else 'UP'}-{abs(change):g}"
        results.append(
            StressScenarioResult(
                scenario_id=f"{state.facility_id}-STRESS-{label}",
                collateral_change_pct=change,
                collateral_value=collateral,
                lending_value=lending,
                drawn=current.drawn,
                ltv_pct=ltv,
                trigger_pct=state.trigger_pct,
                distance_to_trigger_pct_points=distance,
                status=status,
            )
        )
    return results
