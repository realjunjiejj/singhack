"""Suitability: does the portfolio match the client's profile and objectives?

These rules compare what the client said they wanted with what they actually
hold. They are the least mechanical signals in the engine, so each one states
its own limits and none of them is presented as a compliance determination.
"""

from __future__ import annotations

from jb_clarity.domain.enums import CaseStatus, ScoringFactor, SignalType
from jb_clarity.domain.models import Measure
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder
from jb_clarity.phrasing import count_noun

CLIENTS_FILE = "clients.csv"
GROWTH_ASSET_CLASSES = ("Equity", "Structured Products")
# A recurring draw above this share of total wealth is treated as material
# pressure on a portfolio that is also shrinking.
DRAWDOWN_PRESSURE_PCT = 3.0
CURRENCY_ALIGNMENT_PCT = 50.0


def detect(context) -> list[DetectedSignal]:
    settings = context.factor(ScoringFactor.SUITABILITY_MISMATCH)
    builder = SignalBuilder(context.client_id, SignalType.SUITABILITY, status=CaseStatus.ACTIVE)
    contributions: list[tuple[float, str]] = []
    summaries: list[str] = []

    _profile_mismatch(context, builder, settings, contributions, summaries)
    _income_sustainability(context, builder, settings, contributions, summaries)
    _restricted_versus_liquidity_need(context, builder, settings, contributions, summaries)
    _currency_alignment(context, builder, settings, contributions, summaries)

    if not contributions:
        return []

    points = min(max(p for p, _ in contributions), float(settings["max"]))
    reason = max(contributions, key=lambda c: c[0])[1]
    builder.score(ScoringFactor.SUITABILITY_MISMATCH, points, reason)

    return [
        builder.finish(
            summary=" ".join(summaries),
            time_horizon="current",
            severity_rank=52,
        )
    ]


def _profile_mismatch(context, builder, settings, contributions, summaries) -> None:
    risk_score = float(context.client["risk_tolerance_score"])
    profile = str(context.client["risk_profile"])
    total = context.exposure.total_usd
    if total <= 0:
        return

    growth_usd = sum(
        value
        for asset_class, value in context.exposure.by_asset_class.items()
        if str(asset_class) in GROWTH_ASSET_CLASSES
    )
    growth_pct = 100.0 * growth_usd / total
    ceiling = float(settings["conservativeRiskToleranceCeiling"])
    threshold = float(settings["growthAssetShareThresholdPct"])

    if risk_score > ceiling or growth_pct < threshold:
        return

    profile_item = builder.item(
        "risk-profile",
        "Recorded risk profile",
        {
            "riskProfile": profile,
            "riskToleranceScore": risk_score,
            "investmentHorizonYears": int(context.client["investment_horizon_years"]),
        },
        file=CLIENTS_FILE,
        record_key=context.client_id,
        field_name="risk_profile|risk_tolerance_score",
    )
    allocation_item = builder.item(
        "growth-share",
        "Equity and structured-product share of client wealth",
        {
            "growthUsd": growth_usd,
            "totalUsd": total,
            "byAssetClassUsd": {str(k): float(v) for k, v in context.exposure.by_asset_class.items()},
        },
        file="holdings.csv",
        record_key=f"{context.client_id}|{context.snapshot}",
        field_name="asset_class|market_value_usd",
    )
    builder.metric(
        "growth-share",
        "Equity and structured-product share of client wealth",
        "(equity + structured products) market value / total client market value x 100",
        {"growthUsd": growth_usd, "totalUsd": total},
        Measure(value=round(growth_pct, 4), unit="percent"),
        context.snapshot,
    )
    builder.fact(
        "profile",
        f"The client is profiled {profile} with a risk tolerance score of "
        f"{risk_score:.0f} out of 10, while equity and structured products are "
        f"{growth_pct:.2f}% of their wealth.",
        [profile_item, allocation_item],
    )
    builder.interpretation(
        "profile",
        "A portfolio held this far above the risk the client is recorded as "
        "accepting is a suitability question for the RM to raise, not a conclusion "
        "the engine can settle.",
        [profile_item, allocation_item],
    )
    contributions.append(
        (
            float(settings["strongProfileMismatch"]),
            f"A {profile} profile (score {risk_score:.0f}) holds {growth_pct:.1f}% in "
            "equity and structured products.",
        )
    )
    summaries.append(
        f"A {profile} profile holds {growth_pct:.1f}% in equity and structured products."
    )


