"""Profile an incoming dataset and select an explicit ingestion adapter.

The profiler inspects file metadata and headers. It never asks a model to guess
that an arbitrary column represents a client, portfolio, price, or obligation.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from jb_clarity.ingestion.loader import REQUIRED_FILES
from jb_clarity.intelligence.models import DatasetFileProfile, DatasetProfile

CHALLENGE_ADAPTER_ID = "jb-wealth-challenge-v1"


def profile_dataset(source: Path | str) -> DatasetProfile:
    root = Path(source)
    if not root.is_dir():
        return DatasetProfile(source=root.name or ".", files=[])

    files = [_profile_file(path) for path in sorted(root.iterdir()) if path.is_file()]
    return DatasetProfile(source=root.name or ".", files=files)


def select_adapter(profile: DatasetProfile) -> tuple[str | None, list[str]]:
    names = {file.name for file in profile.files}
    missing = sorted(set(REQUIRED_FILES) - names)
    if missing:
        return None, missing
    return CHALLENGE_ADAPTER_ID, []


def _profile_file(path: Path) -> DatasetFileProfile:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)

    suffix = path.suffix.lower()
    columns: list[str] = []
    row_count: int | None = None
    media_type = "application/octet-stream"

    if suffix == ".csv":
        media_type = "text/csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            columns = next(reader, [])
            row_count = sum(1 for _ in reader)
    elif suffix == ".json":
        media_type = "application/json"
        try:
            with path.open(encoding="utf-8") as handle:
                value = json.load(handle)
            if isinstance(value, list):
                row_count = len(value)
                if value and isinstance(value[0], dict):
                    columns = sorted(str(key) for key in value[0])
            elif isinstance(value, dict):
                row_count = 1
                columns = sorted(str(key) for key in value)
        except (json.JSONDecodeError, UnicodeDecodeError):
            row_count = None

    return DatasetFileProfile(
        name=path.name,
        media_type=media_type,
        size_bytes=path.stat().st_size,
        sha256=digest.hexdigest(),
        row_count=row_count,
        columns=columns,
    )
