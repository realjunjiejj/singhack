"""Mandate applicability, exclusions, concentration and look-through."""

from __future__ import annotations

import pytest

from jb_clarity.calculations.exposure import build_client_exposure, parse_look_through
from jb_clarity.calculations.mandate import assess_client_mandates

SNAPSHOT = "2026-08-26"


def test_custody_accounts_are_excluded_from_mandate_tests(challenge_data):
    """CL-0002 holds a large custody position that no mandate governs."""
    assessment = assess_client_mandates(challenge_data, "CL-0002", SNAPSHOT)
    tested = {b.portfolio_id for b in assessment.band_breaches}
    tested |= {p.portfolio_id for p in assessment.position_breaches}
    assert "PF-0004" not in tested, "custody portfolio must not be measured"


def test_custody_still_counts_toward_client_exposure(challenge_data):
    exposure = build_client_exposure(challenge_data, "CL-0001", SNAPSHOT)
    assert exposure.custody_usd > 0
    assert exposure.total_usd == pytest.approx(
        exposure.managed_usd + exposure.custody_usd
    )
    assert exposure.total_usd == pytest.approx(46_571_821.48, abs=0.01)


def test_band_breaches_are_calculated_from_holdings(challenge_data):
    assessment = assess_client_mandates(challenge_data, "CL-0003", SNAPSHOT)
    by_class = {b.asset_class: b for b in assessment.band_breaches}
    equity = by_class["Equity"]
    assert equity.direction == "above max"
    assert equity.max_pct == 30
    assert equity.actual_pct == pytest.approx(71.46, abs=0.01)
    fixed_income = by_class["Fixed Income"]
    assert fixed_income.direction == "below min"
    assert fixed_income.actual_pct == pytest.approx(9.15, abs=0.01)


def test_single_position_limits_apply_only_where_the_dataset_says_so(challenge_data):
    """Diversified funds and sovereigns are not single-name exposures."""
    instruments = challenge_data.instruments.set_index("instrument_id")
    for client_id in challenge_data.client_ids():
        assessment = assess_client_mandates(challenge_data, client_id, SNAPSHOT)
        for breach in assessment.position_breaches:
            assert (
                str(instruments.loc[breach.instrument_id]["concentration_limit_applies"])
                == "Y"
            )


def test_binding_exclusions_are_evaluated_separately_from_drift(challenge_data):
    assessment = assess_client_mandates(challenge_data, "CL-0005", SNAPSHOT)
    excluded = {b.instrument_id for b in assessment.exclusion_breaches}
    assert excluded == {"SYN-EQ-0008", "SYN-ST-0105"}
    for breach in assessment.exclusion_breaches:
        assert "binding exclusion" in breach.mandate_notes.lower()


def test_a_mandate_without_binding_exclusions_produces_none(challenge_data):
    for client_id in ("CL-0001", "CL-0012", "CL-0003"):
        assessment = assess_client_mandates(challenge_data, client_id, SNAPSHOT)
        assert assessment.exclusion_breaches == []


def test_unwaived_exclusion_raises_the_compliance_safety_override(queue_by_client):
    item = queue_by_client["CL-0005"]
    assert item.urgency.tier == "Critical"
    assert item.urgency.safety_override.rule_id == "SO-3-UNWAIVED-BINDING-EXCLUSION"


def test_an_evidenced_waiver_de_escalates_without_hiding_the_breach(
    cases_by_client, packets_by_client, challenge_data
):
    """CL-0007 breached the commodity ceiling with a waiver on file."""
    assessment = assess_client_mandates(challenge_data, "CL-0007", SNAPSHOT)
    commodities = [b for b in assessment.band_breaches if b.asset_class == "Commodities"]
    assert commodities, "the underlying breach must still be detected"

    packets = {p.signal_type: p for p in packets_by_client["CL-0007"]}
    mandate_packet = packets["mandate"]
    facts = " ".join(c.statement for c in mandate_packet.facts)
    interpretations = " ".join(c.statement for c in mandate_packet.interpretations)
    assert "Commodities" in facts, "the breach is still reported as a fact"
    assert "waiver" in interpretations.lower()

    # And it ranks below the unwaived compliance breach.
    assert cases_by_client["CL-0007"].urgency.tier == "Watch"


def test_look_through_reads_the_declared_underlying(challenge_data):
    fcn = challenge_data.instrument("SYN-SP-0505")
    parsed = parse_look_through(fcn)
    assert parsed is not None
    assert parsed.structure == "worst-of basket"
    assert "Pacific Orient Shipping" in parsed.components
    assert "Bara Nusantara Energy" in parsed.components


def test_accumulator_underlying_falls_back_to_the_instrument_name(challenge_data):
    accumulator = challenge_data.instrument("SYN-SP-0503")
    parsed = parse_look_through(accumulator)
    assert parsed is not None
    assert any("Golden Harbour" in component for component in parsed.components)


def test_look_through_never_invents_component_weights(challenge_data):
    exposure = build_client_exposure(challenge_data, "CL-0001", SNAPSHOT)
    assert exposure.look_throughs
    for look_through in exposure.look_throughs:
        assert "weights are not supplied" in look_through.limitation


def test_combined_exposure_adds_declared_underlying_to_direct_holdings(challenge_data):
    exposure = build_client_exposure(challenge_data, "CL-0001", SNAPSHOT)
    energy = exposure.themes["energy"]
    assert energy.direct_pct == pytest.approx(41.42, abs=0.05)
    assert energy.look_through_usd > 0
    assert energy.combined_pct == pytest.approx(44.99, abs=0.05)
    assert energy.combined_pct > energy.direct_pct


def test_look_through_lowers_confidence_because_it_is_indicative(cases_by_client):
    reasons = " ".join(cases_by_client["CL-0001"].confidence.reasons).lower()
    assert "look-through" in reasons


def test_concentration_aggregates_across_a_clients_portfolios(challenge_data):
    """CL-0017 holds three portfolios; exposure is measured across all of them."""
    exposure = build_client_exposure(challenge_data, "CL-0017", SNAPSHOT)
    assert exposure.total_usd == pytest.approx(87_902_980.0, abs=0.01)
    portfolios = challenge_data.client_portfolios("CL-0017")
    assert len(portfolios) == 3
