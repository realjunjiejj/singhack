"""Regression facts for the demonstrated cases.

Every number here was recalculated from the supplied files rather than copied
from the brief, and is asserted at full precision.
"""

from __future__ import annotations

from datetime import date

import pytest


def _claims(case) -> str:
    return " ".join(
        claim.statement
        for claim in (*case.facts, *case.interpretations, *case.uncertainties)
    )


# --------------------------------------------------------------------------
# Hartono Wijaya Kusuma - CL-0001
# --------------------------------------------------------------------------


def test_hartono_facility_is_sgd_with_a_seventy_percent_trigger(challenge_data):
    facility = challenge_data.facilities.loc[
        challenge_data.facilities.facility_id == "CF-0005"
    ].iloc[0]
    assert facility["facility_ccy"] == "SGD"
    assert float(facility["margin_call_ltv_pct"]) == 70.0
    assert facility["client_id"] == "CL-0001"
    assert facility["collateral_portfolio_id"] == "PF-0002"


def test_hartono_breach_history_and_cure(challenge_data):
    facility = challenge_data.facilities.loc[
        challenge_data.facilities.facility_id == "CF-0005"
    ].iloc[0]
    expected = {
        "2025-12-31": 78.5006,
        "2026-02-27": 75.6758,
        "2026-03-31": 58.8618,
        "2026-06-30": 62.1793,
        "2026-08-26": 59.1481,
    }
    for snapshot, ltv in expected.items():
        calculated = (
            float(facility[f"drawn_{snapshot}"])
            / float(facility[f"lending_value_{snapshot}"])
            * 100.0
        )
        assert calculated == pytest.approx(ltv, abs=1e-3)
        # Borrowing never moved across the whole supplied history.
        assert float(facility[f"drawn_{snapshot}"]) == 8_000_000.0


def test_hartono_case_is_historical_resolved_not_current(cases_by_client, queue_by_client):
    case = cases_by_client["CL-0001"]
    assert case.status == "historical-resolved"
    assert queue_by_client["CL-0001"].status == "historical-resolved"
    assert case.urgency.safety_override is None, "a resolved breach is not Critical"
    assert case.urgency.tier != "Critical"


def test_hartono_conclusion_states_the_breach_is_resolved(cases_by_client):
    conclusion = cases_by_client["CL-0001"].conclusion.lower()
    assert "59.15" in conclusion
    assert "back below" in conclusion or "below it" in conclusion


def test_hartono_cure_is_attributed_to_collateral_not_repayment(cases_by_client):
    text = _claims(cases_by_client["CL-0001"])
    assert "8,000,000" in text
    assert "lending value" in text.lower()
    assert "not because of any recorded client action" in text


def test_hartono_current_values_are_exact(cases_by_client):
    case = cases_by_client["CL-0001"]
    scenarios = {s.id: s for s in case.collateral_stress_test.scenarios}
    base = scenarios["CF-0005-STRESS-BASE"]
    assert base.collateral_value.amount == pytest.approx(26_618_144.28, abs=0.01)
    assert base.collateral_value.currency == "SGD"
    assert base.lending_value.amount == pytest.approx(13_525_392.14, abs=0.01)
    assert base.drawn_amount.amount == 8_000_000.0
    assert base.ltv_pct == pytest.approx(59.15, abs=0.01)
    assert base.trigger_pct == 70.0
    assert base.status == "normal"


def test_hartono_fifteen_percent_down_scenario(cases_by_client):
    scenarios = {
        s.id: s for s in cases_by_client["CL-0001"].collateral_stress_test.scenarios
    }
    down = scenarios["CF-0005-STRESS-DOWN-15"]
    assert down.collateral_change_pct == -15
    assert down.ltv_pct == pytest.approx(69.59, abs=0.01)
    assert down.distance_to_trigger_pct_points == pytest.approx(0.41, abs=0.01)
    assert down.status == "near"
    assert down.drawn_amount.amount == 8_000_000.0


def test_hartono_energy_exposure_combines_direct_and_look_through(cases_by_client):
    text = _claims(cases_by_client["CL-0001"])
    assert "Bara Nusantara Energy" in text
    assert "44.99%" in text or "45.0" in text
    assert "worst-of" in text.lower() or "notional" in text.lower()


