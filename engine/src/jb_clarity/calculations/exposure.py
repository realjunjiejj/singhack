"""Client-level exposure, structured-product look-through, and concentration.

Exposure is aggregated across every portfolio a client holds, because a risk
can be invisible inside each portfolio and obvious once combined. Custody
accounts count toward what the client is exposed to, even though they are not
measured against a mandate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd

from jb_clarity.ingestion.loader import ChallengeData

# Theme keywords matched against instrument name, sector, sub-asset class and
# any declared underlying reference. Themes exist to connect a client's stated
# source of wealth to what their portfolio actually holds.
THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "energy": ("energy", "oil", "gas", "coal", "brent", "petroleum", "lng"),
    "technology": ("technology", "cloud", "semiconductor", "software", "digital"),
    "real estate": ("propert", "real estate", "reit", "harbour properties", "mid-levels"),
    "gold and precious metals": ("gold", "xau", "precious metal", "bullion"),
    "shipping and marine": ("shipping", "marine", "tanker", "charter", "orient shipping"),
    "financials": ("bank", "financial"),
    "luxury and consumer": ("luxury", "consumer brands"),
}

_WORST_OF = re.compile(r"worst-of basket\s*:\s*(.+)", re.IGNORECASE)
_SINGLE = re.compile(r"single underlying\s*:\s*(.+)", re.IGNORECASE)
_UNDERLYING = re.compile(r"underlying\s*:\s*(.+)", re.IGNORECASE)
_NAME_REF = re.compile(r"\bref\.\s*([^,]+)", re.IGNORECASE)


@dataclass(frozen=True)
class LookThrough:
    """What a structured product is actually exposed to.

    The asset class says what the instrument is called; `underlying_reference`
    says what the client is exposed to. Component weights are not supplied, so
    no amount is ever split across components.
    """

    instrument_id: str
    instrument_name: str
    underlying_reference: str
    structure: str
    components: tuple[str, ...]
    notional_usd: float
    limitation: str


@dataclass(frozen=True)
class ThemeExposure:
    theme: str
    direct_usd: float
    look_through_usd: float
    direct_instruments: tuple[str, ...]
    look_through_instruments: tuple[str, ...]
    client_total_usd: float

    @property
    def combined_usd(self) -> float:
        return self.direct_usd + self.look_through_usd

    @property
    def direct_pct(self) -> float:
        return 100.0 * self.direct_usd / self.client_total_usd if self.client_total_usd else 0.0

    @property
    def combined_pct(self) -> float:
        return 100.0 * self.combined_usd / self.client_total_usd if self.client_total_usd else 0.0


@dataclass
class ClientExposure:
    client_id: str
    total_usd: float
    managed_usd: float
    custody_usd: float
    by_instrument: pd.DataFrame = field(default_factory=pd.DataFrame)
    by_asset_class: dict[str, float] = field(default_factory=dict)
    by_liquidity_tier: dict[str, float] = field(default_factory=dict)
    look_throughs: list[LookThrough] = field(default_factory=list)
    themes: dict[str, ThemeExposure] = field(default_factory=dict)

    def largest_positions(self, limit: int = 5) -> pd.DataFrame:
        return self.by_instrument.head(limit)


def parse_look_through(instrument: pd.Series) -> LookThrough | None:
    """Extract the named underlyings a structured product references."""
    reference = instrument.get("underlying_reference")
    if reference is None or (isinstance(reference, float) and pd.isna(reference)):
        return None
    reference = str(reference).strip()
    if not reference:
        return None

    name = str(instrument["instrument_name"])
    structure = "reference"
    components: list[str] = []

    if match := _WORST_OF.search(reference):
        structure = "worst-of basket"
        components = [part.strip() for part in match.group(1).split("/")]
    elif match := _SINGLE.search(reference):
        structure = "single underlying"
        components = [match.group(1).strip()]
    elif match := _UNDERLYING.search(reference):
        structure = "single underlying"
        components = [match.group(1).split(",")[0].strip()]
    elif match := _NAME_REF.search(name):
        structure = "single underlying"
        components = [match.group(1).strip()]
    else:
        components = [reference]

    components = tuple(c for c in (c.strip(" .") for c in components) if c)
    if structure == "worst-of basket":
        limitation = (
            "Component weights are not supplied. In a worst-of structure the full "
            "notional is exposed to whichever component performs worst, so the "
            "notional is shown against each named underlying rather than divided "
            "between them."
        )
    else:
        limitation = (
            "The underlying is read from free-text `underlying_reference`. It "
            "identifies what the position is exposed to, not a modelled "
            "sensitivity or delta."
        )

    return LookThrough(
        instrument_id=str(instrument["instrument_id"]),
        instrument_name=name,
        underlying_reference=reference,
        structure=structure,
        components=components,
        notional_usd=0.0,
        limitation=limitation,
    )


def _matches_theme(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def build_client_exposure(
    data: ChallengeData, client_id: str, snapshot: str
) -> ClientExposure:
    """Aggregate one client's exposure across all portfolios at a snapshot."""
    holdings = data.holdings_at(snapshot, client_id)
    total = float(holdings["market_value_usd"].sum())

    service_by_portfolio = data.portfolios.set_index("portfolio_id")["service_model"].to_dict()
    is_custody = holdings["portfolio_id"].map(
        lambda pid: service_by_portfolio.get(pid) == "Custody"
    )
    custody_usd = float(holdings.loc[is_custody, "market_value_usd"].sum())

    by_instrument = (
        holdings.groupby(
            ["instrument_id", "instrument_name", "asset_class", "liquidity_tier"],
            dropna=False,
        )["market_value_usd"]
        .sum()
        .reset_index()
        .sort_values("market_value_usd", ascending=False)
    )
    by_instrument["client_weight_pct"] = (
        100.0 * by_instrument["market_value_usd"] / total if total else 0.0
    )

    exposure = ClientExposure(
        client_id=client_id,
        total_usd=total,
        managed_usd=total - custody_usd,
        custody_usd=custody_usd,
        by_instrument=by_instrument,
        by_asset_class=(
            holdings.groupby("asset_class", dropna=False)["market_value_usd"].sum().to_dict()
        ),
        by_liquidity_tier=(
            holdings.groupby("liquidity_tier", dropna=False)["market_value_usd"].sum().to_dict()
        ),
    )

    instruments = data.instruments.set_index("instrument_id")
    for row in by_instrument.itertuples():
        if row.instrument_id not in instruments.index:
            continue
        instrument = instruments.loc[row.instrument_id]
        instrument = instrument.copy()
        instrument["instrument_id"] = row.instrument_id
        parsed = parse_look_through(instrument)
        if parsed is None:
            continue
        if str(instrument["asset_class"]) != "Structured Products":
            continue
        exposure.look_throughs.append(
            LookThrough(
                instrument_id=parsed.instrument_id,
                instrument_name=parsed.instrument_name,
                underlying_reference=parsed.underlying_reference,
                structure=parsed.structure,
                components=parsed.components,
                notional_usd=float(row.market_value_usd),
                limitation=parsed.limitation,
            )
        )

    exposure.themes = _build_themes(exposure, instruments)
    return exposure


