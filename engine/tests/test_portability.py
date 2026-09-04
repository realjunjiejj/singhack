"""Portability of the engine across differently-identified Books.

These tests take the supplied Book and rebuild it under a hostile identity
scheme, then under different snapshot grids. They exist because "it works on
our data" is not a portability claim.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

import portability
from jb_clarity.build import build_workbench
from jb_clarity.ingestion.loader import load_challenge_data
from jb_clarity.ingestion.source_contract import (
    MINIMUM_SNAPSHOTS,
    SourceContractError,
    discover_snapshots,
)

AS_OF = date(2026, 8, 26)
FIXED_CLOCK = lambda: datetime(2026, 9, 4, tzinfo=timezone.utc)  # noqa: E731


def _drop_snapshots(book: Path, drop: list[str]) -> None:
    """Remove snapshots from a Book, including their wide columns."""
    holdings = pd.read_csv(book / "holdings.csv")
    holdings[~holdings.snapshot_date.astype(str).isin(drop)].to_csv(
        book / "holdings.csv", index=False
    )
    for name in ("portfolios.csv", "credit_facilities.csv", "instruments.csv"):
        frame = pd.read_csv(book / name)
        wide = [c for c in frame.columns if any(d in c for d in drop)]
        frame.drop(columns=wide).to_csv(book / name, index=False)
    market = pd.read_csv(book / "market_context.csv")
    market[~market.snapshot_date.astype(str).isin(drop)].to_csv(
        book / "market_context.csv", index=False
    )


@pytest.fixture(scope="module")
def remapped_book(tmp_path_factory, data_dir) -> tuple[Path, portability.RemapPlan]:
    target = tmp_path_factory.mktemp("remapped") / "book"
    plan = portability.build_plan(data_dir, switch_currency_for="CL-0002")
    portability.write_remapped_book(data_dir, target, plan)
    return target, plan


@pytest.fixture(scope="module")
def remapped_model(remapped_book):
    book, _ = remapped_book
    return build_workbench(book, AS_OF, clock=FIXED_CLOCK)


# -- identity -------------------------------------------------------------


def test_a_fully_remapped_book_still_builds(remapped_model):
    assert len(remapped_model.client_cases) == 20
    assert len(remapped_model.book.priority_queue) == 20


def test_remapped_artifact_is_schema_valid(remapped_model, schema):
    import jsonschema

    jsonschema.Draft202012Validator(schema).validate(remapped_model.to_contract_dict())


def test_no_singhacks_identifier_survives_the_remap(remapped_model, data_dir):
    """The clearest portability failure would be the old Book leaking through."""
    import json

    blob = json.dumps(remapped_model.to_contract_dict())
    leaked = sorted(
        value for value in portability.singhacks_identifiers(data_dir) if value and value in blob
    )
    assert leaked == []


def test_remapped_book_carries_its_own_rm(remapped_model, remapped_book):
    _, plan = remapped_book
    assert remapped_model.book.rm.id == plan.rm_id[1]
    assert remapped_model.book.rm.name == plan.rm_name[1]


def test_remapped_book_uses_its_own_booking_centres(remapped_model):
    centres = set(remapped_model.book.filters.booking_centres)
    assert centres == {"Zurich", "Geneva"}


def test_remapped_evidence_cites_remapped_record_keys(remapped_model):
    """Evidence must point at records that exist in the new Book."""
    for packet in remapped_model.evidence_packets:
        assert packet.client_id.startswith("ZCLI-")
        for item in packet.items:
            assert "CL-00" not in item.source_reference.record_key


def test_identifier_columns_survive_as_strings(remapped_book):
    """A record key must never be reshaped by type inference."""
    book, _ = remapped_book
    data = load_challenge_data(book)
    assert data.clients["client_id"].dtype == "string"
    assert data.holdings["instrument_id"].dtype == "string"


def test_a_switched_base_currency_still_reconciles(remapped_model, remapped_book):
    """One client's portfolios were moved to another currency at real rates."""
    _, plan = remapped_book
    switched = plan.clients[plan.recurrenced_currency[0]]
    case = {c.client_id: c for c in remapped_model.client_cases}[switched]
    conflicts = [c.statement for c in case.uncertainties if "materially different" in c.statement]
    assert conflicts == [], "currency conversion must not manufacture a totals conflict"


# -- snapshot independence ------------------------------------------------


