"""Local upload API behavior."""

from __future__ import annotations

from fastapi.testclient import TestClient

from jb_clarity.api import app
from jb_clarity.ingestion.loader import REQUIRED_FILES


def test_health_reports_optional_gemini(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["geminiConfigured"] is False


def test_canonical_upload_runs_analysis_automatically(data_dir):
    uploads = []
    for name in REQUIRED_FILES:
        media_type = "application/json" if name.endswith(".json") else "text/csv"
        uploads.append(("files", (name, (data_dir / name).read_bytes(), media_type)))
    response = TestClient(app).post("/analyse", files=uploads, data={"live_ai": "false"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["deepFocus"] == ["hidden-risk", "prioritisation"]
    assert payload["workbench"]["book"]["clientCount"] == 20
    assert any(report["agentId"] == "advisory-opportunity-analyst" for report in payload["agentReports"])


def test_live_ai_requires_server_key(monkeypatch, data_dir):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    uploads = [("files", (name, (data_dir / name).read_bytes(), "application/octet-stream")) for name in REQUIRED_FILES]
    response = TestClient(app).post("/analyse", files=uploads, data={"live_ai": "true"})
    assert response.status_code == 409
    assert "GEMINI_API_KEY" in response.json()["detail"]
