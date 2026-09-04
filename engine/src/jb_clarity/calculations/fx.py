"""Currency conversion using the dataset's own quoted conventions.

`market_context.csv` quotes each pair the way the market does: `USDSGD` is SGD
per USD, `EURUSD` is USD per EUR. Getting the direction wrong is a silent
error, so the direction is declared here once and every conversion records the
pair and rate it used.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# series_id -> (base, quote). The quoted value is `quote` units per one `base`.
PAIR_CONVENTIONS: dict[str, tuple[str, str]] = {
    "USDSGD": ("USD", "SGD"),
    "USDHKD": ("USD", "HKD"),
    "USDCHF": ("USD", "CHF"),
    "USDJPY": ("USD", "JPY"),
    "USDCNH": ("USD", "CNH"),
    "USDIDR": ("USD", "IDR"),
    "USDTHB": ("USD", "THB"),
    "USDINR": ("USD", "INR"),
    "EURUSD": ("EUR", "USD"),
    "GBPUSD": ("GBP", "USD"),
}


@dataclass(frozen=True)
class Conversion:
    """One converted amount with the assumption that produced it."""

    amount: float
    currency: str
    assumption: str
    pairs_used: tuple[str, ...] = ()
    direct_pair_available: bool = True


@dataclass
class FxTable:
    """Rates at one snapshot date, with USD used as the pivot currency."""

    snapshot_date: str
    rates: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_market(cls, market, snapshot_date: str) -> "FxTable":
        rows = market.loc[market.snapshot_date == snapshot_date]
        rates = {
            str(r.series_id): float(r.value)
            for r in rows.itertuples()
            if str(r.series_id) in PAIR_CONVENTIONS
        }
        return cls(snapshot_date=snapshot_date, rates=rates)

    def _usd_per_unit(self, currency: str) -> tuple[float | None, str | None]:
        """How many USD one unit of `currency` buys, and the pair used."""
        if currency == "USD":
            return 1.0, None
        for series_id, (base, quote) in PAIR_CONVENTIONS.items():
            rate = self.rates.get(series_id)
            if rate is None:
                continue
            if base == currency and quote == "USD":
                return rate, series_id  # e.g. EURUSD: USD per EUR
            if base == "USD" and quote == currency:
                return 1.0 / rate, series_id  # e.g. USDSGD: SGD per USD
        return None, None

    def convert(self, amount: float, from_ccy: str, to_ccy: str) -> Conversion:
        """Convert `amount` between currencies, pivoting through USD."""
        if from_ccy == to_ccy:
            return Conversion(
                amount=amount,
                currency=to_ccy,
                assumption=f"No conversion required; amount already in {to_ccy}.",
            )

        from_usd, from_pair = self._usd_per_unit(from_ccy)
        to_usd, to_pair = self._usd_per_unit(to_ccy)
        if from_usd is None or to_usd is None:
            missing = from_ccy if from_usd is None else to_ccy
            return Conversion(
                amount=float("nan"),
                currency=to_ccy,
                assumption=(
                    f"No {missing} rate in market_context.csv at {self.snapshot_date}; "
                    "conversion unavailable."
                ),
                direct_pair_available=False,
            )

        converted = amount * from_usd / to_usd
        pairs = tuple(p for p in (from_pair, to_pair) if p)
        direct = len(pairs) <= 1
        assumption = (
            f"Converted {from_ccy} to {to_ccy} at the {self.snapshot_date} "
            f"market_context.csv rate ({', '.join(pairs) if pairs else 'USD pivot'}), "
            "applied in the pair's quoted direction."
        )
        if not direct:
            assumption += " No direct pair is supplied, so USD is used as the pivot."
        return Conversion(
            amount=converted,
            currency=to_ccy,
            assumption=assumption,
            pairs_used=pairs,
            direct_pair_available=direct,
        )

    def to_usd(self, amount: float, from_ccy: str) -> Conversion:
        return self.convert(amount, from_ccy, "USD")