@pytest.mark.parametrize(
    "drop,expected",
    [
        (["2026-02-27", "2026-06-30"], 3),
        (["2026-06-30"], 4),
        ([], 5),
    ],
)
def test_books_with_different_snapshot_counts_build(tmp_path, data_dir, drop, expected):
    book = tmp_path / f"book-{expected}"
    portability.write_remapped_book(data_dir, book)
    _drop_snapshots(book, drop)
    model = build_workbench(book, AS_OF, clock=FIXED_CLOCK)
    assert len(model.meta.source_snapshot_dates) == expected
    for case in model.client_cases:
        assert len(case.timeline) == expected


@pytest.mark.parametrize("drop,expected", [(["2026-02-27", "2026-06-30"], 3), ([], 5)])
def test_snapshot_wording_reports_the_real_count(tmp_path, data_dir, drop, expected):
    """A three-snapshot Book must never be told it has five."""
    import json

    book = tmp_path / f"wording-{expected}"
    portability.write_remapped_book(data_dir, book)
    _drop_snapshots(book, drop)
    blob = json.dumps(build_workbench(book, AS_OF, clock=FIXED_CLOCK).to_contract_dict())

    assert "five supplied snapshot" not in blob
    assert "five dated snapshot" not in blob
    assert f"{expected} supplied snapshots" in blob
    assert f"{expected} dated snapshots" in blob


def test_period_claims_name_their_endpoints(tmp_path, data_dir):
    """A change claim must say which two dates it compared."""
    book = tmp_path / "endpoints"
    portability.write_remapped_book(data_dir, book)
    _drop_snapshots(book, ["2026-02-27", "2026-06-30"])
    model = build_workbench(book, AS_OF, clock=FIXED_CLOCK)
    packets = {
        (p.client_id, p.signal_type): p for p in model.evidence_packets
    }
    facts = " ".join(
        claim.statement
        for (client_id, signal_type), packet in packets.items()
        if signal_type == "explanation"
        for claim in packet.facts
    )
    assert "2025-12-31" in facts and "2026-08-26" in facts


def test_a_single_snapshot_book_is_refused(tmp_path, data_dir):
    """One snapshot cannot support a change explanation, and we say so."""
    book = tmp_path / "single"
    portability.write_remapped_book(data_dir, book)
    _drop_snapshots(book, ["2025-12-31", "2026-02-27", "2026-03-31", "2026-06-30"])
    with pytest.raises(SourceContractError, match="At least 2 distinct dates"):
        build_workbench(book, AS_OF, clock=FIXED_CLOCK)


# -- source contract ------------------------------------------------------


def test_discover_snapshots_orders_and_deduplicates():
    assert discover_snapshots(
        ["2026-03-31", "2025-12-31", "2026-03-31"], "holdings.csv"
    ) == ["2025-12-31", "2026-03-31"]


def test_discover_snapshots_rejects_a_non_iso_date():
    with pytest.raises(SourceContractError, match="not an ISO date"):
        discover_snapshots(["31/12/2025", "2026-03-31"], "holdings.csv")


def test_discover_snapshots_requires_a_comparison_pair():
    with pytest.raises(SourceContractError, match=f"At least {MINIMUM_SNAPSHOTS}"):
        discover_snapshots(["2026-03-31"], "holdings.csv")


def test_a_missing_required_column_names_the_file_and_column(tmp_path, data_dir):
    book = tmp_path / "missing-column"
    portability.write_remapped_book(data_dir, book)
    frame = pd.read_csv(book / "clients.csv").drop(columns=["risk_profile"])
    frame.to_csv(book / "clients.csv", index=False)
    with pytest.raises(SourceContractError, match="clients.csv is missing required column"):
        load_challenge_data(book)


def test_a_malformed_note_names_the_record(tmp_path, data_dir):
    import json

    book = tmp_path / "bad-note"
    portability.write_remapped_book(data_dir, book)
    notes = json.loads((book / "rm_notes.json").read_text(encoding="utf-8"))
    notes[0]["note_date"] = "15 March 2026"
    (book / "rm_notes.json").write_text(json.dumps(notes), encoding="utf-8")
    with pytest.raises(SourceContractError, match="record 0.*not an ISO date"):
        load_challenge_data(book)


def test_unmapped_event_channels_are_reported_not_guessed(model):
    """The supplied Book declares channels the engine cannot map."""
    issues = {issue.id: issue for issue in model.meta.data_quality.issues}
    assert "DQ-UNMAPPED-EVENT-CHANNEL" in issues
    summary = issues["DQ-UNMAPPED-EVENT-CHANNEL"].summary
    assert "nearest-sounding" in summary
    assert "'airlines'" in summary
