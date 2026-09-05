"""Local HTTP boundary for uploaded dataset analysis."""

from __future__ import annotations

import os
from datetime import date
from tempfile import TemporaryDirectory

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from jb_clarity.intelligence.entrypoint import analyse_dataset
from jb_clarity.intelligence.provider import default_narrative_policy, get_gemini_provider
from jb_clarity.intelligence.upload import (
    MAX_FILE_BYTES,
    MAX_UPLOAD_BYTES,
    UploadDatasetError,
    UploadedFile,
    latest_snapshot_date,
    normalise_uploaded_dataset,
)

app = FastAPI(title="AAActual Intelligence analysis API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _gemini_configured() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


@app.get("/health")
def health() -> dict:
    return {
        "status": "ready",
        "geminiConfigured": _gemini_configured(),
        "acceptedFormats": ["csv", "json", "xlsx", "xls"],
        "maxFileBytes": MAX_FILE_BYTES,
        "maxUploadBytes": MAX_UPLOAD_BYTES,
    }


@app.post("/analyse")
async def analyse(
    files: list[UploadFile] = File(...),
    live_ai: bool = Form(False),
    as_of_date: date | None = Form(None),
) -> JSONResponse:
    if live_ai and not _gemini_configured():
        raise HTTPException(
            status_code=409,
            detail="Live Gemini analysis was requested but GEMINI_API_KEY is not configured on the server.",
        )

    uploaded: list[UploadedFile] = []
    running_total = 0
    for file in files:
        content = await file.read(MAX_FILE_BYTES + 1)
        running_total += len(content)
        if len(content) > MAX_FILE_BYTES or running_total > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Uploaded dataset exceeds the configured size limit.")
        uploaded.append(UploadedFile(name=file.filename or "", content=content))

    try:
        with TemporaryDirectory(prefix="jb-clarity-upload-") as directory:
            from pathlib import Path

            dataset = Path(directory)
            await run_in_threadpool(normalise_uploaded_dataset, uploaded, dataset)
            effective_date = as_of_date or await run_in_threadpool(latest_snapshot_date, dataset)
            provider = get_gemini_provider() if live_ai else None
            policy = default_narrative_policy if live_ai else None
            result = await run_in_threadpool(
                analyse_dataset,
                dataset,
                effective_date,
                narrative_provider=provider,
                narrative_policy=policy,
            )
    except UploadDatasetError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (ValueError, KeyError) as error:
        raise HTTPException(status_code=422, detail=f"Dataset validation failed: {error}") from error

    payload = result.to_contract_dict()
    status_code = 200 if result.status in {"completed", "partial"} and result.workbench is not None else 422
    return JSONResponse(payload, status_code=status_code)
