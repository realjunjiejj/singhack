"""Concentration across every portfolio, including structured-product look-through.

A position can sit inside a mandate limit in each portfolio and still dominate
a client's wealth once the portfolios are combined. Where a structured product
declares an underlying, that exposure is counted as indicative and its limits
are stated rather than hidden.
"""

from __future__ import annotations

from jb_clarity.calculations.exposure import THEME_KEYWORDS, ThemeExposure
from jb_clarity.domain.enums import CaseStatus, ScoringFactor, SignalType
from jb_clarity.domain.models import Measure
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder

CLIENTS_FILE = "clients.csv"
INSTRUMENTS_FILE = "instruments.csv"


def detect(context) -> list[DetectedSignal]:
    thresholds = context.config["concentration"]
    exposure = context.exposure
    if exposure.total_usd <= 0:
        return []

    largest = exposure.by_instrument.iloc[0] if not exposure.by_instrument.empty else None
    themes = _material_themes(context, thresholds)
    source_theme = _source_of_wealth_theme(context, themes, thresholds)

    if (
        (largest is None or largest["client_weight_pct"] < thresholds["clientPositionSharePct"])
        and not themes
        and source_theme is None
    ):
        return []

    builder = SignalBuilder(context.client_id, SignalType.CONCENTRATION, status=CaseStatus.ACTIVE)
    contributions: list[tuple[float, str]] = []

    if largest is not None and largest["client_weight_pct"] >= thresholds["clientPositionSharePct"]:
        item = builder.item(
            "largest-position",
            f"{largest['instrument_name']} across all portfolios",
            {
                "marketValueUsd": float(largest["market_value_usd"]),
                "clientWeightPct": round(float(largest["client_weight_pct"]), 4),
            },
            file="holdings.csv",
            record_key=f"{context.client_id}|{largest['instrument_id']}|{context.snapshot}",
            field_name="market_value_usd",
        )
        builder.metric(
            "largest-position",
            "Largest single position as a share of client wealth",
            "position market value across all portfolios / total client market value x 100",
            {
                "instrumentId": str(largest["instrument_id"]),
                "positionUsd": float(largest["market_value_usd"]),
                "clientTotalUsd": exposure.total_usd,
            },
            Measure(value=round(float(largest["client_weight_pct"]), 4), unit="percent"),
            context.snapshot,
        )
        builder.fact(
            "largest-position",
            f"{largest['instrument_name']} is {largest['client_weight_pct']:.2f}% of this "
            f"client's total wealth once every portfolio is combined "
            f"(USD {largest['market_value_usd']:,.0f}).",
            [item],
        )
        if exposure.custody_usd > 0:
            builder.assumption(
                "custody-included",
                f"USD {exposure.custody_usd:,.0f} of this total sits in custody accounts. "
                "Custody is not measured against a mandate but the client is still "
                "exposed to it, so it is included here.",
                [item],
            )

    for theme in themes:
        theme_items = _theme_items(builder, context, theme)
        builder.metric(
            f"theme-{theme.theme}",
            f"Combined {theme.theme} exposure",
            "(direct exposure + declared structured-product notional) / total client wealth x 100",
            {
                "directUsd": theme.direct_usd,
                "lookThroughUsd": theme.look_through_usd,
                "clientTotalUsd": theme.client_total_usd,
            },
            Measure(value=round(theme.combined_pct, 4), unit="percent"),
            context.snapshot,
        )
        if theme.look_through_usd:
            builder.fact(
                f"theme-{theme.theme}",
                f"Direct {theme.theme} holdings are {theme.direct_pct:.2f}% of this "
                f"client's wealth. Adding the declared underlying of "
                f"{', '.join(theme.look_through_instruments)} takes the exposure to "
                f"{theme.combined_pct:.2f}% (USD {theme.combined_usd:,.0f}).",
                theme_items,
            )
            builder.uncertainty(
                f"theme-lookthrough-{theme.theme}",
                "Structured-product component weights are not supplied. The full "
                "notional is counted against the theme because a worst-of structure "
                "exposes the whole notional to its weakest component, so this is an "
                "indicative upper bound rather than a modelled sensitivity.",
                theme_items,
            )
            builder.deduct_confidence(
                "Look-through exposure is read from free-text underlying references "
                "without component weights.",
                context.config["confidence"]["deductions"]["indicativeLookThrough"],
            )
        else:
            builder.fact(
                f"theme-{theme.theme}",
                f"{theme.theme.title()} exposure is {theme.combined_pct:.2f}% of this "
                f"client's wealth (USD {theme.combined_usd:,.0f}).",
                theme_items,
            )

    if source_theme is not None:
        source_item = builder.item(
            "source-of-wealth",
            "Recorded source of wealth",
            str(context.client["source_of_wealth"]),
            file=CLIENTS_FILE,
            record_key=context.client_id,
            field_name="source_of_wealth",
        )
        builder.interpretation(
            "source-alignment",
            f"The client's recorded source of wealth is "
            f"'{context.client['source_of_wealth']}'. Their portfolio also carries "
            f"{source_theme.combined_pct:.2f}% in {source_theme.theme} exposure, so the "
            "wealth that funds the portfolio and a large part of the portfolio itself "
            "depend on the same conditions.",
            [source_item],
        )
        contributions.append(
            (
                float(
                    context.factor(ScoringFactor.SUITABILITY_MISMATCH)[
                        "sourceOfWealthConcentration"
                    ]
                ),
                f"Portfolio {source_theme.theme} exposure of "
                f"{source_theme.combined_pct:.2f}% repeats the client's recorded source "
                "of wealth.",
            )
        )

    if contributions:
        settings = context.factor(ScoringFactor.SUITABILITY_MISMATCH)
        points = min(max(points for points, _ in contributions), float(settings["max"]))
        reason = max(contributions, key=lambda c: c[0])[1]
        builder.score(ScoringFactor.SUITABILITY_MISMATCH, points, reason)

    summary_parts = []
    if largest is not None and largest["client_weight_pct"] >= thresholds["clientPositionSharePct"]:
        summary_parts.append(
            f"{largest['instrument_name']} is {largest['client_weight_pct']:.1f}% of total wealth"
        )
    for theme in themes:
        summary_parts.append(f"{theme.theme} exposure is {theme.combined_pct:.1f}%")

    return [
        builder.finish(
            summary="; ".join(summary_parts) + "." if summary_parts else "Concentration reviewed.",
            time_horizon="current",
            severity_rank=48,
        )
    ]


