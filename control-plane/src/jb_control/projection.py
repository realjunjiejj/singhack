"""Model-input projection: what an Evidence Packet becomes before generation.

This is the data-minimisation boundary. It is an allowlist, not a blocklist,
so a field added to the Workbench contract next month is dropped by default
rather than silently forwarded.

The most important exclusion is `items`. Evidence items carry source record
keys and raw values — including RM note excerpts, which are client-influenced
text. The model receives engine-authored claim statements and citation
identifiers, and resolves nothing itself.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from jb_control.errors import OutputValidationError, ProjectionError

# src/jb_control/projection.py -> src/jb_control -> src -> control-plane
CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"


@lru_cache(maxsize=2)
def load_classification(path: str | None = None) -> dict[str, Any]:
    target = Path(path) if path else CONTRACTS_DIR / "data-classification.json"
    with target.open(encoding="utf-8") as handle:
        return json.load(handle)


# Identifiers that must be tokenised before they reach a model. The engine's
# own identifiers are pseudonymous already; a client's name is not.
_REDACTIONS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("[EMAIL]", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("[PHONE]", re.compile(r"\+?\d[\d ()-]{7,}\d")),
    ("[IBAN]", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")),
)


@dataclass
class Redactor:
    """A narrow redaction interface.

    Presidio is the intended implementation and is defence in depth, not
    complete detection. The pattern set here is deliberately small and named,
    so nobody mistakes it for comprehensive coverage.
    """

    extra_terms: tuple[str, ...] = ()

    def redact(self, text: str) -> str:
        cleaned = text
        for token, pattern in _REDACTIONS:
            cleaned = pattern.sub(token, cleaned)
        for term in self.extra_terms:
            if term:
                cleaned = re.sub(re.escape(term), "[NAME]", cleaned, flags=re.IGNORECASE)
        return cleaned


@dataclass
class ModelInput:
    """The bounded payload a language adapter may receive."""

    task: str
    packet: dict[str, Any]
    allowed_citation_ids: frozenset[str] = field(default_factory=frozenset)

    def as_dict(self) -> dict[str, Any]:
        return {"task": self.task, "packet": self.packet}


PERMITTED_TASKS = frozenset(
    {"explain_case", "draft_meeting_brief", "translate_approved_draft"}
)


def project_packet(
    packet: dict[str, Any],
    *,
    task: str,
    redactor: Redactor | None = None,
    classification: dict[str, Any] | None = None,
) -> ModelInput:
    """Reduce an Evidence Packet to the minimum the task needs.

    Raises rather than degrading: if the packet cannot be projected safely the
    call is refused, because the failure mode of "send a bit more" is exactly
    what this boundary exists to prevent.
    """
    if task not in PERMITTED_TASKS:
        raise ProjectionError("unknown_task")
    if not isinstance(packet, dict) or not packet:
        raise ProjectionError("packet_missing")

    rules = (classification or load_classification())["modelInputAllowlist"]
    redactor = redactor or Redactor()

    projected: dict[str, Any] = {}
    for name in rules["packetFields"]:
        if name in packet:
            projected[name] = packet[name]
    if "packetId" not in projected:
        raise ProjectionError("packet_identity_missing")

    citation_ids: set[str] = set()
    claim_fields = rules["claimFields"]

    for collection in rules["claimCollections"]:
        claims = packet.get(collection) or []
        if not isinstance(claims, list):
            raise ProjectionError(f"malformed_collection:{collection}")
        reduced = []
        for claim in claims:
            if not isinstance(claim, dict):
                raise ProjectionError(f"malformed_claim:{collection}")
            entry: dict[str, Any] = {}
            for name in claim_fields:
                if name not in claim:
                    continue
                value = claim[name]
                # Claim statements are engine-authored, but they are the only
                # free text crossing the boundary, so they still get redacted.
                entry[name] = redactor.redact(value) if name == "statement" else value
            citation_ids.update(entry.get("evidenceItemIds", []) or [])
            reduced.append(entry)
        if reduced:
            projected[collection] = reduced

    metrics = packet.get("derivedMetrics") or []
    if metrics:
        projected["derivedMetrics"] = [
            {name: metric[name] for name in rules["derivedMetricFields"] if name in metric}
            for metric in metrics
            if isinstance(metric, dict)
        ]

    # Belt and braces: nothing on the denied list may survive, whatever the
    # allowlist happens to contain.
    for denied in rules["deniedFields"]:
        projected.pop(denied, None)

    return ModelInput(
        task=task, packet=projected, allowed_citation_ids=frozenset(citation_ids)
    )


_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _figures(text: str) -> list[str]:
    return [match.group().replace(",", "") for match in _NUMBER.finditer(text)]


def validate_generated(
    output: dict[str, Any],
    model_input: ModelInput,
    *,
    canonical_text: str | None = None,
) -> dict[str, Any]:
    """Check generated content before any human sees it.

    Three failures matter: a citation the packet does not contain, a figure the
    canonical text does not contain, and a missing structure. Any of them fails
    closed to the cached draft.
    """
    if not isinstance(output, dict):
        raise OutputValidationError("output_not_structured")

    text = output.get("content")
    if not isinstance(text, str) or not text.strip():
        raise OutputValidationError("output_empty")

    cited = output.get("citedEvidenceItemIds")
    if not isinstance(cited, list) or not cited:
        raise OutputValidationError("output_uncited")

    unknown = sorted(set(cited) - model_input.allowed_citation_ids)
    if unknown:
        raise OutputValidationError("citation_outside_packet")

    if canonical_text is not None:
        introduced = sorted(set(_figures(text)) - set(_figures(canonical_text)))
        if introduced:
            raise OutputValidationError("figure_not_in_canonical")

    return output
