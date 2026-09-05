"""Safely normalise explicit CSV/JSON or Excel uploads for analysis."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path

import pandas as pd

from jb_clarity.ingestion.loader import REQUIRED_FILES

MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
ALLOWED_SUFFIXES = {".csv", ".json", ".xlsx", ".xls"}
CANONICAL_STEMS = {Path(name).stem: name for name in REQUIRED_FILES}


class UploadDatasetError(ValueError):
    """An uploaded bundle cannot be mapped safely to the known adapter."""


@dataclass(frozen=True)
class UploadedFile:
    name: str
    content: bytes


def normalise_uploaded_dataset(files: list[UploadedFile], target: Path) -> list[str]:
    """Write an explicit canonical dataset into ``target`` and return its files.

    CSV/JSON filenames must match the canonical challenge names. An Excel file
    may either be named after one canonical table or contain sheets named after
    canonical tables. Column meaning is never inferred from arbitrary names.
    """
    if not files:
        raise UploadDatasetError("Select at least one CSV, JSON, XLSX, or XLS file.")
    total = sum(len(file.content) for file in files)
    if total > MAX_UPLOAD_BYTES:
        raise UploadDatasetError("The upload exceeds the 100 MB local analysis limit.")

    target.mkdir(parents=True, exist_ok=True)
    written: set[str] = set()
    for upload in files:
        safe_name = Path(upload.name).name
        if safe_name != upload.name or not safe_name:
            raise UploadDatasetError(f"Unsafe filename rejected: {upload.name!r}.")
        if len(upload.content) > MAX_FILE_BYTES:
            raise UploadDatasetError(f"{safe_name} exceeds the 25 MB per-file limit.")
        suffix = Path(safe_name).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise UploadDatasetError(f"Unsupported file type for {safe_name}. Use CSV, JSON, XLSX, or XLS.")
        if suffix in {".xlsx", ".xls"}:
            _write_workbook(upload, target, written)
        else:
            canonical = _canonical_filename(safe_name)
            _claim(canonical, written)
            _validate_text_payload(canonical, upload.content)
            (target / canonical).write_bytes(upload.content)

    missing = sorted(set(REQUIRED_FILES) - written)
    if missing:
        raise UploadDatasetError(
            "Dataset is incomplete. Missing canonical tables: " + ", ".join(missing)
        )
    return sorted(written)


def latest_snapshot_date(dataset: Path) -> date:
    frame = pd.read_csv(dataset / "holdings.csv", usecols=["snapshot_date"], dtype=str)
    values = pd.to_datetime(frame["snapshot_date"], errors="coerce").dropna()
    if values.empty:
        raise UploadDatasetError("holdings.csv has no valid snapshot_date values.")
    return values.max().date()


def _canonical_filename(name: str) -> str:
    match = next((item for item in REQUIRED_FILES if item.casefold() == name.casefold()), None)
    if match is None:
        raise UploadDatasetError(
            f"Unrecognised table {name}. Keep canonical filenames such as clients.csv or holdings.csv."
        )
    return match


def _write_workbook(upload: UploadedFile, target: Path, written: set[str]) -> None:
    try:
        workbook = pd.ExcelFile(BytesIO(upload.content))
    except Exception as error:
        raise UploadDatasetError(f"Could not read Excel workbook {upload.name}: {error}") from error

    named_sheets = {
        sheet: CANONICAL_STEMS.get(Path(sheet).stem.casefold())
        for sheet in workbook.sheet_names
    }
    canonical_sheets = {sheet: name for sheet, name in named_sheets.items() if name is not None}
    file_target = CANONICAL_STEMS.get(Path(upload.name).stem.casefold())

    if canonical_sheets:
        for sheet, canonical in canonical_sheets.items():
            _write_frame(workbook.parse(sheet), canonical, target, written)
        return
    if file_target is not None:
        _write_frame(workbook.parse(workbook.sheet_names[0]), file_target, target, written)
        return
    raise UploadDatasetError(
        f"{upload.name} has no recognised sheet. Name sheets clients, holdings, portfolios, and the other canonical tables."
    )


def _write_frame(frame: pd.DataFrame, canonical: str, target: Path, written: set[str]) -> None:
    _claim(canonical, written)
    if canonical.endswith(".json"):
        records = json.loads(frame.to_json(orient="records", date_format="iso"))
        (target / canonical).write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    else:
        frame.to_csv(target / canonical, index=False)


def _claim(canonical: str, written: set[str]) -> None:
    if canonical in written:
        raise UploadDatasetError(f"Duplicate canonical table supplied: {canonical}.")
    written.add(canonical)


def _validate_text_payload(canonical: str, content: bytes) -> None:
    try:
        text = content.decode("utf-8-sig")
        if canonical.endswith(".json"):
            value = json.loads(text)
            if not isinstance(value, list):
                raise UploadDatasetError(f"{canonical} must contain a JSON array of records.")
        elif not text.strip():
            raise UploadDatasetError(f"{canonical} is empty.")
    except UnicodeDecodeError as error:
        raise UploadDatasetError(f"{canonical} must be UTF-8 encoded.") from error
    except json.JSONDecodeError as error:
        raise UploadDatasetError(f"{canonical} is not valid JSON: {error.msg}.") from error
