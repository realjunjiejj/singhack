"""Every claim must resolve to an evidence item and a source record."""

from __future__ import annotations

from jb_clarity.domain.enums import GuidedAction

SOURCE_FILES = {
    "clients.csv",
    "portfolios.csv",
    "holdings.csv",
    "instruments.csv",
    "mandates.csv",
    "transactions.csv",
    "credit_facilities.csv",
    "commitments.csv",
    "planned_cash_needs.csv",
    "market_context.csv",
    "event_log.csv",
    "rm_notes.json",
}


def _all_items(artifact) -> dict:
    return {
        item["id"]: item
        for packet in artifact["evidencePackets"]
        for item in packet["items"]
    }


def test_every_evidence_item_names_a_real_source_file(artifact):
    for item in _all_items(artifact).values():
        reference = item["sourceReference"]
        assert reference["file"] in SOURCE_FILES
        assert reference["recordKey"].strip()


def test_evidence_item_ids_are_globally_unique(artifact):
    ids = [
        item["id"]
        for packet in artifact["evidencePackets"]
        for item in packet["items"]
    ]
    assert len(ids) == len(set(ids))


def test_every_claim_in_every_packet_resolves(artifact):
    items = _all_items(artifact)
    for packet in artifact["evidencePackets"]:
        collections = ("facts", "interpretations", "uncertainties", "conflicts", "assumptions")
        for collection in collections:
            for claim in packet[collection]:
                assert claim["statement"].strip()
                for item_id in claim["evidenceItemIds"]:
                    assert item_id in items, f"{claim['id']} cites missing {item_id}"


def test_case_claims_resolve_to_that_clients_own_evidence(artifact):
    by_client: dict[str, set[str]] = {}
    for packet in artifact["evidencePackets"]:
        by_client.setdefault(packet["clientId"], set()).update(
            item["id"] for item in packet["items"]
        )
    for case in artifact["clientCases"]:
        owned = by_client.get(case["clientId"], set())
        for collection in ("facts", "interpretations", "uncertainties"):
            for claim in case[collection]:
                for item_id in claim["evidenceItemIds"]:
                    assert item_id in owned, (
                        f"{case['clientId']} claim {claim['id']} cites evidence "
                        "belonging to another client"
                    )


def test_factor_contributions_cite_resolvable_evidence(artifact):
    items = _all_items(artifact)
    for case in artifact["clientCases"]:
        for contribution in case["factorContributions"]:
            for item_id in contribution["evidenceItemIds"]:
                assert item_id in items


def test_signals_open_loops_and_clocks_cite_resolvable_evidence(artifact):
    items = _all_items(artifact)
    for case in artifact["clientCases"]:
        for collection in ("anticipatorySignals", "openLoops", "governanceClocks"):
            for entry in case[collection]:
                assert entry["evidenceItemIds"]
                for item_id in entry["evidenceItemIds"]:
                    assert item_id in items


def test_meeting_brief_references_resolve(artifact):
    items = _all_items(artifact)
    for case in artifact["clientCases"]:
        brief = case["meetingBrief"]
        loop_ids = {loop["id"] for loop in case["openLoops"]}
        clock_ids = {clock["id"] for clock in case["governanceClocks"]}
        assert set(brief["openLoopIds"]) <= loop_ids
        assert set(brief["governanceClockIds"]) <= clock_ids
        for item_id in brief["evidenceItemIds"]:
            assert item_id in items


def test_derived_metrics_show_their_working(artifact):
    for packet in artifact["evidencePackets"]:
        for metric in packet["derivedMetrics"]:
            assert metric["formula"].strip()
            assert metric["inputs"], "a metric must expose the inputs it used"
            assert metric["result"]["unit"]
            assert metric["snapshotDate"]


def test_fact_interpretation_and_uncertainty_stay_separate(artifact):
    for packet in artifact["evidencePackets"]:
        fact_ids = {c["id"] for c in packet["facts"]}
        interpretation_ids = {c["id"] for c in packet["interpretations"]}
        uncertainty_ids = {c["id"] for c in packet["uncertainties"]}
        assert not fact_ids & interpretation_ids
        assert not fact_ids & uncertainty_ids
        assert not interpretation_ids & uncertainty_ids


def test_only_approved_guided_actions_are_offered(artifact):
    approved = {str(action) for action in GuidedAction}
    for case in artifact["clientCases"]:
        assert set(case["allowedGuidedActions"]) <= approved
        # Open loop actions are only offered when there is a loop to act on.
        loop_actions = {
            "confirm-open-loop",
            "defer-open-loop",
            "assign-open-loop",
            "dismiss-open-loop",
        }
        offered = set(case["allowedGuidedActions"]) & loop_actions
        assert bool(offered) == bool(case["openLoops"])


def test_no_case_offers_an_action_outside_the_human_in_the_loop_boundary(artifact):
    forbidden = {"execute-trade", "send-message", "contact-client", "place-order"}
    for case in artifact["clientCases"]:
        assert not set(case["allowedGuidedActions"]) & forbidden


def test_event_claims_only_appear_with_the_controlled_event_source(artifact):
    """No claim may assert a 2026 event without citing event_log.csv."""
    items = _all_items(artifact)
    for packet in artifact["evidencePackets"]:
        for claim in packet["facts"]:
            cited_files = {
                items[i]["sourceReference"]["file"] for i in claim["evidenceItemIds"]
            }
            if "event_log.csv" in cited_files:
                continue
            lowered = claim["statement"].lower()
            for phrase in ("hormuz", "iran", "federal reserve", "opec", "war"):
                assert phrase not in lowered, (
                    f"{claim['id']} names a world event without citing event_log.csv"
                )
