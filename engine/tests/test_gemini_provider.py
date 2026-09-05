"""Tests for Google Gemini integration in the multi-agent intelligence layer."""

from __future__ import annotations

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from jb_clarity import analyse_dataset
from jb_clarity.intelligence.gemini import GeminiNarrativeProvider
from jb_clarity.intelligence.provider import (
    NarrativeDraft,
    NarrativeRequest,
    default_narrative_policy,
)


def _sample_request() -> NarrativeRequest:
    return NarrativeRequest(
        task_id="TASK-CL-0001",
        agent_id="hidden-risk-specialist",
        fixed_task="Explain this finding.",
        client_id="CL-0001",
        case_id="CASE-CL-0001",
        canonical_summary="Hartono holds 44.99% energy across portfolios.",
        canonical_why_it_matters="High concentration in volatile commodity.",
        allowed_evidence_packet_ids=["PACKET-CL-0001-CONCENTRATION"],
        allowed_evidence_item_ids=["EV-CL-0001-CONCENTRATION-01"],
    )


def test_gemini_provider_requires_an_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="requires an API key"):
        GeminiNarrativeProvider()


def test_gemini_provider_formats_payload_and_parses_response():
    provider = GeminiNarrativeProvider(api_key="test-key", model="gemini-2.5-pro")
    mock_response_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "summary": "Hartono holds 44.99% energy across portfolios.",
                                    "why_it_matters": "High concentration in volatile commodity.",
                                    "evidence_item_ids": [
                                        "EV-CL-0001-CONCENTRATION-01"
                                    ],
                                }
                            )
                        }
                    ]
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_response_payload).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        draft = provider.generate(_sample_request())

        assert isinstance(draft, NarrativeDraft)
        assert draft.summary == "Hartono holds 44.99% energy across portfolios."
        assert draft.evidence_item_ids == ["EV-CL-0001-CONCENTRATION-01"]

        # Verify call arguments
        req = mock_urlopen.call_args[0][0]
        assert "gemini-2.5-pro" in req.full_url
        assert "key=test-key" in req.full_url
        sent_body = json.loads(req.data.decode("utf-8"))
        assert sent_body["generationConfig"]["responseMimeType"] == "application/json"
        assert (
            "Senior Wealth Advisory Specialist"
            in sent_body["systemInstruction"]["parts"][0]["text"]
        )


def test_gemini_provider_handles_http_errors():
    provider = GeminiNarrativeProvider(api_key="test-key")
    error = urllib.error.HTTPError(
        url="http://test",
        code=429,
        msg="Too Many Requests",
        hdrs={},
        fp=io.BytesIO(b'{"error": "Quota exceeded"}'),
    )

    with patch("urllib.request.urlopen", side_effect=error):
        with pytest.raises(RuntimeError, match="HTTP 429"):
            provider.generate(_sample_request())


def test_gemini_provider_e2e_with_analyse_dataset(data_dir, model):
    def fake_urlopen(req, timeout=None):
        body = json.loads(req.data.decode("utf-8"))
        prompt = body["contents"][0]["parts"][0]["text"]

        # Extract canonical summary and why it matters from prompt
        lines = prompt.splitlines()
        summary = ""
        why_it_matters = ""
        for i, line in enumerate(lines):
            if line.startswith("Canonical Finding Summary:"):
                summary = lines[i + 1]
            elif line.startswith("Canonical 'Why It Matters':"):
                why_it_matters = lines[i + 1]

        items = [line[2:] for line in lines if line.startswith("- EV-")]

        mock_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "summary": summary,
                                        "why_it_matters": why_it_matters,
                                        "evidence_item_ids": items[:1],
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    provider = GeminiNarrativeProvider(api_key="test-key", model="gemini-2.5-pro")

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        result = analyse_dataset(
            data_dir,
            clock=lambda: model.meta.generated_at,
            narrative_provider=provider,
            narrative_policy=default_narrative_policy,
        )

        assert result.status == "completed"
        hidden = next(
            r for r in result.agent_reports if r.agent_id == "hidden-risk-specialist"
        )
        assert any(
            finding.narrative_source == "model-validated" for finding in hidden.findings
        )