def _theme_items(builder: SignalBuilder, context, theme: ThemeExposure) -> list[str]:
    items = [
        builder.item(
            f"theme-direct-{theme.theme}",
            f"Direct {theme.theme} holdings",
            {
                "instruments": list(theme.direct_instruments),
                "marketValueUsd": theme.direct_usd,
            },
            file="holdings.csv",
            record_key=f"{context.client_id}|{context.snapshot}",
            field_name="market_value_usd",
        )
    ]
    for look_through in context.exposure.look_throughs:
        if look_through.instrument_name in theme.look_through_instruments:
            items.append(
                builder.item(
                    f"underlying-{look_through.instrument_id}",
                    f"{look_through.instrument_name} declared underlying",
                    {
                        "structure": look_through.structure,
                        "components": list(look_through.components),
                        "underlyingReference": look_through.underlying_reference,
                        "notionalUsd": look_through.notional_usd,
                    },
                    file=INSTRUMENTS_FILE,
                    record_key=look_through.instrument_id,
                    field_name="underlying_reference",
                )
            )
    return items


def _material_themes(context, thresholds: dict) -> list[ThemeExposure]:
    themes = [
        theme
        for theme in context.exposure.themes.values()
        if theme.combined_pct >= thresholds["themeSharePct"]
    ]
    return sorted(themes, key=lambda t: -t.combined_pct)


def _source_of_wealth_theme(context, themes, thresholds: dict) -> ThemeExposure | None:
    """The theme, if any, that repeats where the client's money came from."""
    source = str(context.client["source_of_wealth"]).lower()
    best: ThemeExposure | None = None
    for name, keywords in THEME_KEYWORDS.items():
        if not any(keyword in source for keyword in keywords):
            continue
        theme = context.exposure.themes.get(name)
        if theme is None:
            continue
        if theme.combined_pct < thresholds["sourceOfWealthSharePct"]:
            continue
        if best is None or theme.combined_pct > best.combined_pct:
            best = theme
    return best
