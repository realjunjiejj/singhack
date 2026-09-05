"""Optional model seam for bounded, validated specialist narratives."""

from __future__ import annotations

from typing import Callable, Protocol

from pydantic import Field

from jb_clarity.domain.models import Contract
from jb_clarity.intelligence.models import AgentReport, AnalysisDiagnostic
from jb_clarity.language.validator import validate_draft


class NarrativeRequest(Contract):
    task_id: str
    agent_id: str
    fixed_task: str
    client_id: str
    case_id: str
    canonical_summary: str
    canonical_why_it_matters: str
    allowed_evidence_packet_ids: list[str] = Field(default_factory=list)
    allowed_evidence_item_ids: list[str] = Field(default_factory=list)


NarrativePolicy = Callable[[NarrativeRequest], NarrativeRequest]


def default_narrative_policy(request: NarrativeRequest) -> NarrativeRequest:
    """Standard private-bank narrative projection policy.

    Ensures only bounded, allowed Evidence Item IDs and canonical summaries
    are projected to the language model.
    """
    return request.model_copy()


class NarrativeDraft(Contract):
    summary: str
    why_it_matters: str
    evidence_item_ids: list[str] = Field(default_factory=list)


class NarrativeProvider(Protocol):
    """Adapter implemented by a local or hosted language-model gateway."""

    def generate(self, request: NarrativeRequest) -> NarrativeDraft: ...


def get_gemini_provider(
    api_key: str | None = None, model: str = "gemini-3.8-flash"
) -> NarrativeProvider:
    from jb_clarity.intelligence.gemini import GeminiNarrativeProvider

    return GeminiNarrativeProvider(api_key=api_key, model=model)


def enrich_deep_reports(
    reports: list[AgentReport],
    provider: NarrativeProvider,
    policy: NarrativePolicy | None = None,
) -> list[AgentReport]:
    """Apply validated model language to deep findings only.

    The provider cannot alter calculations, metrics, Urgency, Confidence, rank,
    or Evidence Packet membership. Invalid or unavailable language is dropped.
    """
    enriched: list[AgentReport] = []
    for report in reports:
        if report.depth != "deep":
            enriched.append(report)
            continue

        findings = []
        diagnostics = list(report.diagnostics)
        for finding in report.findings:
            request = NarrativeRequest(
                task_id=f"TASK-{finding.finding_id}",
                agent_id=report.agent_id,
                fixed_task=(
                    "Explain this already-calculated finding for an RM. Preserve "
                    "the figures, cite only allowed evidence, surface uncertainty, "
                    "and do not add advice, rank, or facts."
                ),
                client_id=finding.client_id,
                case_id=finding.case_id,
                canonical_summary=finding.summary,
                canonical_why_it_matters=finding.why_it_matters,
                allowed_evidence_packet_ids=finding.evidence_packet_ids,
                allowed_evidence_item_ids=finding.evidence_item_ids,
            )
            projected = policy(request) if policy is not None else request
            try:
                draft = provider.generate(projected)
            except (
                Exception
            ) as error:  # model adapters are outside the engine's trust zone
                diagnostics.append(
                    AnalysisDiagnostic(
                        code="MODEL-PROVIDER-UNAVAILABLE",
                        severity="warning",
                        message=(
                            f"{finding.finding_id} kept deterministic language because "
                            f"the optional provider failed: {type(error).__name__}."
                        ),
                    )
                )
                findings.append(finding)
                continue

            errors = _validate_draft(request, draft)
            if errors:
                diagnostics.append(
                    AnalysisDiagnostic(
                        code="MODEL-OUTPUT-REJECTED",
                        severity="warning",
                        message=f"{finding.finding_id}: {'; '.join(errors)}",
                    )
                )
                findings.append(finding)
                continue

            findings.append(
                finding.model_copy(
                    update={
                        "summary": draft.summary,
                        "why_it_matters": draft.why_it_matters,
                        "narrative_source": "model-validated",
                        "narrative_evidence_item_ids": draft.evidence_item_ids,
                    }
                )
            )
        enriched.append(
            report.model_copy(update={"findings": findings, "diagnostics": diagnostics})
        )
    return enriched


def _validate_draft(request: NarrativeRequest, draft: NarrativeDraft) -> list[str]:
    result = validate_draft(
        draft.summary + " " + draft.why_it_matters,
        request.canonical_summary + " " + request.canonical_why_it_matters,
        draft.evidence_item_ids,
        set(request.allowed_evidence_item_ids),
    )
    errors = list(result.errors)
    if not draft.summary.strip() or not draft.why_it_matters.strip():
        errors.append("empty required narrative field")
    return errors
