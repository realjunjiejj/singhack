"""Operator-facing commands.

`validate-data` exists so someone can point the engine at a Book and find out
whether it will build, and why not, without producing an artifact.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from fixtures import second_book
from jb_clarity.cli import main


@pytest.fixture
def book(tmp_path) -> Path:
    return second_book.write_book(tmp_path / "book")


def test_validate_reports_a_healthy_book(book, capsys):
    assert main(["validate-data", "--data", str(book)]) == 0
    out = capsys.readouterr().out
    assert "Canonical source contract : v1.0.0" in out
    assert "RM-ZH-401" in out
    assert "clients                 : 4" in out
    assert "portfolios              : 5" in out
    assert "snapshots               : 4 (2025-06-30 to 2026-03-31)" in out
    assert "Generation may proceed." in out


def test_validate_lists_resolved_source_filenames(book, capsys):
    main(["validate-data", "--data", str(book)])
    out = capsys.readouterr().out
    assert "clients.csv" in out and "present" in out
    assert "rm_notes.json" in out


def test_validate_reports_capabilities(book, capsys):
    main(["validate-data", "--data", str(book)])
    out = capsys.readouterr().out
    assert "enabled  credit and collateral stress test" in out
    assert "enabled  event-grounded explanation" in out


def test_validate_never_prints_note_contents(book, capsys):
    """Validation output must be safe to paste into a ticket."""
    main(["validate-data", "--data", str(book)])
    out = capsys.readouterr().out
    for note in second_book.NOTES:
        assert note["note"] not in out
    assert "engineering stake" not in out


def test_validate_surfaces_unmapped_event_channels(book, capsys):
    main(["validate-data", "--data", str(book)])
    out = capsys.readouterr().out
    assert "DQ-UNMAPPED-EVENT-CHANNEL" in out
    assert "Sovereign wealth flows" in out


def test_validate_blocks_on_a_missing_core_file(book, capsys):
    (book / "holdings.csv").unlink()
    assert main(["validate-data", "--data", str(book)]) == 1
    assert "BLOCKED" in capsys.readouterr().err


def test_validate_blocks_on_a_missing_required_column(book, capsys):
    frame = pd.read_csv(book / "clients.csv").drop(columns=["risk_profile"])
    frame.to_csv(book / "clients.csv", index=False)
    assert main(["validate-data", "--data", str(book)]) == 1
    err = capsys.readouterr().err
    assert "clients.csv is missing required column" in err
    assert "risk_profile" in err


def test_validate_blocks_on_an_invalid_date(book, capsys):
    notes = json.loads((book / "rm_notes.json").read_text(encoding="utf-8"))
    notes[0]["note_date"] = "March 2026"
    (book / "rm_notes.json").write_text(json.dumps(notes), encoding="utf-8")
    assert main(["validate-data", "--data", str(book)]) == 1
    assert "not an ISO date" in capsys.readouterr().err


def test_validate_blocks_a_single_snapshot_book(book, capsys):
    holdings = pd.read_csv(book / "holdings.csv")
    latest = holdings[holdings.snapshot_date == second_book.AS_OF]
    latest.to_csv(book / "holdings.csv", index=False)
    assert main(["validate-data", "--data", str(book)]) == 1
    assert "At least 2 distinct dates" in capsys.readouterr().err


def test_validate_blocks_an_ambiguous_multi_rm_dataset(book, capsys):
    """Two RMs in one directory is a Book-selection question, not a default."""
    clients = pd.read_csv(book / "clients.csv")
    clients.loc[clients.client_id == "MW-C-400", "rm_id"] = "RM-GE-902"
    clients.loc[clients.client_id == "MW-C-400", "rm_name"] = "Tomas Horak"
    clients.to_csv(book / "clients.csv", index=False)

    assert main(["validate-data", "--data", str(book)]) == 1
    err = capsys.readouterr().err
    assert "more than one relationship manager" in err
    assert "RM-ZH-401" in err and "RM-GE-902" in err


def test_build_still_produces_an_artifact(book, tmp_path, capsys):
    output = tmp_path / "out.json"
    code = main([
        "build",
        "--data", str(book),
        "--as-of", second_book.AS_OF,
        "--generated-at", "2026-04-01T00:00:00+00:00",
        "--output", str(output),
    ])
    assert code == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["meta"]["artifactKind"] == "generated"
    assert len(payload["book"]["priorityQueue"]) == 4
    assert "clients ranked : 4" in capsys.readouterr().out


def test_build_rejects_a_dataset_the_validator_would_block(book, tmp_path):
    shutil.rmtree(book / "holdings.csv", ignore_errors=True)
    (book / "holdings.csv").unlink(missing_ok=True)
    with pytest.raises(FileNotFoundError):
        main([
            "build",
            "--data", str(book),
            "--as-of", second_book.AS_OF,
            "--output", str(tmp_path / "out.json"),
        ])
