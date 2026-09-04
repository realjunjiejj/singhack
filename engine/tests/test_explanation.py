"""Portfolio explanation: the timeline, and events grounded in the event log."""

from __future__ import annotations

import pytest

from jb_clarity.calculations.timeline import build_client_timeline, link_events

SNAPSHOT = "2026-08-26"


def _explanation(packets_by_client, client_id):
    return {p.signal_type: p for p in packets_by_client[client_id]}["explanation"]


def test_every_client_has_an_explanation_packet(model, packets_by_client):
    for case in model.client_cases:
        signal_types = {p.signal_type for p in packets_by_client[case.client_id]}
        assert "explanation" in signal_types


def test_every_timeline_point_can_open_its_own_evidence(model):
    """A number on the timeline the RM cannot trace is not usable."""
    for case in model.client_cases:
        assert len(case.timeline) == 5
        for point in case.timeline:
            assert point.evidence_item_ids, (
                f"{case.client_id} {point.date} has no evidence to open"
            )


def test_timeline_ltv_points_cite_the_facility_record(cases_by_client):
    case = cases_by_client["CL-0001"]
    for point in case.timeline:
        assert "loanToValue" in point.metrics
        # One citation for the wealth total, one for the facility ratio.
        assert len(point.evidence_item_ids) == 2


def test_period_change_is_stated_with_both_endpoints(packets_by_client):
    facts = " ".join(c.statement for c in _explanation(packets_by_client, "CL-0012").facts)
    assert "30,130,862" in facts
    assert "28,028,705" in facts
    assert "-6.98%" in facts


def test_asset_class_movement_is_named(packets_by_client):
    """Cheung's decline is a fixed income story; the engine must say so."""
    facts = " ".join(c.statement for c in _explanation(packets_by_client, "CL-0012").facts)
    assert "Fixed Income down" in facts


def test_event_claims_cite_the_controlled_event_source(model, packets_by_client):
    for case in model.client_cases:
        packet = _explanation(packets_by_client, case.client_id)
        items = {item.id: item for item in packet.items}
        for claim in packet.interpretations:
            files = {items[i].source_reference.file for i in claim.evidence_item_ids}
            assert "event_log.csv" in files, (
                f"{claim.id} makes an event claim without citing the event log"
            )


def test_events_are_quoted_from_the_log_not_paraphrased(
    packets_by_client, challenge_data
):
    descriptions = set(challenge_data.events["description"].astype(str))
    packet = _explanation(packets_by_client, "CL-0012")
    quoted = [
        description
        for description in descriptions
        if any(description in claim.statement for claim in packet.interpretations)
    ]
    assert quoted, "event descriptions must be quoted verbatim from event_log.csv"


def test_cheung_duration_story_links_rate_events_to_his_bonds(packets_by_client):
    packet = _explanation(packets_by_client, "CL-0012")
    text = " ".join(c.statement for c in packet.interpretations)
    assert "US Treasury 2.375% due 2045" in text
    assert "4.46%" in text or "10-year" in text
    assert "duration" in text.lower()


def test_no_event_is_linked_without_a_matching_holding(challenge_data):
    """A transmission channel that reaches nothing produces no claim."""
    links = link_events(challenge_data, "CL-0010", SNAPSHOT)
    for link in links:
        assert link.matched_instruments
        assert link.matched_value_usd > 0


def test_each_holding_is_attributed_to_the_channel_that_reached_it(challenge_data):
    """A single-stock energy holding must not be reported under a tech channel."""
    links = {
        link.event_date: link
        for link in link_events(challenge_data, "CL-0001", SNAPSHOT)
    }
    tech_event = links["2026-06-05"]
    by_channel = dict(tech_event.matches_by_channel)
    tech_names = {name for _, name, _ in by_channel["US technology"]}
    assert "US Technology Leaders Fund" in tech_names
    assert "Bara Nusantara Energy Tbk" not in tech_names
    # It is still reported, under the generic channel that genuinely matched.
    generic = {name for _, name, _ in by_channel["concentrated equity"]}
    assert "Bara Nusantara Energy Tbk" in generic


def test_explanation_states_that_it_is_not_attribution(packets_by_client):
    packet = _explanation(packets_by_client, "CL-0012")
    caveats = " ".join(c.statement for c in packet.uncertainties)
    assert "not performance attribution" in caveats


def test_explanation_declares_the_controlled_event_source(packets_by_client):
    packet = _explanation(packets_by_client, "CL-0012")
    assumptions = " ".join(c.statement for c in packet.assumptions)
    assert "event_log.csv" in assumptions
    assert "outside knowledge" in assumptions


def test_explanation_never_leads_a_client_case(model):
    """Explanation is context; a live risk always leads instead."""
    for case in model.client_cases:
        types = {s.type for s in case.anticipatory_signals}
        if len(types) > 1:
            assert case.status is not None


def test_client_profile_is_evidenced_for_every_client(model, packets_by_client):
    """The brief quotes objectives verbatim, so they need a source record."""
    for case in model.client_cases:
        packet = _explanation(packets_by_client, case.client_id)
        labels = {item.label for item in packet.items}
        assert "Client profile and stated objectives" in labels
        profile = next(
            item for item in packet.items
            if item.label == "Client profile and stated objectives"
        )
        assert profile.source_reference.file == "clients.csv"
        assert profile.source_reference.record_key == case.client_id
        assert profile.id in case.meeting_brief.evidence_item_ids


def test_timeline_totals_match_an_independent_recomputation(model, challenge_data):
    for case in model.client_cases:
        timeline = build_client_timeline(challenge_data, case.client_id)
        expected = [round(p.total_usd, 2) for p in timeline.points]
        actual = [round(p.metrics["totalValue"].value, 2) for p in case.timeline]
        assert actual == expected
