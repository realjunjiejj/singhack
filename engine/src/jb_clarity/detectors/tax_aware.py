"""Tax-aware review prompts grounded in domicile and supplied unrealised P/L.

This detector does not calculate tax, select lots, or recommend harvesting. It
identifies where opposite-sign positions or cross-border facts justify a
qualified specialist review.
"""

from __future__ import annotations

import math

from jb_clarity.domain.enums import CaseStatus, SignalType
from jb_clarity.domain.models import Measure
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder


def detect(context) -> list[DetectedSignal]:
    residence = str(context.client["country_of_residence"])
    domicile = str(context.client["tax_domicile"])
    portfolio_currency = {
        str(row.portfolio_id): str(row.base_currency)
        for row in context.data.client_portfolios(context.client_id).itertuples()
    }
    gains_usd = 0.0
    losses_usd = 0.0
    positions_with_gains = 0
    positions_with_losses = 0
    convertible = 0
    for row in context.holdings.itertuples():
        pnl = float(row.unrealised_pnl_base)
        currency = portfolio_currency.get(str(row.portfolio_id))
        if currency is None or not math.isfinite(pnl) or pnl == 0:
            continue
        converted = context.fx.to_usd(pnl, currency)
        if not math.isfinite(converted.amount):
            continue
        convertible += 1
        if converted.amount > 0:
            gains_usd += converted.amount
            positions_with_gains += 1
        else:
            losses_usd += converted.amount
            positions_with_losses += 1

    cross_border = residence.casefold() != domicile.casefold()
    has_offsets_to_review = positions_with_gains > 0 and positions_with_losses > 0
    if not cross_border and not has_offsets_to_review:
        return []

    builder = SignalBuilder(context.client_id, SignalType.TAX_AWARE, status=CaseStatus.NORMAL)
    profile_item = builder.item(
        "domicile",
        "Residence and tax domicile",
        {"countryOfResidence": residence, "taxDomicile": domicile},
        file="clients.csv",
        record_key=context.client_id,
        field_name="country_of_residence|tax_domicile",
    )
    pnl_item = builder.item(
        "unrealised-pnl",
        "Current unrealised gains and losses across the client's portfolios",
        {
            "snapshotDate": context.snapshot,
            "positionsConverted": convertible,
            "positionsWithGains": positions_with_gains,
            "positionsWithLosses": positions_with_losses,
            "gainsUsd": round(gains_usd, 2),
            "lossesUsd": round(losses_usd, 2),
        },
        file="holdings.csv",
        record_key=f"{context.client_id}|{context.snapshot}",
        field_name="unrealised_pnl_base",
    )
    builder.metric(
        "gains",
        "Unrealised gains converted to USD",
        "sum of positive unrealised P/L in portfolio base currency, converted to USD",
        {"positionsWithGains": positions_with_gains},
        Measure(value=round(gains_usd, 2), unit="currency", currency="USD"),
        context.snapshot,
    )
    builder.metric(
        "losses",
        "Unrealised losses converted to USD",
        "sum of negative unrealised P/L in portfolio base currency, converted to USD",
        {"positionsWithLosses": positions_with_losses},
        Measure(value=round(losses_usd, 2), unit="currency", currency="USD"),
        context.snapshot,
    )
    builder.fact(
        "review-inputs",
        f"The record shows tax domicile {domicile} and residence {residence}; current positions include USD {gains_usd:,.0f} of unrealised gains and USD {abs(losses_usd):,.0f} of unrealised losses after supplied FX conversion.",
        [profile_item, pnl_item],
    )
    builder.interpretation(
        "specialist-review",
        "These facts support a tax-aware specialist review of timing and available options; they do not establish tax treatment or a recommendation to realise any position.",
        [profile_item, pnl_item],
    )
    builder.uncertainty(
        "household-and-rules",
        "The upload contract contains no household identifier, tax-lot rules, relief eligibility, or jurisdiction-specific tax calculation. Household optimisation and tax advice therefore remain out of scope until those governed inputs are supplied.",
        [profile_item, pnl_item],
    )
    summary_parts = []
    if cross_border:
        summary_parts.append(f"Tax domicile ({domicile}) differs from residence ({residence})")
    if has_offsets_to_review:
        summary_parts.append(f"the supplied positions contain both unrealised gains and losses")
    return [builder.finish(summary="; ".join(summary_parts) + ". Specialist review is required before action.", time_horizon="current supplied snapshot", severity_rank=12)]
