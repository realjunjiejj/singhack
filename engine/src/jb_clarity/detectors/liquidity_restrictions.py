"""Redemption gates and other restrictions on getting money out.

A gate is not the same as total illiquidity: the position still has value and
may still redeem, but it cannot be relied on to meet a dated obligation.
"""

from __future__ import annotations

from jb_clarity.calculations.liquidity import RESTRICTED_TIERS
from jb_clarity.domain.enums import CaseStatus, ScoringFactor, SignalType
from jb_clarity.domain.models import Measure
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder

MATERIAL_SHARE_PCT = 10.0
GATED_TIER = "Quarterly Gate"


def detect(context) -> list[DetectedSignal]:
    holdings = context.holdings
    restricted = holdings[holdings.liquidity_tier.isin(RESTRICTED_TIERS)]
    redemptions = context.data.transactions[
        (context.data.transactions.client_id == context.client_id)
        & (context.data.transactions.transaction_type == "Redemption Request")
    ]
    if restricted.empty and redemptions.empty:
        return []

    restricted_usd = float(restricted["market_value_usd"].sum())
    share_pct = 100.0 * restricted_usd / context.total_usd if context.total_usd else 0.0
    gated = restricted[restricted.liquidity_tier == GATED_TIER]

    if share_pct < MATERIAL_SHARE_PCT and gated.empty and redemptions.empty:
        return []

    status = CaseStatus.ACTIVE if (not gated.empty or not redemptions.empty) else CaseStatus.NORMAL
    builder = SignalBuilder(context.client_id, SignalType.LIQUIDITY_RESTRICTION, status=status)

    item_ids = []
    for _, row in restricted.iterrows():
        item_ids.append(
            builder.item(
                str(row["instrument_id"]),
                f"{row['instrument_name']} ({row['liquidity_tier']})",
                {
                    "marketValueUsd": float(row["market_value_usd"]),
                    "liquidityTier": str(row["liquidity_tier"]),
                    "advanceRatePct": float(row["advance_rate_pct"]),
                },
                file="holdings.csv",
                record_key=f"{row['portfolio_id']}|{row['instrument_id']}|{context.snapshot}",
                field_name="liquidity_tier",
            )
        )

    builder.metric(
        "restricted-share",
        "Share of client wealth in gated or illiquid holdings",
        "restricted market value / total client market value x 100",
        {
            "restrictedUsd": restricted_usd,
            "totalUsd": context.total_usd,
        },
        Measure(value=round(share_pct, 2), unit="percent"),
        context.snapshot,
    )

    builder.fact(
        "restricted",
        f"USD {restricted_usd:,.0f}, or {share_pct:.1f}% of this client's wealth, sits "
        f"in holdings marked {' or '.join(RESTRICTED_TIERS)}.",
        item_ids,
    )

    if not gated.empty:
        gated_usd = float(gated["market_value_usd"].sum())
        names = ", ".join(sorted(set(gated["instrument_name"].astype(str))))
        builder.interpretation(
            "gate",
            f"{names} carries a quarterly redemption gate covering USD {gated_usd:,.0f}. "
            "The manager may restrict withdrawals at a redemption date, so this holding "
            "cannot be relied on to meet a dated obligation. It is not worthless and "
            "may still redeem in part.",
            item_ids,
        )

    for _, row in redemptions.iterrows():
        redemption_item = builder.item(
            str(row["transaction_id"]),
            "Redemption request",
            {
                "tradeDate": str(row["trade_date"]),
                "instrument": str(row["instrument_name"]),
                "narrative": str(row["narrative"]),
            },
            file="transactions.csv",
            record_key=str(row["transaction_id"]),
        )
        builder.fact(
            f"redemption-{row['transaction_id']}",
            f"A redemption request was submitted on {row['trade_date']} for "
            f"{row['instrument_name']}.",
            [redemption_item],
        )
        builder.uncertainty(
            f"redemption-outcome-{row['transaction_id']}",
            "The dataset records the request but not its settlement, so the amount "
            "and date actually received are unknown.",
            [redemption_item],
        )
        builder.deduct_confidence(
            "A redemption request is recorded with no settled amount or date, so how "
            "much will actually be received is unknown.",
            context.config["confidence"]["deductions"]["missingCalculationInput"],
        )

    if not gated.empty or not redemptions.empty:
        builder.score(
            ScoringFactor.SUITABILITY_MISMATCH,
            0.0,
            "Redemption restrictions are reported as context; they score through the "
            "obligations they affect.",
        )

    return [
        builder.finish(
            summary=(
                "Gated or illiquid holdings are "
                f"{share_pct:.1f}% of this client's wealth"
                + (", and a redemption request is outstanding" if not redemptions.empty else "")
                + "."
            ),
            time_horizon="current",
            severity_rank=45 if not gated.empty else 20,
        )
    ]