def _income_sustainability(context, builder, settings, contributions, summaries) -> None:
    """A recurring draw taken from a portfolio that is shrinking."""
    recurring = [
        occurrence
        for occurrence in context.occurrences
        if occurrence.is_confirmed and "annual" in occurrence.recurrence.lower()
    ]
    if not recurring or context.exposure.total_usd <= 0:
        return
    if context.timeline.change_pct >= 0:
        return

    largest = max(recurring, key=lambda o: o.amount)
    converted = context.fx.to_usd(largest.amount, largest.currency)
    if converted.amount != converted.amount:
        return
    draw_pct = 100.0 * converted.amount / context.exposure.total_usd
    if draw_pct < DRAWDOWN_PRESSURE_PCT:
        return

    need_item = builder.item(
        "recurring-draw",
        f"Recurring obligation {largest.need_id}",
        {
            "description": largest.description,
            "amount": largest.amount,
            "currency": largest.currency,
            "recurrence": largest.recurrence,
        },
        file="planned_cash_needs.csv",
        record_key=largest.need_id,
    )
    timeline_item = builder.item(
        "portfolio-trend",
        "Client wealth at the first and latest supplied snapshots",
        {
            context.timeline.first.snapshot_date: context.timeline.first.total_usd,
            context.timeline.last.snapshot_date: context.timeline.last.total_usd,
        },
        file="holdings.csv",
        record_key=f"{context.client_id}|{context.timeline.first.snapshot_date}|{context.snapshot}",
        field_name="market_value_usd",
    )
    objective_item = builder.item(
        "objectives",
        "Stated objectives",
        str(context.client["objectives"]),
        file=CLIENTS_FILE,
        record_key=context.client_id,
        field_name="objectives",
    )
    builder.metric(
        "draw-rate",
        "Recurring draw as a share of client wealth",
        "annual obligation converted to USD / total client market value x 100",
        {
            "obligationUsd": converted.amount,
            "totalUsd": context.exposure.total_usd,
            "sourceCurrency": largest.currency,
        },
        Measure(value=round(draw_pct, 4), unit="percent"),
        context.snapshot,
    )
    builder.fact(
        "draw-versus-trend",
        f"A confirmed recurring draw of {largest.currency} {largest.amount:,.0f} is "
        f"{draw_pct:.2f}% of this client's wealth, which fell "
        f"{abs(context.timeline.change_pct):.2f}% "
        f"(USD {abs(context.timeline.change_usd):,.0f}) between "
        f"{context.timeline.first.snapshot_date} and {context.timeline.last.snapshot_date}.",
        [need_item, timeline_item],
    )
    builder.interpretation(
        "draw-versus-objective",
        "The recorded objectives ask the portfolio to fund this draw while preserving "
        "capital. Over the supplied period the portfolio did both less well than the "
        "objective implies, which is a conversation about the plan rather than about "
        "any single holding.",
        [objective_item, need_item, timeline_item],
    )
    builder.uncertainty(
        "draw-horizon",
        f"The engine compares the draw with "
        f"{count_noun(len(context.timeline.points), 'supplied snapshot')} between "
        f"{context.timeline.first.snapshot_date} and "
        f"{context.timeline.last.snapshot_date}. It makes no projection of how long "
        "the portfolio can sustain the draw and no assumption about the client's "
        "circumstances.",
        [need_item, timeline_item],
    )
    contributions.append(
        (
            float(settings["moderateProfileMismatch"]),
            f"A confirmed recurring draw of {draw_pct:.2f}% of wealth sits against a "
            f"portfolio that fell {abs(context.timeline.change_pct):.2f}% over the "
            "supplied period.",
        )
    )
    summaries.append(
        f"A recurring draw of {draw_pct:.1f}% of wealth runs against a portfolio down "
        f"{abs(context.timeline.change_pct):.1f}%."
    )


