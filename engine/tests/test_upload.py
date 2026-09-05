from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest

from jb_clarity.ingestion.loader import REQUIRED_FILES
from jb_clarity.intelligence.upload import (
    UploadDatasetError,
    UploadedFile,
    latest_snapshot_date,
    normalise_uploaded_dataset,
)


def _source_files(data_dir: Path) -> list[UploadedFile]:
    return [UploadedFile(name=name, content=(data_dir / name).read_bytes()) for name in REQUIRED_FILES]


def test_normalises_canonical_upload_and_finds_latest_snapshot(data_dir: Path, tmp_path: Path):
    written = normalise_uploaded_dataset(_source_files(data_dir), tmp_path)
    assert written == sorted(REQUIRED_FILES)
    assert latest_snapshot_date(tmp_path).isoformat() == "2026-08-26"


def test_rejects_incomplete_dataset(data_dir: Path, tmp_path: Path):
    files = [file for file in _source_files(data_dir) if file.name != "holdings.csv"]
    with pytest.raises(UploadDatasetError, match="holdings.csv"):
        normalise_uploaded_dataset(files, tmp_path)


def test_normalises_excel_workbook_with_canonical_sheet_names(data_dir: Path, tmp_path: Path):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name in REQUIRED_FILES:
            source = data_dir / name
            if name.endswith(".json"):
                frame = pd.read_json(source)
            else:
                frame = pd.read_csv(source)
            frame.to_excel(writer, sheet_name=Path(name).stem, index=False)

    written = normalise_uploaded_dataset([UploadedFile("customer-book.xlsx", buffer.getvalue())], tmp_path)
    assert written == sorted(REQUIRED_FILES)
    assert pd.read_csv(tmp_path / "clients.csv").shape[0] == 20
    assert (tmp_path / "rm_notes.json").read_text(encoding="utf-8").startswith("[")
