"""Typed Workbench model.

These models are the engine's boundary output. They serialise to exactly the
shape declared by `contracts/workbench.schema.json` v1.0.0. Field names are
snake_case in Python and camelCase on the wire via the alias generator, so the
contract cannot drift silently from the code.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from jb_clarity.domain.enums import (
    CaseStatus,
    ConfidenceLevel,
    DataQualityStatus,
    GovernanceStatus,
    GuidedAction,
    IssueSeverity,
    OpenLoopState,
    UrgencyTier,
)


class Contract(BaseModel):
    """Base model: camelCase on the wire, snake_case in Python."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        ser_json_inf_nan="strings",
    )


class SourceReference(Contract):
    """Where a claim comes from. Enough to reproduce it by hand."""

    file: str
    record_key: str
    field: str | None = None


class EvidenceItem(Contract):
    id: str
    label: str
    value: Any
    source_reference: SourceReference


class Measure(Contract):
    value: float
    unit: str
    currency: str | None = None


class Money(Contract):
    amount: float
    currency: str


class DerivedMetric(Contract):
    id: str
    name: str
    formula: str
    inputs: dict[str, Any]
    result: Measure
    snapshot_date: date


class Claim(Contract):
    """A statement plus the evidence item identifiers that support it."""

    id: str
    statement: str
    evidence_item_ids: list[str] = Field(default_factory=list)


class FactorContribution(Contract):
    factor: str
    points: float
    reason: str
    evidence_item_ids: list[str] = Field(default_factory=list)


class SafetyOverride(Contract):
    rule_id: str
    reason: str


class Urgency(Contract):
    tier: UrgencyTier
    score: float
    safety_override: SafetyOverride | None = None


class Confidence(Contract):
    level: ConfidenceLevel
    score: float
    reasons: list[str] = Field(default_factory=list)


class AnticipatorySignal(Contract):
    id: str
    type: str
    status: CaseStatus
    summary: str
    time_horizon: str
    evidence_item_ids: list[str] = Field(default_factory=list)


class OpenLoop(Contract):
    id: str
    summary: str
    note_date: date
    source_excerpt: str
    why_open: str
    confidence: Confidence
    confirmation_required: bool = True
    state: OpenLoopState = OpenLoopState.CANDIDATE
    evidence_item_ids: list[str] = Field(default_factory=list)


class GovernanceClock(Contract):
    id: str
    type: str
    due_date: date
    days_remaining: int
    status: GovernanceStatus
    summary: str
    evidence_item_ids: list[str] = Field(default_factory=list)


class TimelinePoint(Contract):
    date: date
    label: str
    metrics: dict[str, Measure] = Field(default_factory=dict)
    evidence_item_ids: list[str] = Field(default_factory=list)


class MeetingBrief(Contract):
    what_changed: str
    why_it_matters: str
    uncertainties: list[str] = Field(default_factory=list)
    opening_question: str
    discussion_options: list[str] = Field(default_factory=list)
    specialist_suggestion: str | None = None
    open_loop_ids: list[str] = Field(default_factory=list)
    governance_clock_ids: list[str] = Field(default_factory=list)
    evidence_item_ids: list[str] = Field(default_factory=list)


class ClientReadyDraft(Contract):
    language: str
    canonical_language: str
    status: str = "draft"
    content: str
    evidence_item_ids: list[str] = Field(default_factory=list)


class StressScenario(Contract):
    id: str
    collateral_change_pct: float
    collateral_value: Money
    lending_value: Money
    drawn_amount: Money
    ltv_pct: float
    trigger_pct: float
    distance_to_trigger_pct_points: float
    status: CaseStatus


class CollateralStressTest(Contract):
    label: str
    forecast: bool = False
    scenarios: list[StressScenario] = Field(default_factory=list)


