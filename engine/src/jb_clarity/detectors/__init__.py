"""Signal detectors.

Detectors are general rules over the dataset. None of them names a client, so
the demonstration cases surface for the same reason every other case does.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pandas as pd

from jb_clarity.calculations.exposure import ClientExposure, build_client_exposure
from jb_clarity.calculations.fx import FxTable
from jb_clarity.calculations.liquidity import EligibleLiquidity, assess_client_liquidity
from jb_clarity.calculations.ltv import FacilityState, build_facility_state
from jb_clarity.calculations.mandate import MandateAssessment, assess_client_mandates
from jb_clarity.calculations.timeline import (
    ClientTimeline,
    EventLink,
    build_client_timeline,
    link_events,
)
from jb_clarity.evidence.claims import DetectedSignal
from jb_clarity.ingestion.loader import ChallengeData, RmNote
from jb_clarity.ingestion.normalization import CashNeedOccurrence, occurrences
from jb_clarity.ingestion.validation import TotalsReconciliation, ValidationReport


@dataclass
class ClientContext:
    """Everything one client's detectors need, computed once."""

    data: ChallengeData
    client_id: str
    client: pd.Series
    as_of: date
    snapshot: str
    fx: FxTable
    config: dict[str, Any]
    exposure: ClientExposure
    mandates: MandateAssessment
    facilities: list[FacilityState]
    occurrences: list[CashNeedOccurrence]
    liquidity: list[EligibleLiquidity]
    timeline: ClientTimeline
    event_links: list[EventLink]
    notes: list[RmNote]
    reconciliation: TotalsReconciliation
    stale_valuations: list[dict] = field(default_factory=list)

    @property
    def client_name(self) -> str:
        return str(self.client["client_name"])

    @property
    def booking_centre(self) -> str:
        return str(self.client["booking_centre"])

    @property
    def reporting_language(self) -> str:
        return str(self.client["reporting_language"])

    @property
    def total_usd(self) -> float:
        return self.exposure.total_usd

    @property
    def holdings(self) -> pd.DataFrame:
        return self.data.holdings_at(self.snapshot, self.client_id)

    def factor(self, name: str) -> dict[str, Any]:
        return self.config["urgency"]["factors"][name]


def build_client_context(
    data: ChallengeData,
    client_id: str,
    as_of: date,
    fx: FxTable,
    config: dict[str, Any],
    report: ValidationReport,
) -> ClientContext:
    snapshot = data.latest_snapshot
    client_occurrences = occurrences(data.client_cash_needs(client_id), as_of)
    exposure = build_client_exposure(data, client_id, snapshot)
    facilities = [
        build_facility_state(row, data.snapshot_dates)
        for _, row in data.client_facilities(client_id).iterrows()
    ]
    facilities.sort(key=lambda f: f.facility_id)

    return ClientContext(
        data=data,
        client_id=client_id,
        client=data.client(client_id),
        as_of=as_of,
        snapshot=snapshot,
        fx=fx,
        config=config,
        exposure=exposure,
        mandates=assess_client_mandates(data, client_id, snapshot),
        facilities=facilities,
        occurrences=client_occurrences,
        liquidity=assess_client_liquidity(
            data.holdings_at(snapshot, client_id),
            client_occurrences,
            fx,
            horizon_days=config["liquidity"]["planningHorizonDays"],
        ),
        timeline=build_client_timeline(data, client_id),
        event_links=link_events(data, client_id, snapshot),
        notes=data.client_notes(client_id),
        reconciliation=report.reconciliations[client_id],
        stale_valuations=[
            s for s in report.stale_valuations if s["client_id"] == client_id
        ],
    )


def detect_all(context: ClientContext) -> list[DetectedSignal]:
    """Run every detector for one client, in a stable order."""
    from jb_clarity.detectors import (
        cash_needs,
        concentration,
        credit,
        evidence_conflicts,
        liquidity_restrictions,
        mandate,
        suitability,
    )

    signals: list[DetectedSignal] = []
    signals.extend(credit.detect(context))
    signals.extend(cash_needs.detect(context))
    signals.extend(liquidity_restrictions.detect(context))
    signals.extend(mandate.detect(context))
    signals.extend(concentration.detect(context))
    signals.extend(suitability.detect(context))
    signals.extend(evidence_conflicts.detect(context))
    return sorted(signals, key=lambda s: (-s.severity_rank, s.signal_id))
