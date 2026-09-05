"""Typed contract emitted by the intelligence-team entry point."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from jb_clarity.domain.models import (
    Confidence,
    Contract,
    DerivedMetric,
    FactorContribution,
    Urgency,
    WorkbenchModel,
)


class DatasetFileProfile(Contract):
    name: str
    media_type: str
    size_bytes: int
    sha256: str
    row_count: int | None = None
    columns: list[str] = Field(default_factory=list)


class DatasetProfile(Contract):
    source: str
    files: list[DatasetFileProfile] = Field(default_factory=list)


class AnalysisDiagnostic(Contract):
    code: str
    severity: Literal["info", "warning", "material", "blocked"]
    message: str


class AgentFinding(Contract):
    finding_id: str
    direction: str
    client_id: str
    case_id: str
    title: str
    summary: str
    why_it_matters: str
    limitations: list[str] = Field(default_factory=list)
    evidence_packet_ids: list[str] = Field(default_factory=list)
    evidence_item_ids: list[str] = Field(default_factory=list)
    derived_metrics: list[DerivedMetric] = Field(default_factory=list)
    factor_contributions: list[FactorContribution] = Field(default_factory=list)
    rank: int | None = None
    urgency: Urgency | None = None
    confidence: Confidence | None = None
    narrative_source: Literal["deterministic", "model-validated"] = "deterministic"
    narrative_evidence_item_ids: list[str] = Field(default_factory=list)


class AgentReport(Contract):
    agent_id: str
    role: str
    depth: Literal["deep", "supporting", "control"]
    status: Literal["completed", "partial", "skipped", "blocked"]
    summary: str
    findings: list[AgentFinding] = Field(default_factory=list)
    diagnostics: list[AnalysisDiagnostic] = Field(default_factory=list)


class IntelligenceRun(Contract):
    schema_version: str = "1.0.0"
    run_id: str
    generated_at: datetime
    status: Literal["completed", "partial", "needs-mapping", "blocked"]
    adapter_id: str | None = None
    deep_focus: list[str] = Field(default_factory=list)
    dataset_profile: DatasetProfile
    diagnostics: list[AnalysisDiagnostic] = Field(default_factory=list)
    agent_reports: list[AgentReport] = Field(default_factory=list)
    workbench: WorkbenchModel | None = None

    def to_contract_dict(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json", by_alias=True, exclude_none=True)
        if self.workbench is not None:
            payload["workbench"] = self.workbench.to_contract_dict()
        return payload