def test_hartono_property_need_and_family_constraint_are_surfaced(cases_by_client):
    case = cases_by_client["CL-0001"]
    text = _claims(case)
    assert "9,000,000" in text
    constraints = [loop for loop in case.open_loops if "constraint" in loop.summary]
    assert constraints
    assert "uncles" in constraints[0].source_excerpt


def test_hartono_timeline_covers_all_five_snapshots(cases_by_client):
    timeline = cases_by_client["CL-0001"].timeline
    assert [point.date.isoformat() for point in timeline] == [
        "2025-12-31",
        "2026-02-27",
        "2026-03-31",
        "2026-06-30",
        "2026-08-26",
    ]
    ltvs = [point.metrics["loanToValue"].value for point in timeline]
    assert ltvs == [78.5, 75.68, 58.86, 62.18, 59.15]


# --------------------------------------------------------------------------
# Cheung Kwok Wing - CL-0012
# --------------------------------------------------------------------------


def test_cheung_portfolio_decline_is_exact(cases_by_client):
    timeline = cases_by_client["CL-0012"].timeline
    assert timeline[0].metrics["totalValue"].value == pytest.approx(
        30_130_861.79, abs=0.01
    )
    assert timeline[-1].metrics["totalValue"].value == pytest.approx(
        28_028_704.71, abs=0.01
    )


def test_cheung_holds_a_2045_maturity(challenge_data):
    holdings = challenge_data.holdings_at("2026-08-26", "CL-0012")
    names = set(holdings["instrument_name"].astype(str))
    assert "US Treasury 2.375% due 2045" in names


def test_cheung_objective_and_obligation_conflict_is_preserved(
    cases_by_client, packets_by_client
):
    packets = {p.signal_type: p for p in packets_by_client["CL-0012"]}
    conflicts = " ".join(c.statement for c in packets["data-conflict"].conflicts)
    assert "1,100,000" in conflicts
    assert "1,280,000" in conflicts
    assert "does not choose between them" in conflicts


def test_cheung_conflict_reduces_confidence_without_reducing_urgency(cases_by_client):
    case = cases_by_client["CL-0012"]
    assert case.confidence.level == "Medium"
    assert any("disagree" in reason for reason in case.confidence.reasons)
    assert case.urgency.score > 0


def test_cheung_case_makes_no_life_expectancy_claim(cases_by_client):
    text = _claims(cases_by_client["CL-0012"]).lower()
    for phrase in ("life expectancy", "expected to live", "will not live", "mortality"):
        assert phrase not in text


def test_cheung_draw_is_linked_to_the_falling_portfolio(cases_by_client):
    text = _claims(cases_by_client["CL-0012"])
    assert "recurring draw" in text.lower()
    assert "6.98%" in text or "4.57%" in text


def test_cheung_decline_has_a_grounded_duration_explanation(
    cases_by_client, packets_by_client
):
    case = cases_by_client["CL-0012"]
    text = _claims(case).lower()
    assert "yield rises" in text or "yield reaches" in text
    assert "duration" in text
    assert "not a measured attribution" in text
    assert "rising yields" in case.conclusion.lower()
    assert "duration" in case.conclusion.lower()

    packets = {p.signal_type: p for p in packets_by_client["CL-0012"]}
    packet = packets["explanation"]
    assert any(
        item.source_reference.file == "event_log.csv" for item in packet.items
    )


# --------------------------------------------------------------------------
# Margarethe Voss-Brenner - CL-0003
# --------------------------------------------------------------------------


def test_margarethe_profile_versus_allocation(cases_by_client, challenge_data):
    client = challenge_data.client("CL-0003")
    assert client["risk_profile"] == "Conservative"
    assert float(client["risk_tolerance_score"]) == 2
    text = _claims(cases_by_client["CL-0003"])
    assert "Conservative" in text
    assert "71.46%" in text or "76.8" in text


def test_margarethe_inheritance_tax_need_is_confirmed_and_dated(cases_by_client):
    text = _claims(cases_by_client["CL-0003"])
    assert "3,400,000" in text
    assert "confirmed" in text.lower()
    assert "2026-10-01" in text


def test_margarethe_equity_band_breach_is_reported(packets_by_client):
    packets = {p.signal_type: p for p in packets_by_client["CL-0003"]}
    facts = " ".join(c.statement for c in packets["mandate"].facts)
    assert "Equity is 71.46% of PF-0005" in facts
    assert "30%" in facts


