"""The highest behavioural seam: dataset in, Workbench artifact out."""

from __future__ import annotations

from datetime import date, datetime, timezone

from jb_clarity.build import build_workbench

AS_OF = date(2026, 8, 26)
FIXED_CLOCK = lambda: datetime(2026, 9, 4, tzinfo=timezone.utc)  # noqa: E731


def test_artifact_identifies_itself_as_generated_v1(model):
    assert model.meta.schema_version == "1.0.0"
    assert model.meta.artifact_kind == "generated"
    assert model.meta.as_of_date == AS_OF


def test_all_five_supplied_snapshots_are_recorded(model):
    assert model.meta.source_snapshot_dates == [
        date(2025, 12, 31),
        date(2026, 2, 27),
        date(2026, 3, 31),
        date(2026, 6, 30),
        date(2026, 8, 26),
    ]


def test_whole_book_is_present_and_ranked(model):
    assert model.book.client_count == 20
    assert model.book.portfolio_count == 24
    assert len(model.book.priority_queue) == 20
    assert len(model.client_cases) == 20

    ranks = [item.rank for item in model.book.priority_queue]
    assert ranks == list(range(1, 21)), "ranks must be contiguous and start at 1"
    assert len({item.client_id for item in model.book.priority_queue}) == 20


def test_rm_identity_comes_from_the_data(model):
    assert model.book.rm.id == "RM-SG-014"
    assert model.book.rm.name == "Priscilla Ong"


def test_every_queue_item_has_a_matching_case(model, cases_by_client):
    for item in model.book.priority_queue:
        assert item.client_id in cases_by_client
        case = cases_by_client[item.client_id]
        assert item.case_id == case.case_id
        assert item.urgency.tier == case.urgency.tier
        assert item.urgency.score == case.urgency.score
        assert item.confidence.level == case.confidence.level


def test_client_cases_are_ordered_to_match_the_queue(model):
    queue_order = [item.client_id for item in model.book.priority_queue]
    case_order = [case.client_id for case in model.client_cases]
    assert case_order == queue_order


def test_repeat_builds_are_semantically_identical(data_dir):
    first = build_workbench(data_dir, AS_OF, clock=FIXED_CLOCK).to_contract_dict()
    second = build_workbench(data_dir, AS_OF, clock=FIXED_CLOCK).to_contract_dict()
    assert first == second


def test_generated_at_is_the_only_variable_field(data_dir):
    first = build_workbench(data_dir, AS_OF).to_contract_dict()
    second = build_workbench(data_dir, AS_OF).to_contract_dict()
    first["meta"]["generatedAt"] = second["meta"]["generatedAt"] = "fixed"
    assert first == second


def test_book_summary_counts_match_the_queue(model):
    summary = model.book.summary
    assert summary.critical + summary.high + summary.watch == 20
    tiers = [item.urgency.tier for item in model.book.priority_queue]
    assert summary.critical == tiers.count("Critical")
    assert summary.high == tiers.count("High")
    assert summary.watch == tiers.count("Watch")


def test_filters_offer_only_values_present_in_the_book(model):
    centres = set(model.book.filters.booking_centres)
    assert centres == {"Singapore", "Hong Kong"}
    assert model.book.filters.signal_types, "signal type filter must not be empty"


def test_data_quality_is_reported_not_repaired(model):
    # The supplied data carries a known private-markets valuation lag, so the
    # artifact must say attention rather than claim to be clear.
    assert model.meta.data_quality.status == "attention"
    ids = {issue.id for issue in model.meta.data_quality.issues}
    assert "DQ-STALE-VALUATION" in ids
