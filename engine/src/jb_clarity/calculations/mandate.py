"""Mandate compliance: allocation bands, position limits, binding exclusions.

Custody accounts are not managed by the bank and are not measured against a
mandate, so they are excluded from compliance while still counting toward the
client's exposure. Single-position limits apply only where the dataset marks
`concentration_limit_applies`, which keeps diversified funds, sovereign bonds
and deposits out of a single-name test.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from jb_clarity.ingestion.loader import ChallengeData

CUSTODY = "Custody"


@dataclass(frozen=True)
class BandBreach:
    portfolio_id: str
    client_id: str
    mandate_code: str
    mandate_name: str
    service_model: str
    asset_class: str
    actual_pct: float
    min_pct: float
    target_pct: float
    max_pct: float
    direction: str

    @property
    def gap_pct_points(self) -> float:
        if self.direction == "above max":
            return self.actual_pct - self.max_pct
        return self.min_pct - self.actual_pct

    @property
    def summary(self) -> str:
        bound = self.max_pct if self.direction == "above max" else self.min_pct
        word = "above its maximum" if self.direction == "above max" else "below its minimum"
        return (
            f"{self.asset_class} is {self.actual_pct:.2f}% of {self.portfolio_id}, "
            f"{self.gap_pct_points:.2f} percentage points {word} of {bound:.0f}%."
        )


@dataclass(frozen=True)
class PositionBreach:
    portfolio_id: str
    client_id: str
    mandate_code: str
    instrument_id: str
    instrument_name: str
    weight_pct: float
    limit_pct: float
    market_value_base: float
    currency: str

    @property
    def gap_pct_points(self) -> float:
        return self.weight_pct - self.limit_pct

    @property
    def summary(self) -> str:
        return (
            f"{self.instrument_name} is {self.weight_pct:.2f}% of {self.portfolio_id}, "
            f"above the {self.limit_pct:.0f}% single-position limit."
        )


@dataclass(frozen=True)
class ExclusionBreach:
    """A holding that falls inside a mandate's binding exclusion list."""

    portfolio_id: str
    client_id: str
    mandate_code: str
    instrument_id: str
    instrument_name: str
    weight_pct: float
    market_value_base: float
    currency: str
    mandate_notes: str

    @property
    def summary(self) -> str:
        return (
            f"{self.instrument_name} is {self.weight_pct:.2f}% of {self.portfolio_id} "
            f"and is flagged as excluded under the {self.mandate_code} mandate."
        )


@dataclass
class MandateAssessment:
    band_breaches: list[BandBreach] = field(default_factory=list)
    position_breaches: list[PositionBreach] = field(default_factory=list)
    exclusion_breaches: list[ExclusionBreach] = field(default_factory=list)

    @property
    def any_breach(self) -> bool:
        return bool(self.band_breaches or self.position_breaches or self.exclusion_breaches)


def assess_client_mandates(
    data: ChallengeData, client_id: str, snapshot: str
) -> MandateAssessment:
    """Test every managed portfolio a client holds against its mandate."""
    assessment = MandateAssessment()
    instruments = data.instruments.set_index("instrument_id")
    portfolios = data.client_portfolios(client_id)

    for _, portfolio in portfolios.iterrows():
        if str(portfolio["service_model"]) == CUSTODY:
            continue

        portfolio_id = str(portfolio["portfolio_id"])
        mandate_code = str(portfolio["mandate_code"])
        holdings = data.holdings_at(snapshot).loc[
            data.holdings_at(snapshot).portfolio_id == portfolio_id
        ]
        total = float(holdings["market_value_base"].sum())
        if total <= 0:
            continue

        bands = data.mandate_bands(mandate_code)
        currency = str(portfolio["base_currency"])

        for _, band in bands.iterrows():
            asset_class = str(band["asset_class"])
            held = float(
                holdings.loc[holdings.asset_class == asset_class, "market_value_base"].sum()
            )
            actual_pct = 100.0 * held / total
            direction = ""
            if actual_pct > float(band["max_pct"]):
                direction = "above max"
            elif actual_pct < float(band["min_pct"]):
                direction = "below min"
            if direction:
                assessment.band_breaches.append(
                    BandBreach(
                        portfolio_id=portfolio_id,
                        client_id=client_id,
                        mandate_code=mandate_code,
                        mandate_name=str(portfolio["mandate_name"]),
                        service_model=str(portfolio["service_model"]),
                        asset_class=asset_class,
                        actual_pct=actual_pct,
                        min_pct=float(band["min_pct"]),
                        target_pct=float(band["target_pct"]),
                        max_pct=float(band["max_pct"]),
                        direction=direction,
                    )
                )

        limit_pct = float(bands["max_single_position_pct"].iloc[0])
        mandate_notes = str(bands["mandate_notes"].iloc[0])

        for _, holding in holdings.iterrows():
            instrument_id = str(holding["instrument_id"])
            if instrument_id not in instruments.index:
                continue
            instrument = instruments.loc[instrument_id]
            weight_pct = 100.0 * float(holding["market_value_base"]) / total

            if str(instrument.get("concentration_limit_applies")) == "Y" and weight_pct > limit_pct:
                assessment.position_breaches.append(
                    PositionBreach(
                        portfolio_id=portfolio_id,
                        client_id=client_id,
                        mandate_code=mandate_code,
                        instrument_id=instrument_id,
                        instrument_name=str(holding["instrument_name"]),
                        weight_pct=weight_pct,
                        limit_pct=limit_pct,
                        market_value_base=float(holding["market_value_base"]),
                        currency=currency,
                    )
                )

            if str(instrument.get("sustainability_excluded")) == "Y" and _has_binding_exclusions(
                mandate_notes
            ):
                assessment.exclusion_breaches.append(
                    ExclusionBreach(
                        portfolio_id=portfolio_id,
                        client_id=client_id,
                        mandate_code=mandate_code,
                        instrument_id=instrument_id,
                        instrument_name=str(holding["instrument_name"]),
                        weight_pct=weight_pct,
                        market_value_base=float(holding["market_value_base"]),
                        currency=currency,
                        mandate_notes=mandate_notes,
                    )
                )

    return assessment


def _has_binding_exclusions(mandate_notes: str) -> bool:
    """A mandate only carries exclusions when its notes say they are binding."""
    return "binding exclusion" in mandate_notes.lower()