class ClientCase(Contract):
    case_id: str
    client_id: str
    client_name: str
    reporting_language: str
    conclusion: str
    why_now: str
    status: CaseStatus
    urgency: Urgency
    confidence: Confidence
    facts: list[Claim] = Field(default_factory=list)
    interpretations: list[Claim] = Field(default_factory=list)
    uncertainties: list[Claim] = Field(default_factory=list)
    factor_contributions: list[FactorContribution] = Field(default_factory=list)
    anticipatory_signals: list[AnticipatorySignal] = Field(default_factory=list)
    open_loops: list[OpenLoop] = Field(default_factory=list)
    governance_clocks: list[GovernanceClock] = Field(default_factory=list)
    timeline: list[TimelinePoint] = Field(default_factory=list)
    evidence_packet_ids: list[str] = Field(default_factory=list)
    allowed_guided_actions: list[GuidedAction] = Field(default_factory=list)
    meeting_brief: MeetingBrief
    client_ready_drafts: list[ClientReadyDraft] | None = None
    collateral_stress_test: CollateralStressTest | None = None


class EvidencePacket(Contract):
    packet_id: str
    case_id: str
    client_id: str
    as_of_date: date
    signal_type: str
    status: CaseStatus
    facts: list[Claim] = Field(default_factory=list)
    interpretations: list[Claim] = Field(default_factory=list)
    uncertainties: list[Claim] = Field(default_factory=list)
    conflicts: list[Claim] = Field(default_factory=list)
    assumptions: list[Claim] = Field(default_factory=list)
    urgency_inputs: list[FactorContribution] = Field(default_factory=list)
    confidence_inputs: list[str] = Field(default_factory=list)
    derived_metrics: list[DerivedMetric] = Field(default_factory=list)
    items: list[EvidenceItem] = Field(default_factory=list)
    allowed_guided_actions: list[GuidedAction] = Field(default_factory=list)


class PriorityQueueItem(Contract):
    rank: int
    case_id: str
    client_id: str
    client_name: str
    booking_centre: str
    reporting_language: str
    urgency: Urgency
    confidence: Confidence
    priority_rationale: str
    factor_contributions: list[FactorContribution] = Field(default_factory=list)
    status: CaseStatus
    signal_summaries: list[str] = Field(default_factory=list)
    open_loop_count: int = 0
    governance_clock_count: int = 0


class RmIdentity(Contract):
    id: str
    name: str


class BookSummary(Contract):
    critical: int
    high: int
    watch: int


class BookFilters(Contract):
    signal_types: list[str] = Field(default_factory=list)
    booking_centres: list[str] = Field(default_factory=list)
    urgency_tiers: list[UrgencyTier] = Field(default_factory=list)
    confidence_levels: list[ConfidenceLevel] = Field(default_factory=list)


class Book(Contract):
    rm: RmIdentity
    client_count: int
    portfolio_count: int
    summary: BookSummary
    filters: BookFilters
    priority_queue: list[PriorityQueueItem] = Field(default_factory=list)


class DataQualityIssue(Contract):
    id: str
    severity: IssueSeverity
    summary: str
    source_references: list[SourceReference] = Field(default_factory=list)


class DataQuality(Contract):
    status: DataQualityStatus
    issues: list[DataQualityIssue] = Field(default_factory=list)


class Meta(Contract):
    schema_version: str
    artifact_kind: str
    as_of_date: date
    generated_at: datetime
    source_snapshot_dates: list[date] = Field(default_factory=list)
    data_quality: DataQuality


class WorkbenchModel(Contract):
    """The complete Workbench artifact."""

    meta: Meta
    book: Book
    client_cases: list[ClientCase] = Field(default_factory=list)
    evidence_packets: list[EvidencePacket] = Field(default_factory=list)

    def to_contract_dict(self) -> dict[str, Any]:
        """Serialise to the wire shape validated by the JSON Schema."""
        return _prune_nulls(self.model_dump(mode="json", by_alias=True))


# Keys the schema requires even when their value is null. Everything else is
# omitted when absent, so optional fields never appear as explicit nulls.
_REQUIRED_NULLABLE_KEYS = frozenset({"safetyOverride", "specialistSuggestion"})


def _prune_nulls(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _prune_nulls(inner)
            for key, inner in value.items()
            if inner is not None or key in _REQUIRED_NULLABLE_KEYS
        }
    if isinstance(value, list):
        return [_prune_nulls(item) for item in value]
    return value
