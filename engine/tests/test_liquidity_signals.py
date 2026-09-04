"""Eligible Liquidity: timing rules, currency conversion and restrictions."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from jb_clarity.calculations.fx import FxTable
from jb_clarity.calculations.liquidity import (
    RESTRICTED_TIERS,
    assess_eligible_liquidity,
)
from jb_clarity.ingestion.normalization import (
    CashNeedOccurrence,
    normalise_certainty,
    occurrences,
)

AS_OF = date(2026, 8, 26)


def _holdings(**tiers: float) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"liquidity_tier": tier, "market_value_usd": value}
            for tier, value in tiers.items()
        ]
    )


def _need(days: int, amount: float = 1_000_000.0, currency: str = "USD") -> CashNeedOccurrence:
    due = date.fromordinal(AS_OF.toordinal() + days)
    return CashNeedOccurrence(
        need_id="CN-TEST",
        client_id="CL-TEST",
        description="Test obligation",
        currency=currency,
        amount=amount,
        certainty="Confirmed",
        recurrence="One-off",
        window_from=due,
        window_to=due,
        next_due=due,
        days_remaining=days,
        in_open_window=False,
    )


@pytest.fixture(scope="module")
def fx(challenge_data) -> FxTable:
    return FxTable.from_market(challenge_data.market, "2026-08-26")


def test_daily_holdings_always_count(fx):
    result = assess_eligible_liquidity(_holdings(Daily=2_000_000.0), _need(1), fx)
    assert result.eligible_amount == pytest.approx(2_000_000.0)
    assert result.is_fully_covered


def test_weekly_needs_fourteen_days_notice(fx):
    early = assess_eligible_liquidity(_holdings(Weekly=2_000_000.0), _need(13), fx)
    assert early.eligible_amount == 0.0
    assert "Weekly" in early.excluded_by_timing

    ready = assess_eligible_liquidity(_holdings(Weekly=2_000_000.0), _need(14), fx)
    assert ready.eligible_amount == pytest.approx(2_000_000.0)


def test_monthly_needs_forty_five_days_notice(fx):
    early = assess_eligible_liquidity(_holdings(Monthly=2_000_000.0), _need(44), fx)
    assert early.eligible_amount == 0.0

    ready = assess_eligible_liquidity(_holdings(Monthly=2_000_000.0), _need(45), fx)
    assert ready.eligible_amount == pytest.approx(2_000_000.0)


def test_gated_and_illiquid_never_count_toward_guaranteed_coverage(fx):
    holdings = pd.DataFrame(
        [
            {"liquidity_tier": "Quarterly Gate", "market_value_usd": 5_000_000.0},
            {"liquidity_tier": "Illiquid", "market_value_usd": 5_000_000.0},
        ]
    )
    result = assess_eligible_liquidity(holdings, _need(365), fx)
    assert result.eligible_amount == 0.0
    assert set(result.restricted_by_tier) == set(RESTRICTED_TIERS)
    assert result.restricted_total == pytest.approx(10_000_000.0)


def test_unknown_tier_is_treated_as_restricted_not_available(fx):
    holdings = pd.DataFrame(
        [{"liquidity_tier": "Fortnightly", "market_value_usd": 1_000_000.0}]
    )
    result = assess_eligible_liquidity(holdings, _need(90), fx)
    assert result.eligible_amount == 0.0
    assert "Fortnightly" in result.restricted_by_tier


def test_conversion_follows_the_quoted_direction(fx):
    """USDSGD is SGD per USD, so USD buys more SGD, not fewer."""
    result = assess_eligible_liquidity(
        _holdings(Daily=1_000_000.0), _need(1, amount=1.0, currency="SGD"), fx
    )
    assert result.eligible_amount == pytest.approx(1_352_000.0)


def test_eur_conversion_uses_usd_per_eur(fx):
    result = assess_eligible_liquidity(
        _holdings(Daily=1_092_000.0), _need(1, amount=1.0, currency="EUR"), fx
    )
    assert result.eligible_amount == pytest.approx(1_000_000.0, rel=1e-6)


def test_fx_assumptions_are_always_stated(fx):
    result = assess_eligible_liquidity(
        _holdings(Daily=1_000.0), _need(1, currency="HKD"), fx
    )
    assert any("HKD" in assumption for assumption in result.fx_assumptions)
    assert any("Daily" in assumption for assumption in result.fx_assumptions)


def test_shortfall_is_reported_when_cover_is_incomplete(fx):
    result = assess_eligible_liquidity(
        _holdings(Daily=400_000.0), _need(10, amount=1_000_000.0), fx
    )
    assert not result.is_fully_covered
    assert result.shortfall == pytest.approx(600_000.0)
    assert result.coverage_pct == pytest.approx(40.0)


def test_recurring_needs_resolve_to_their_next_occurrence(challenge_data):
    resolved = {o.need_id: o for o in occurrences(challenge_data.cash_needs, AS_OF)}
    # An annual draw that started in January next falls due the following January.
    cheung = resolved["CN-012"]
    assert cheung.next_due == date(2027, 1, 1)
    assert cheung.days_remaining == 128
    # A dated one-off keeps its own date.
    margarethe = resolved["CN-004"]
    assert margarethe.next_due == date(2026, 10, 1)
    assert margarethe.days_remaining == 36


def test_certainty_phrases_are_normalised_conservatively():
    assert normalise_certainty("Confirmed") == "Confirmed"
    assert normalise_certainty("Likely") == "Likely"
    assert normalise_certainty("Aspirational") == "Aspirational"
    assert normalise_certainty("Conditional on the sale completing") == "Conditional"
    assert normalise_certainty(None) == "Conditional"
    assert normalise_certainty("something unrecognised") == "Conditional"


def test_overlapping_claims_on_one_pool_are_named(cases_by_client, packets_by_client):
    """Two obligations in the same window cannot both use the same assets."""
    packets = {p.signal_type: p for p in packets_by_client["CL-0017"]}
    statements = " ".join(c.statement for c in packets["cash-need"].uncertainties)
    assert "overlap" in statements.lower()


def test_gated_holdings_are_surfaced_without_being_called_worthless(packets_by_client):
    packets = {p.signal_type: p for p in packets_by_client["CL-0006"]}
    restriction = packets["liquidity-restriction"]
    text = " ".join(c.statement for c in restriction.interpretations)
    assert "gate" in text.lower()
    assert "not worthless" in text.lower()
