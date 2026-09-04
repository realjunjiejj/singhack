"""Eligible Liquidity: what can realistically fund an obligation, on time.

Portfolio value is not available funding. A holding only counts toward an
obligation if its liquidity tier can settle inside the time remaining, and the
rules below are deliberately conservative prototype policy rather than a bank
standard.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from jb_clarity.calculations.fx import FxTable
from jb_clarity.ingestion.normalization import CashNeedOccurrence

# Minimum days of notice before a tier is treated as available for a dated
# obligation. Daily is always available; gated and illiquid assets never count
# toward guaranteed coverage.
TIER_MINIMUM_DAYS: dict[str, int] = {
    "Daily": 0,
    "Weekly": 14,
    "Monthly": 45,
}
RESTRICTED_TIERS = ("Quarterly Gate", "Illiquid")

POLICY_NOTE = (
    "Eligible Liquidity counts Daily holdings always, Weekly holdings with at "
    "least 14 days of notice, and Monthly holdings with at least 45 days. "
    "Quarterly Gate and Illiquid holdings are excluded from guaranteed coverage "
    "and reported separately. These are conservative prototype rules, not a "
    "bank liquidity standard."
)


@dataclass
class EligibleLiquidity:
    """Coverage of one obligation by assets that can settle in time."""

    need_id: str
    client_id: str
    currency: str
    amount: float
    days_remaining: int
    eligible_amount: float
    eligible_by_tier: dict[str, float] = field(default_factory=dict)
    restricted_by_tier: dict[str, float] = field(default_factory=dict)
    excluded_by_timing: dict[str, float] = field(default_factory=dict)
    fx_assumptions: list[str] = field(default_factory=list)
    fx_incomplete: bool = False
    competing_need_ids: tuple[str, ...] = ()

    @property
    def coverage_pct(self) -> float:
        return 100.0 * self.eligible_amount / self.amount if self.amount else 100.0

    @property
    def is_fully_covered(self) -> bool:
        return self.eligible_amount >= self.amount

    @property
    def shortfall(self) -> float:
        return max(0.0, self.amount - self.eligible_amount)

    @property
    def restricted_total(self) -> float:
        return sum(self.restricted_by_tier.values())

    @property
    def has_shared_pool(self) -> bool:
        return bool(self.competing_need_ids)


def assess_eligible_liquidity(
    holdings: pd.DataFrame,
    occurrence: CashNeedOccurrence,
    fx: FxTable,
    competing: tuple[str, ...] = (),
) -> EligibleLiquidity:
    """Assess whether one obligation can be funded from sellable assets.

    `holdings` are the client's positions at the as-of snapshot across every
    portfolio, including custody, because the client can sell what they own.
    """
    result = EligibleLiquidity(
        need_id=occurrence.need_id,
        client_id=occurrence.client_id,
        currency=occurrence.currency,
        amount=occurrence.amount,
        days_remaining=occurrence.days_remaining,
        eligible_amount=0.0,
        competing_need_ids=competing,
    )

    days = max(occurrence.days_remaining, 0)
    assumptions: set[str] = set()
    eligible_usd = 0.0

    by_tier = holdings.groupby("liquidity_tier", dropna=False)["market_value_usd"].sum()
    for tier, value_usd in by_tier.items():
        tier_name = str(tier)
        value_usd = float(value_usd)
        if tier_name in RESTRICTED_TIERS:
            result.restricted_by_tier[tier_name] = value_usd
            continue
        minimum_days = TIER_MINIMUM_DAYS.get(tier_name)
        if minimum_days is None:
            # An unrecognised tier is never assumed to be available.
            result.restricted_by_tier[tier_name] = value_usd
            continue
        if days < minimum_days:
            result.excluded_by_timing[tier_name] = value_usd
            continue
        result.eligible_by_tier[tier_name] = value_usd
        eligible_usd += value_usd

    conversion = fx.convert(eligible_usd, "USD", occurrence.currency)
    if conversion.amount != conversion.amount:
        result.fx_incomplete = True
        result.eligible_amount = 0.0
        assumptions.add(conversion.assumption)
    else:
        result.eligible_amount = conversion.amount
        if occurrence.currency != "USD":
            assumptions.add(conversion.assumption)
            if not conversion.direct_pair_available:
                result.fx_incomplete = True

    assumptions.add(POLICY_NOTE)
    result.fx_assumptions = sorted(assumptions)
    return result


def assess_client_liquidity(
    holdings: pd.DataFrame,
    occurrences: list[CashNeedOccurrence],
    fx: FxTable,
    horizon_days: int = 365,
) -> list[EligibleLiquidity]:
    """Assess every actionable obligation, exposing pool overlap.

    Each obligation is measured against the whole eligible pool, so two
    obligations inside the same window can both appear covered by the same
    assets. That overlap is named rather than silently netted.
    """
    actionable = [
        o for o in occurrences if o.is_actionable and 0 <= o.days_remaining <= horizon_days
    ]
    ids_by_need = {o.need_id: o for o in actionable}

    results: list[EligibleLiquidity] = []
    for occurrence in actionable:
        competing = tuple(
            sorted(
                need_id
                for need_id, other in ids_by_need.items()
                if need_id != occurrence.need_id
                and abs(other.days_remaining - occurrence.days_remaining) <= 90
            )
        )
        results.append(
            assess_eligible_liquidity(holdings, occurrence, fx, competing=competing)
        )
    return results