def _restricted_versus_liquidity_need(context, builder, settings, contributions, summaries) -> None:
    need_level = str(context.client["liquidity_needs"])
    if need_level != "High" or context.exposure.total_usd <= 0:
        return

    restricted_usd = sum(
        value
        for tier, value in context.exposure.by_liquidity_tier.items()
        if str(tier) in ("Quarterly Gate", "Illiquid")
    )
    restricted_pct = 100.0 * restricted_usd / context.exposure.total_usd
    if restricted_pct < float(settings["restrictedAssetShareThresholdPct"]):
        return

    item = builder.item(
        "liquidity-need",
        "Recorded liquidity need and restricted holdings",
        {
            "liquidityNeeds": need_level,
            "restrictedUsd": restricted_usd,
            "restrictedPct": round(restricted_pct, 4),
        },
        file=CLIENTS_FILE,
        record_key=context.client_id,
        field_name="liquidity_needs",
    )
    builder.fact(
        "liquidity-need",
        f"The client's liquidity need is recorded as High, yet {restricted_pct:.2f}% "
        f"of their wealth (USD {restricted_usd:,.0f}) is gated or illiquid.",
        [item],
    )
    contributions.append(
        (
            float(settings["liquidityNeedVersusRestrictedAssets"]),
            f"A High liquidity need sits against {restricted_pct:.1f}% gated or "
            "illiquid holdings.",
        )
    )
    summaries.append(
        f"A High liquidity need sits against {restricted_pct:.1f}% gated or illiquid assets."
    )


def _currency_alignment(context, builder, settings, contributions, summaries) -> None:
    """Obligations in a currency the client's sellable assets are not held in."""
    holdings = context.holdings
    sellable = holdings[holdings.liquidity_tier == "Daily"]
    if sellable.empty:
        return
    total_sellable = float(sellable["market_value_usd"].sum())
    if total_sellable <= 0:
        return

    by_currency = sellable.groupby("instrument_ccy", dropna=False)["market_value_usd"].sum()

    for occurrence in context.occurrences:
        if not occurrence.is_actionable or occurrence.days_remaining < 0:
            continue
        if occurrence.days_remaining > context.config["liquidity"]["planningHorizonDays"]:
            continue
        matched = float(by_currency.get(occurrence.currency, 0.0))
        matched_pct = 100.0 * matched / total_sellable
        if matched_pct >= CURRENCY_ALIGNMENT_PCT:
            continue

        item = builder.item(
            f"currency-{occurrence.need_id}",
            f"Sellable assets by currency against {occurrence.need_id}",
            {
                "obligationCurrency": occurrence.currency,
                "obligationAmount": occurrence.amount,
                "sellableByCurrencyUsd": {str(k): float(v) for k, v in by_currency.items()},
            },
            file="holdings.csv",
            record_key=f"{context.client_id}|{context.snapshot}",
            field_name="instrument_ccy|market_value_usd",
        )
        builder.fact(
            f"currency-{occurrence.need_id}",
            f"{occurrence.description} is denominated in {occurrence.currency}, but only "
            f"{matched_pct:.1f}% of this client's daily-liquid assets are held in "
            f"{occurrence.currency}.",
            [item],
        )
        builder.interpretation(
            f"currency-risk-{occurrence.need_id}",
            "Funding the obligation would require a currency conversion at whatever "
            "rate applies on the day, so the cost in portfolio terms is not fixed.",
            [item],
        )
        contributions.append(
            (
                float(settings["liquidityNeedVersusRestrictedAssets"]),
                f"{occurrence.need_id} is a {occurrence.currency} obligation while "
                f"only {matched_pct:.1f}% of sellable assets are in that currency.",
            )
        )
        summaries.append(
            f"A {occurrence.currency} obligation sits against mostly non-"
            f"{occurrence.currency} sellable assets."
        )
        return
