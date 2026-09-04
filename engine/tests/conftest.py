"""Shared fixtures.

The suite exercises the real supplied dataset through the highest behavioural
seam. Building once per session keeps the run fast without weakening what is
being tested.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from jb_clarity.build import build_workbench
from jb_clarity.config import load_scoring_config
from jb_clarity.ingestion.loader import load_challenge_data
from jb_clarity.ingestion.validation import validate

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "singhacks-jb-wealth-intelligence" / "data"
SCHEMA_PATH = REPO_ROOT / "contracts" / "workbench.schema.json"
AS_OF = date(2026, 8, 26)
FIXED_CLOCK = lambda: datetime(2026, 9, 4, tzinfo=timezone.utc)  # noqa: E731


@pytest.fixture(scope="session")
def data_dir() -> Path:
    assert DATA_DIR.exists(), f"Challenge data not found at {DATA_DIR}"
    return DATA_DIR


@pytest.fixture(scope="session")
def challenge_data(data_dir: Path):
    return load_challenge_data(data_dir)


@pytest.fixture(scope="session")
def validation_report(challenge_data):
    return validate(challenge_data)


@pytest.fixture(scope="session")
def config() -> dict:
    return load_scoring_config()


@pytest.fixture(scope="session")
def model(data_dir: Path):
    return build_workbench(data_dir, AS_OF, clock=FIXED_CLOCK)


@pytest.fixture(scope="session")
def artifact(model) -> dict:
    return model.to_contract_dict()


@pytest.fixture(scope="session")
def schema() -> dict:
    with SCHEMA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture(scope="session")
def cases_by_client(model) -> dict:
    return {case.client_id: case for case in model.client_cases}


@pytest.fixture(scope="session")
def queue_by_client(model) -> dict:
    return {item.client_id: item for item in model.book.priority_queue}


@pytest.fixture(scope="session")
def packets_by_client(model) -> dict:
    grouped: dict[str, list] = {}
    for packet in model.evidence_packets:
        grouped.setdefault(packet.client_id, []).append(packet)
    return grouped
