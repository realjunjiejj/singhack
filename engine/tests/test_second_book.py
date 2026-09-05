"""The second Book: Meridian Wealth.

Everything here must hold for a Book the engine has never seen, with no
client-specific code and no manual editing of the artifact. If a rule only
works because of something particular to the SingHacks data, it fails here.
"""

from __future__ import annotations

import json
import socket
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from fixtures import second_book
from jb_clarity.build import build_workbench

AS_OF = date.fromisoformat(second_book.AS_OF)
FIXED_CLOCK = lambda: datetime(2026, 4, 1, tzinfo=timezone.utc)  # noqa: E731


@pytest.fixture(scope="module")
def book(tmp_path_factory) -> Path:
    return second_book.write_book(tmp_path_factory.mktemp("meridian") / "book")


@pytest.fixture(scope="module")
def model(book: Path):
    return build_workbench(book, AS_OF, clock=FIXED_CLOCK)


@pytest.fixture(scope="module")
def artifact(model) -> dict:
    return model.to_contract_dict()


@pytest.fixture(scope="module")
def cases(model) -> dict:
    return {case.client_id: case for case in model.client_cases}


@pytest.fixture(scope="module")
def packets(model) -> dict:
    grouped: dict[tuple[str, str], object] = {}
    for packet in model.evidence_packets:
        grouped[(packet.client_id, packet.signal_type)] = packet
    return grouped


# -- the Book is genuinely different --------------------------------------


def test_the_book_has_its_own_shape(model):
    assert model.book.client_count == 4
    assert model.book.portfolio_count == 5
    assert len(model.book.priority_queue) == 4
    assert model.book.rm.id == "RM-ZH-401"
    assert model.book.rm.name == "Ingrid Solberg"


def test_the_book_uses_its_own_snapshot_grid(model):
    assert [d.isoformat() for d in model.meta.source_snapshot_dates] == second_book.SNAPSHOTS
    assert len(model.meta.source_snapshot_dates) == 4


def test_one_client_holds_two_portfolios(book):
    portfolios = pd.read_csv(book / "portfolios.csv")
    counts = portfolios.groupby("client_id").size()
    assert counts["MW-C-200"] == 2


def test_the_book_spans_two_currencies(book):
    portfolios = pd.read_csv(book / "portfolios.csv")
    assert set(portfolios.base_currency) == {"CHF", "USD"}
    market = pd.read_csv(book / "market_context.csv")
    assert "CHFUSD" in set(market.series_id)


def test_no_singhacks_content_appears_anywhere(artifact):
    blob = json.dumps(artifact)
    leaked = sorted(token for token in second_book.singhacks_tokens() if token in blob)
    assert leaked == []


def test_the_artifact_is_schema_valid(artifact, schema):
    import jsonschema

    jsonschema.Draft202012Validator(schema).validate(artifact)


# -- ranking behaves, for allowed reasons ---------------------------------


def test_critical_arrives_only_through_a_safety_override(model):
    critical = [i for i in model.book.priority_queue if i.urgency.tier == "Critical"]
    assert len(critical) == 1
    item = critical[0]
    assert item.client_id == "MW-C-200"
    assert item.urgency.safety_override.rule_id == "SO-3-UNWAIVED-BINDING-EXCLUSION"
    for other in model.book.priority_queue:
        if other.client_id != item.client_id:
            assert other.urgency.safety_override is None


def test_the_excluded_holding_is_named_from_this_books_mandate(packets):
    packet = packets[("MW-C-200", "exclusion")]
    facts = " ".join(claim.statement for claim in packet.facts)
    assert "Nordkap Tobacco Holding" in facts
    assert "MW-SUS" in facts


def test_the_conservative_client_shows_a_band_break_and_a_mismatch(packets):
    mandate = " ".join(c.statement for c in packets[("MW-C-100", "mandate")].facts)
    assert "Equity" in mandate and "MW-P-100" in mandate
    suitability = " ".join(c.statement for c in packets[("MW-C-100", "suitability")].facts)
    assert "Conservative" in suitability


def test_the_facility_is_near_its_trigger_not_breached(cases, packets):
    case = cases["MW-C-300"]
    credit = [s for s in case.anticipatory_signals if s.type == "credit"]
    assert credit and credit[0].status == "near"
    assert case.urgency.safety_override is None
    facts = " ".join(c.statement for c in packets[("MW-C-300", "credit")].facts)
    assert "MW-LN-300" in facts


def test_the_confirmed_obligation_is_surfaced(packets):
    facts = " ".join(c.statement for c in packets[("MW-C-400", "cash-need")].facts)
    assert "Foundation endowment commitment" in facts
    assert "1,800,000" in facts


def test_changing_the_facility_changes_the_queue(tmp_path, book):
    """A different source record must produce a different Client Case."""
    before = {
        i.client_id: i.urgency.score
        for i in build_workbench(book, AS_OF, clock=FIXED_CLOCK).book.priority_queue
    }

    altered = tmp_path / "breached"
    second_book.write_book(altered)
    frame = pd.read_csv(altered / "credit_facilities.csv")
    lending = float(frame.loc[0, f"lending_value_{second_book.AS_OF}"])
    frame.loc[0, f"drawn_{second_book.AS_OF}"] = lending * 0.94
    frame.loc[0, f"ltv_pct_{second_book.AS_OF}"] = 94.0
    frame.to_csv(altered / "credit_facilities.csv", index=False)

    after = {
        i.client_id: i
        for i in build_workbench(altered, AS_OF, clock=FIXED_CLOCK).book.priority_queue
    }
    assert after["MW-C-300"].urgency.tier == "Critical"
    assert (
        after["MW-C-300"].urgency.safety_override.rule_id
        == "SO-1-ACTIVE-FACILITY-BREACH"
    )
    assert after["MW-C-300"].urgency.score > before["MW-C-300"]


