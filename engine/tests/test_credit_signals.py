"""Facility loan-to-value states, boundaries and the bounded stress test."""

from __future__ import annotations

import pandas as pd
import pytest

from jb_clarity.calculations.ltv import (
    NEAR_BAND_PCT_POINTS,
    build_facility_state,
    stress_scenarios,
)
from jb_clarity.domain.enums import CaseStatus

SNAPSHOTS = ["2025-12-31", "2026-02-27", "2026-03-31", "2026-06-30", "2026-08-26"]


def _facility(challenge_data, facility_id: str):
    row = challenge_data.facilities.loc[
        challenge_data.facilities.facility_id == facility_id
    ].iloc[0]
    return build_facility_state(row, SNAPSHOTS)


def _synthetic(trigger: float, ltvs: list[float]) -> pd.Series:
    """A facility whose lending value is chosen to produce the given LTVs."""
    drawn = 1_000_000.0
    row = {
        "facility_id": "CF-TEST",
        "client_id": "CL-TEST",
        "collateral_portfolio_id": "PF-TEST",
        "facility_type": "Lombard Credit Facility",
        "facility_ccy": "USD",
        "credit_limit": 5_000_000.0,
        "margin_call_ltv_pct": trigger,
    }
    for snapshot, ltv in zip(SNAPSHOTS, ltvs):
        lending = drawn / (ltv / 100.0)
        row[f"drawn_{snapshot}"] = drawn
        row[f"lending_value_{snapshot}"] = lending
        row[f"collateral_market_value_{snapshot}"] = lending * 2
        row[f"ltv_pct_{snapshot}"] = ltv
    return pd.Series(row)


def test_ltv_is_measured_against_lending_value_not_market_value(challenge_data):
    state = _facility(challenge_data, "CF-0005")
    current = state.current
    assert current.drawn == 8_000_000.0
    assert current.lending_value == pytest.approx(13_525_392.14)
    assert current.collateral_market_value == pytest.approx(26_618_144.28)
    assert current.ltv_pct == pytest.approx(59.1481, abs=1e-4)
    # Against raw market value the ratio would look far safer than it is.
    assert current.drawn / current.collateral_market_value * 100 < 31


def test_recomputed_ltv_matches_the_supplied_column(challenge_data):
    for facility_id in challenge_data.facilities.facility_id:
        state = _facility(challenge_data, facility_id)
        for snapshot in state.snapshots:
            assert snapshot.ltv_pct == pytest.approx(snapshot.reported_ltv_pct, abs=0.01)


def test_active_breach_is_detected(challenge_data):
    state = build_facility_state(_synthetic(70.0, [50, 55, 60, 65, 72]), SNAPSHOTS)
    assert state.status == CaseStatus.ACTIVE


def test_exactly_at_the_trigger_counts_as_a_breach():
    state = build_facility_state(_synthetic(70.0, [50, 50, 50, 50, 70.0]), SNAPSHOTS)
    assert state.status == CaseStatus.ACTIVE


def test_near_is_within_the_configured_band():
    """A flat series isolates the band test from the worsening-trend rule."""
    just_inside = 70.0 - NEAR_BAND_PCT_POINTS + 0.1
    inside = build_facility_state(_synthetic(70.0, [just_inside] * 5), SNAPSHOTS)
    assert inside.status == CaseStatus.NEAR

    just_outside = 70.0 - NEAR_BAND_PCT_POINTS - 0.1
    outside = build_facility_state(_synthetic(70.0, [just_outside] * 5), SNAPSHOTS)
    assert outside.status == CaseStatus.NORMAL


def test_worsening_from_outside_the_band_is_still_near():
    state = build_facility_state(_synthetic(70.0, [30, 35, 40, 50, 58]), SNAPSHOTS)
    assert state.trend_pct_points == pytest.approx(8.0)
    assert state.status == CaseStatus.NEAR


def test_historical_resolved_requires_a_prior_breach_and_a_safe_present():
    state = build_facility_state(_synthetic(70.0, [78.5, 75.68, 58.86, 62.18, 59.15]), SNAPSHOTS)
    assert state.status == CaseStatus.HISTORICAL_RESOLVED
    assert [s.snapshot_date for s in state.historical_breaches] == [
        "2025-12-31",
        "2026-02-27",
    ]


def test_near_takes_precedence_over_a_historical_breach():
    """A facility that breached before and is close again reads as near."""
    state = build_facility_state(_synthetic(70.0, [76, 60, 60, 62, 68]), SNAPSHOTS)
    assert state.status == CaseStatus.NEAR
    assert state.historical_breaches, "history must still be retained"


def test_missing_lending_value_produces_no_ratio_rather_than_a_wrong_one():
    row = _synthetic(70.0, [50, 50, 50, 50, 50])
    row["lending_value_2026-08-26"] = 0.0
    state = build_facility_state(row, SNAPSHOTS)
    assert state.current.lending_value_usable is False
    assert state.status == CaseStatus.NORMAL


def test_supplied_book_has_no_active_breach_today(challenge_data):
    """Today's book is genuinely clear of live margin calls."""
    statuses = {
        facility_id: _facility(challenge_data, facility_id).status
        for facility_id in challenge_data.facilities.facility_id
    }
    assert CaseStatus.ACTIVE not in statuses.values()
    assert statuses["CF-0005"] == CaseStatus.HISTORICAL_RESOLVED
    assert statuses["CF-0002"] == CaseStatus.NEAR
    assert statuses["CF-0001"] == CaseStatus.NEAR
    assert statuses["CF-0003"] == CaseStatus.NORMAL
    assert statuses["CF-0004"] == CaseStatus.NORMAL


def test_stress_scenarios_hold_borrowing_constant(challenge_data):
    state = _facility(challenge_data, "CF-0005")
    base, down = stress_scenarios(state, (0, -15))
    assert base.drawn == down.drawn == 8_000_000.0
    assert base.ltv_pct == pytest.approx(59.15, abs=0.01)
    assert down.collateral_value == pytest.approx(22_625_422.64, abs=0.01)
    assert down.lending_value == pytest.approx(11_496_583.32, abs=0.01)
    assert down.ltv_pct == pytest.approx(69.59, abs=0.01)
    assert down.distance_to_trigger_pct_points == pytest.approx(0.41, abs=0.01)
    assert down.status == CaseStatus.NEAR


def test_stress_test_is_labelled_as_a_calculation_not_a_forecast(cases_by_client):
    stress = cases_by_client["CL-0001"].collateral_stress_test
    assert stress is not None
    assert stress.forecast is False
    assert "not a forecast" in stress.label.lower()


def test_clients_without_a_facility_have_no_stress_test(cases_by_client):
    assert cases_by_client["CL-0003"].collateral_stress_test is None