def _build_themes(
    exposure: ClientExposure, instruments: pd.DataFrame
) -> dict[str, ThemeExposure]:
    themes: dict[str, ThemeExposure] = {}
    look_through_ids = {lt.instrument_id for lt in exposure.look_throughs}

    for theme, keywords in THEME_KEYWORDS.items():
        direct_usd = 0.0
        direct_names: list[str] = []
        for row in exposure.by_instrument.itertuples():
            if row.instrument_id in look_through_ids:
                continue
            if row.instrument_id not in instruments.index:
                continue
            instrument = instruments.loc[row.instrument_id]
            descriptor = " ".join(
                str(instrument.get(field_name, ""))
                for field_name in ("instrument_name", "sector", "sub_asset_class")
            )
            if _matches_theme(descriptor, keywords):
                direct_usd += float(row.market_value_usd)
                direct_names.append(str(row.instrument_name))

        look_through_usd = 0.0
        look_through_names: list[str] = []
        for look_through in exposure.look_throughs:
            haystack = " ".join(look_through.components) + " " + look_through.instrument_name
            if _matches_theme(haystack, keywords):
                look_through_usd += look_through.notional_usd
                look_through_names.append(look_through.instrument_name)

        if direct_usd or look_through_usd:
            themes[theme] = ThemeExposure(
                theme=theme,
                direct_usd=direct_usd,
                look_through_usd=look_through_usd,
                direct_instruments=tuple(direct_names),
                look_through_instruments=tuple(look_through_names),
                client_total_usd=exposure.total_usd,
            )
    return themes