def test_changing_the_obligation_changes_the_queue(tmp_path):
    altered = tmp_path / "unfundable"
    second_book.write_book(altered)
    frame = pd.read_csv(altered / "planned_cash_needs.csv")
    frame.loc[frame.need_id == "MW-OB-400", "amount"] = 900_000_000.0
    frame.to_csv(altered / "planned_cash_needs.csv", index=False)

    queue = {
        i.client_id: i
        for i in build_workbench(altered, AS_OF, clock=FIXED_CLOCK).book.priority_queue
    }
    assert queue["MW-C-400"].urgency.tier == "Critical"
    assert (
        queue["MW-C-400"].urgency.safety_override.rule_id
        == "SO-2-UNCOVERED-NEAR-OBLIGATION"
    )


# -- explanation comes from this Book's event source -----------------------


def test_event_wording_comes_from_the_new_controlled_event_source(packets):
    interpretations = " ".join(
        c.statement for c in packets[("MW-C-300", "explanation")].interpretations
    )
    assert "North Sea production outage" in interpretations
    assert "Helvetia Energy AG" in interpretations
    assert "Hormuz" not in interpretations


def test_event_claims_cite_this_books_event_log(packets):
    packet = packets[("MW-C-300", "explanation")]
    items = {item.id: item for item in packet.items}
    for claim in packet.interpretations:
        files = {items[i].source_reference.file for i in claim.evidence_item_ids}
        assert "event_log.csv" in files


def test_an_unrecognised_channel_stays_unlinked_and_visible(model, artifact):
    """The engine must not guess what 'Sovereign wealth flows' touches."""
    issues = {issue.id: issue for issue in model.meta.data_quality.issues}
    assert "DQ-UNMAPPED-EVENT-CHANNEL" in issues
    assert "'Sovereign wealth flows'" in issues["DQ-UNMAPPED-EVENT-CHANNEL"].summary

    for case in artifact["clientCases"]:
        for packet_claims in ("facts", "interpretations"):
            for claim in case[packet_claims]:
                assert "Sovereign wealth" not in claim["statement"]


def test_the_lagged_valuation_is_disclosed(model):
    issues = {issue.id: issue for issue in model.meta.data_quality.issues}
    assert "DQ-STALE-VALUATION" in issues
    assert model.meta.data_quality.status == "attention"


# -- relationship threads --------------------------------------------------


def test_the_unanswered_question_becomes_an_open_loop(cases):
    loops = cases["MW-C-300"].open_loops
    questions = [loop for loop in loops if "question" in loop.summary]
    assert questions
    assert questions[0].confidence.level == "High"
    assert "raise the facility limit" in questions[0].source_excerpt
    assert questions[0].confirmation_required is True


def test_the_answered_question_does_not_become_an_open_loop(cases):
    """A thread the note itself records as answered is not an open task."""
    loops = cases["MW-C-200"].open_loops
    assert [loop for loop in loops if "question" in loop.summary] == []


def test_the_client_constraint_is_captured(cases):
    loops = cases["MW-C-100"].open_loops
    constraints = [loop for loop in loops if "constraint" in loop.summary]
    assert constraints
    assert "engineering stake" in constraints[0].source_excerpt


# -- evidence resolves to this Book ---------------------------------------


def test_every_claim_resolves_to_this_books_evidence(artifact):
    items = {
        item["id"]: item
        for packet in artifact["evidencePackets"]
        for item in packet["items"]
    }
    assert items
    for packet in artifact["evidencePackets"]:
        for collection in ("facts", "interpretations", "uncertainties", "conflicts", "assumptions"):
            for claim in packet[collection]:
                for item_id in claim["evidenceItemIds"]:
                    assert item_id in items
    for item in items.values():
        assert item["sourceReference"]["recordKey"]


def test_every_timeline_point_resolves_to_this_books_evidence(artifact):
    items = {
        item["id"]
        for packet in artifact["evidencePackets"]
        for item in packet["items"]
    }
    for case in artifact["clientCases"]:
        assert len(case["timeline"]) == 4
        for point in case["timeline"]:
            assert point["evidenceItemIds"]
            for item_id in point["evidenceItemIds"]:
                assert item_id in items


def test_timeline_totals_match_the_source_holdings(artifact, book):
    holdings = pd.read_csv(book / "holdings.csv")
    for case in artifact["clientCases"]:
        for point in case["timeline"]:
            expected = float(
                holdings[
                    (holdings.client_id == case["clientId"])
                    & (holdings.snapshot_date == point["date"])
                ]["market_value_usd"].sum()
            )
            assert point["metrics"]["totalValue"]["value"] == pytest.approx(expected, abs=0.02)


def test_a_reporting_language_without_a_translation_degrades_to_english(cases):
    """Uzbek has no cached draft; the case stays usable in canonical English."""
    case = cases["MW-C-400"]
    assert case.reporting_language == "Uzbek"
    languages = {draft.language for draft in case.client_ready_drafts or []}
    assert languages == {"English"}
    assert case.meeting_brief.opening_question


# -- operating conditions --------------------------------------------------


def test_building_the_book_makes_no_network_request(monkeypatch, book):
    def refuse(*args, **kwargs):  # pragma: no cover - only runs on failure
        raise AssertionError("the engine attempted a network connection")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    model = build_workbench(book, AS_OF, clock=FIXED_CLOCK)
    assert len(model.client_cases) == 4


def test_the_build_is_reproducible(book):
    first = build_workbench(book, AS_OF, clock=FIXED_CLOCK).to_contract_dict()
    second = build_workbench(book, AS_OF, clock=FIXED_CLOCK).to_contract_dict()
    assert first == second