def test_margarethe_totals_reconcile_and_the_engine_says_so(
    validation_report, packets_by_client
):
    """The apparent 22.18m/20.31m gap is a denomination difference, not a conflict.

    EUR 20,312,395.29 at the 2026-08-26 EURUSD rate of 1.092 is exactly
    USD 22,181,135.66, so reporting a material disagreement would be wrong.
    """
    reconciliation = validation_report.reconciliations["CL-0003"]
    assert reconciliation.holdings_usd == pytest.approx(22_181_135.66, abs=0.05)
    assert reconciliation.client_record_usd == pytest.approx(22_181_135.66, abs=0.05)
    assert reconciliation.portfolio_record_usd == pytest.approx(22_181_135.66, abs=0.05)
    assert reconciliation.portfolio_base_currency_total == pytest.approx(
        20_312_395.29, abs=0.05
    )
    assert not reconciliation.is_material
    assert reconciliation.fx_explains_denomination_gap

    packets = {p.signal_type: p for p in packets_by_client["CL-0003"]}
    interpretations = " ".join(c.statement for c in packets["data-conflict"].interpretations)
    assert "20,312,395.29" in interpretations
    assert "base currency" in interpretations
    assert "manufacture a disagreement" in interpretations


def test_margarethe_relationship_context_does_not_become_a_score(cases_by_client):
    """Widowhood is conversation context, never a scoring factor."""
    case = cases_by_client["CL-0003"]
    factors = " ".join(c.factor + c.reason for c in case.factor_contributions).lower()
    for phrase in ("widow", "grief", "bereave", "husband", "spouse"):
        assert phrase not in factors


# --------------------------------------------------------------------------
# Supporting Book stories
# --------------------------------------------------------------------------


def test_nguyen_gated_credit_and_near_term_obligations(cases_by_client, packets_by_client):
    case = cases_by_client["CL-0006"]
    text = _claims(case)
    assert "5,000,000" in text and "2026-09-01" in text
    assert "3,000,000" in text and "2026-10-01" in text
    packets = {p.signal_type: p for p in packets_by_client["CL-0006"]}
    restriction = " ".join(
        c.statement for c in packets["liquidity-restriction"].interpretations
    )
    assert "Orchard Private Credit Fund II" in restriction


def test_nguyen_currency_mismatch_is_detected(cases_by_client):
    text = _claims(cases_by_client["CL-0006"])
    assert "denominated in USD" in text
    assert "daily-liquid assets" in text


def test_chalermchai_unanswered_deposit_question(cases_by_client):
    loops = cases_by_client["CL-0004"].open_loops
    matching = [loop for loop in loops if "deposits" in loop.source_excerpt.lower()]
    assert matching
    assert matching[0].note_date == date(2026, 8, 19)
    assert matching[0].confidence.level == "High"


def test_tan_boon_huat_succession_and_kyc(cases_by_client):
    case = cases_by_client["CL-0011"]
    loops = [loop for loop in case.open_loops if "raised again" in loop.summary]
    assert loops and "fourth attempt" in loops[0].source_excerpt.lower()
    clock = case.governance_clocks[0]
    assert clock.days_remaining == 5
    assert clock.status == "due-soon"


def test_lindqvist_deployment_agreed_but_unexecuted(cases_by_client):
    loops = cases_by_client["CL-0009"].open_loops
    matching = [loop for loop in loops if "raised again" in loop.summary]
    assert matching
    loop = matching[0]
    assert loop.note_date == date(2026, 3, 2)
    assert loop.confidence.level == "High"
    assert "attempt" in loop.source_excerpt.lower()


def test_near_trigger_facilities_are_found_generally(model, cases_by_client):
    """No client allowlist: near-trigger status comes from the data."""
    near = {
        case.client_id
        for case in model.client_cases
        for signal in case.anticipatory_signals
        if signal.type == "credit" and signal.status == "near"
    }
    assert near == {"CL-0002", "CL-0014"}


def test_recurring_obligation_larger_than_the_client_is_flagged(packets_by_client):
    """CN-007 read as annual instalments exceeds the client's whole wealth."""
    packets = {p.signal_type: p for p in packets_by_client["CL-0006"]}
    conflicts = " ".join(c.statement for c in packets["data-conflict"].conflicts)
    assert "CN-007" in conflicts
    assert "more than this client's entire wealth" in conflicts
