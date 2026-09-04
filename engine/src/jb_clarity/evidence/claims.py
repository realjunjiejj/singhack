"""Detected signals and the builder that keeps their evidence well-formed.

A detector never writes a bare sentence. It records a statement together with
the evidence item identifiers that support it, so every claim in the artifact
can be resolved back to a source file and record key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

from jb_clarity.domain.enums import CaseStatus, ScoringFactor, SignalType
from jb_clarity.domain.models import (
    Claim,
    DerivedMetric,
    EvidenceItem,
    Measure,
    SafetyOverride,
    SourceReference,
)
from jb_clarity.evidence import ids


@dataclass
class ConfidenceDeduction:
    """A named, configured reduction in Confidence."""

    reason: str
    points: float


@dataclass
class DetectedSignal:
    """One Anticipatory Signal with everything needed to defend it."""

    signal_id: str
    client_id: str
    signal_type: SignalType
    status: CaseStatus
    summary: str
    time_horizon: str
    factor: ScoringFactor | None = None
    points: float = 0.0
    points_reason: str = ""
    facts: list[Claim] = field(default_factory=list)
    interpretations: list[Claim] = field(default_factory=list)
    uncertainties: list[Claim] = field(default_factory=list)
    conflicts: list[Claim] = field(default_factory=list)
    assumptions: list[Claim] = field(default_factory=list)
    derived_metrics: list[DerivedMetric] = field(default_factory=list)
    items: list[EvidenceItem] = field(default_factory=list)
    safety_override: SafetyOverride | None = None
    confidence_deductions: list[ConfidenceDeduction] = field(default_factory=list)
    days_remaining: int | None = None
    severity_rank: int = 0

    @property
    def item_ids(self) -> list[str]:
        return [item.id for item in self.items]

    @property
    def all_claims(self) -> list[Claim]:
        return [
            *self.facts,
            *self.interpretations,
            *self.uncertainties,
            *self.conflicts,
            *self.assumptions,
        ]


class SignalBuilder:
    """Accumulates evidence for one signal and guarantees unique identifiers."""

    def __init__(
        self,
        client_id: str,
        signal_type: SignalType,
        *,
        status: CaseStatus = CaseStatus.NORMAL,
        discriminator: str = "",
    ) -> None:
        self.client_id = client_id
        self.signal_type = signal_type
        # Several signals of one family can exist for a client (two facilities,
        # three obligations). The discriminator keeps their evidence ids apart
        # so identifiers stay globally unique and stable.
        self._prefix = f"{discriminator}-" if discriminator else ""
        self._signal = DetectedSignal(
            signal_id=ids.signal_id(client_id, signal_type, discriminator),
            client_id=client_id,
            signal_type=signal_type,
            status=status,
            summary="",
            time_horizon="",
        )
        self._used_item_keys: set[str] = set()
        self._used_claim_keys: set[str] = set()

    # -- evidence -----------------------------------------------------------
    def item(
        self,
        key: str,
        label: str,
        value: Any,
        *,
        file: str,
        record_key: str,
        field_name: str | None = None,
    ) -> str:
        """Record one source-backed evidence item and return its identifier."""
        unique_key = self._unique(f"{self._prefix}{key}", self._used_item_keys)
        item_id = ids.evidence_item_id(self.client_id, self.signal_type, unique_key)
        self._signal.items.append(
            EvidenceItem(
                id=item_id,
                label=label,
                value=value,
                source_reference=SourceReference(
                    file=file, record_key=record_key, field=field_name
                ),
            )
        )
        return item_id

    def metric(
        self,
        key: str,
        name: str,
        formula: str,
        inputs: dict[str, Any],
        result: Measure,
        snapshot_date: date | str,
    ) -> str:
        metric = DerivedMetric(
            id=ids.metric_id(self.client_id, self.signal_type, f"{self._prefix}{key}"),
            name=name,
            formula=formula,
            inputs=inputs,
            result=result,
            snapshot_date=(
                snapshot_date
                if isinstance(snapshot_date, date)
                else date.fromisoformat(str(snapshot_date))
            ),
        )
        self._signal.derived_metrics.append(metric)
        return metric.id

    # -- claims -------------------------------------------------------------
    def _claim(self, prefix: str, key: str, statement: str, item_ids: list[str]) -> Claim:
        unique_key = self._unique(f"{prefix}-{self._prefix}{key}", self._used_claim_keys)
        return Claim(
            id=ids.claim_id(prefix, self.client_id, self.signal_type, unique_key),
            statement=statement,
            evidence_item_ids=list(dict.fromkeys(item_ids)),
        )

    def fact(self, key: str, statement: str, item_ids: list[str]) -> Claim:
        claim = self._claim("F", key, statement, item_ids)
        self._signal.facts.append(claim)
        return claim

    def interpretation(self, key: str, statement: str, item_ids: list[str]) -> Claim:
        claim = self._claim("I", key, statement, item_ids)
        self._signal.interpretations.append(claim)
        return claim

    def uncertainty(self, key: str, statement: str, item_ids: list[str]) -> Claim:
        claim = self._claim("U", key, statement, item_ids)
        self._signal.uncertainties.append(claim)
        return claim

    def conflict(self, key: str, statement: str, item_ids: list[str]) -> Claim:
        claim = self._claim("C", key, statement, item_ids)
        self._signal.conflicts.append(claim)
        return claim

    def assumption(self, key: str, statement: str, item_ids: list[str]) -> Claim:
        claim = self._claim("A", key, statement, item_ids)
        self._signal.assumptions.append(claim)
        return claim

    # -- scoring and status -------------------------------------------------
    def score(self, factor: ScoringFactor, points: float, reason: str) -> None:
        self._signal.factor = factor
        self._signal.points = points
        self._signal.points_reason = reason

    def override(self, rule_id: str, reason: str) -> None:
        self._signal.safety_override = SafetyOverride(rule_id=rule_id, reason=reason)

    def deduct_confidence(self, reason: str, points: float) -> None:
        self._signal.confidence_deductions.append(
            ConfidenceDeduction(reason=reason, points=points)
        )

    def finish(
        self,
        summary: str,
        time_horizon: str,
        *,
        status: CaseStatus | None = None,
        days_remaining: int | None = None,
        severity_rank: int = 0,
    ) -> DetectedSignal:
        self._signal.summary = summary
        self._signal.time_horizon = time_horizon
        if status is not None:
            self._signal.status = status
        self._signal.days_remaining = days_remaining
        self._signal.severity_rank = severity_rank
        return self._signal

    @staticmethod
    def _unique(key: str, used: set[str]) -> str:
        candidate = key
        suffix = 2
        while candidate in used:
            candidate = f"{key}-{suffix}"
            suffix += 1
        used.add(candidate)
        return candidate
