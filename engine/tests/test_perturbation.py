"""The engine must react correctly when the underlying data changes.

Asserting that today's book produces today's answer only proves the engine is
consistent. These tests change one fact at a time and check the conclusion
moves for the right reason, which is what makes the ranking defensible rather
than merely reproducible.
"""

from __future__ import annotations

import json
import shutil
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from jb_clarity.build import build_workbench
from jb_clarity.ingestion.loader import load_challenge_data

AS_OF = date(2026, 8, 26)
FIXED_CLOCK = lambda: datetime(2026, 9, 4, tzinfo=timezone.utc)  # noqa: E731


@pytest.fixture
def mutated(tmp_path, data_dir):
    """Build the artifact from a copy of the dataset with one fact changed."""

    def _build(mutate) -> dict:
        target = tmp_path / "data"
        shutil.copytree(data_dir, target)
        mutate(target)
        return build_workbench(target, AS_OF, clock=FIXED_CLOCK).to_contract_dict()

    return _build


def _queue(payload: dict) -> dict:
    return {item["clientId"]: item for item in payload["book"]["priorityQueue"]}


def _packets(payload: dict, client_id: str) -> list[dict]:
    return [p for p in payload["evidencePackets"] if p["clientId"] == client_id]


def test_an_active_breach_becomes_critical(mutated):
    def breach(target: Path) -> None:
        frame = pd.read_csv(target / "credit_facilities.csv")
        row = frame.facility_id == "CF-0005"
        frame.loc[row, "drawn_2026-08-26"] = 13_000_000.0
        frame.loc[row, "ltv_pct_2026-08-26"] = 96.11
        frame.to_csv(target / "credit_facilities.csv", index=False)

    item = _queue(mutated(breach))["CL-0001"]
    assert item["urgency"]["tier"] == "Critical"
    assert item["urgency"]["safetyOverride"]["ruleId"] == "SO-1-ACTIVE-FACILITY-BREACH"
    assert item["rank"] <= 2
    assert item["status"] == "active"


def test_an_uncoverable_confirmed_obligation_becomes_critical(mutated):
    def huge_need(target: Path) -> None:
        frame = pd.read_csv(target / "planned_cash_needs.csv")
        frame.loc[frame.need_id == "CN-004", "amount"] = 500_000_000.0
        frame.to_csv(target / "planned_cash_needs.csv", index=False)

    item = _queue(mutated(huge_need))["CL-0003"]
    assert item["urgency"]["tier"] == "Critical"
    assert (
        item["urgency"]["safetyOverride"]["ruleId"] == "SO-2-UNCOVERED-NEAR-OBLIGATION"
    )


def test_a_coverable_obligation_does_not_become_critical(mutated):
    """The override is about coverage, not about size."""

    def affordable(target: Path) -> None:
        frame = pd.read_csv(target / "planned_cash_needs.csv")
        frame.loc[frame.need_id == "CN-004", "amount"] = 1_000.0
        frame.to_csv(target / "planned_cash_needs.csv", index=False)

    item = _queue(mutated(affordable))["CL-0003"]
    assert item["urgency"]["safetyOverride"] is None


def test_clearing_an_exclusion_removes_the_compliance_override(mutated):
    def clear(target: Path) -> None:
        frame = pd.read_csv(target / "instruments.csv")
        frame.loc[
            frame.instrument_id.isin(["SYN-EQ-0008", "SYN-ST-0105"]),
            "sustainability_excluded",
        ] = "N"
        frame.to_csv(target / "instruments.csv", index=False)

    item = _queue(mutated(clear))["CL-0005"]
    assert item["urgency"]["tier"] != "Critical"
    assert item["urgency"]["safetyOverride"] is None


def test_removing_a_waiver_raises_urgency_for_the_same_breach(mutated, queue_by_client):
    baseline = queue_by_client["CL-0007"].urgency.score

    def drop_waiver(target: Path) -> None:
        notes = json.loads((target / "rm_notes.json").read_text(encoding="utf-8"))
        for note in notes:
            if note["note_id"] == "N-010":
                note["note"] = "Client instructed an additional gold purchase."
        (target / "rm_notes.json").write_text(json.dumps(notes), encoding="utf-8")

    item = _queue(mutated(drop_waiver))["CL-0007"]
    assert item["urgency"]["score"] > baseline


def test_a_genuine_totals_disagreement_is_reported(mutated, cases_by_client):
    baseline_confidence = cases_by_client["CL-0008"].confidence.score

    def corrupt(target: Path) -> None:
        frame = pd.read_csv(target / "clients.csv")
        frame.loc[frame.client_id == "CL-0008", "total_aum_usd"] = 5_000_000.0
        frame.to_csv(target / "clients.csv", index=False)

    payload = mutated(corrupt)
    conflicts = [c for p in _packets(payload, "CL-0008") for c in p["conflicts"]]
    assert conflicts, "a real disagreement must surface as a conflict"
    case = {c["clientId"]: c for c in payload["clientCases"]}["CL-0008"]
    assert case["confidence"]["score"] < baseline_confidence
    assert any(
        issue["id"] == "DQ-TOTALS-DISAGREE"
        for issue in payload["meta"]["dataQuality"]["issues"]
    )


def test_a_missing_lending_value_never_fabricates_a_ratio(mutated):
    def blank(target: Path) -> None:
        frame = pd.read_csv(target / "credit_facilities.csv")
        frame.loc[frame.facility_id == "CF-0002", "lending_value_2026-08-26"] = 0.0
        frame.to_csv(target / "credit_facilities.csv", index=False)

    payload = mutated(blank)
    blob = json.dumps(
        [p for p in _packets(payload, "CL-0014") if p["signalType"] == "credit"]
    )
    assert "cannot be calculated" in blob
    assert "Infinity" not in blob and "NaN" not in blob


def test_an_orphan_reference_is_reported(mutated):
    def orphan(target: Path) -> None:
        frame = pd.read_csv(target / "holdings.csv")
        row = frame.iloc[[0]].copy()
        row["instrument_id"] = "SYN-XX-9999"
        pd.concat([frame, row]).to_csv(target / "holdings.csv", index=False)

    payload = mutated(orphan)
    assert any(
        issue["id"] == "DQ-REF-HOLDING-INSTRUMENT"
        for issue in payload["meta"]["dataQuality"]["issues"]
    )


def test_broken_holding_arithmetic_is_caught(mutated):
    def broken(target: Path) -> None:
        frame = pd.read_csv(target / "holdings.csv")
        frame.loc[0, "market_value_local"] = frame.loc[0, "market_value_local"] * 3
        frame.to_csv(target / "holdings.csv", index=False)

    payload = mutated(broken)
    assert any(
        issue["id"] == "DQ-ARITHMETIC-MARKET-VALUE"
        for issue in payload["meta"]["dataQuality"]["issues"]
    )


def test_a_missing_source_file_fails_loudly(tmp_path, data_dir):
    target = tmp_path / "data"
    shutil.copytree(data_dir, target)
    (target / "mandates.csv").unlink()
    with pytest.raises(FileNotFoundError, match="mandates.csv"):
        load_challenge_data(target)
