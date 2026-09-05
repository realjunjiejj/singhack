"""Google Gemini integration for the multi-agent intelligence layer.

Enables Gemini 2.5 Pro (and other Gemini models) to act as specialist narrative
agents while strictly enforcing the private-bank evidence and safety boundary.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from jb_clarity.intelligence.provider import NarrativeDraft, NarrativeRequest

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_API_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class GeminiNarrativeProvider:
    """Narrative provider that queries Google Gemini for specialist agent language."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_GEMINI_MODEL,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        if not self.api_key:
            raise ValueError(
                "GeminiNarrativeProvider requires an API key. Pass api_key or set GEMINI_API_KEY."
            )
        self.model = model
        self.timeout = timeout

    def generate(self, request: NarrativeRequest) -> NarrativeDraft:
        """Call Gemini to generate a validated specialist narrative draft."""
        prompt = self._build_prompt(request)
        system_instruction = self._build_system_instruction(request)
        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "summary": {"type": "STRING"},
                        "why_it_matters": {"type": "STRING"},
                        "evidence_item_ids": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"},
                        },
                    },
                    "required": ["summary", "why_it_matters", "evidence_item_ids"],
                },
            },
        }

        raw_response = self._call_gemini_api(payload)
        return self._parse_response(raw_response)

    def _build_system_instruction(self, request: NarrativeRequest) -> str:
        return (
            "You are a Senior Wealth Advisory Specialist in Julius Baer Clarity assisting "
            "Relationship Manager (RM) Priscilla Ong.\n"
            "Your role is to explain already-calculated portfolio findings with utmost precision.\n\n"
            "STRICT PRIVATE BANKING RULES:\n"
            "1. NEVER invent, modify, or round financial figures (amounts, currencies, percentages, dates).\n"
            "2. All figures must match the canonical facts exactly.\n"
            "3. Cite ONLY Evidence Item IDs from the provided allowed list.\n"
            "4. Be concise, professional, and explain the 'Why Now' from the client's perspective.\n"
            "5. Do NOT provide autonomous trading advice or execute actions; prepare the RM for conversation."
        )

    def _build_prompt(self, request: NarrativeRequest) -> str:
        return (
            f"Agent Role: {request.agent_id}\n"
            f"Task: {request.fixed_task}\n"
            f"Client ID: {request.client_id} (Case: {request.case_id})\n\n"
            f"Canonical Finding Summary:\n{request.canonical_summary}\n\n"
            f"Canonical 'Why It Matters':\n{request.canonical_why_it_matters}\n\n"
            f"Allowed Evidence Item IDs to cite:\n"
            + "\n".join(f"- {item_id}" for item_id in request.allowed_evidence_item_ids)
            + "\n\nProvide the refined summary, why_it_matters, and the cited evidence_item_ids as JSON."
        )

    def _call_gemini_api(self, payload: dict[str, Any]) -> str:
        import time

        url = f"{GEMINI_API_ENDPOINT.format(model=self.model)}?key={self.api_key}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    return response.read().decode("utf-8")
            except urllib.error.HTTPError as error:
                if error.code == 429 and attempt < max_retries - 1:
                    time.sleep(2.0 * (attempt + 1))
                    continue
                error_body = error.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"Gemini API returned HTTP {error.code}: {error_body}"
                ) from error
            except urllib.error.URLError as error:
                raise RuntimeError(
                    f"Gemini API connection error: {error.reason}"
                ) from error

    def _parse_response(self, raw_json: str) -> NarrativeDraft:
        data = json.loads(raw_json)
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("No candidates returned by Gemini API.")
            text = candidates[0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
            return NarrativeDraft(
                summary=parsed["summary"],
                why_it_matters=parsed["why_it_matters"],
                evidence_item_ids=parsed.get("evidence_item_ids", []),
            )
        except (KeyError, IndexError, json.JSONDecodeError) as error:
            raise ValueError(
                f"Failed to parse Gemini structured output: {error}"
            ) from error
