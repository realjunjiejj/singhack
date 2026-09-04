"""What the portfolio did across the five snapshots, and what explains it.

This is the evidence behind the timeline. It also carries the only claims in
the engine that mention a 2026 world event, and each of those cites a row of
`event_log.csv` — the Controlled Event Source — rather than anything the model
happens to remember. An event is connected to a client only where one of its
declared transmission channels maps to something they actually hold.
"""

from __future__ import annotations

from jb_clarity.calculations.timeline import EventLink
from jb_clarity.domain.enums import CaseStatus, SignalType
from jb_clarity.domain.models import Measure
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder

HOLDINGS_FILE = "holdings.csv"
EVENTS_FILE = "event_log.csv"
CLIENTS_FILE = "clients.csv"

PROFILE_ITEM_LABEL = "Client profile and stated objectives"

# An event is only worth explaining when it reaches a material share of the
# client's wealth. Below this it is noise on a client's report.
MATERIAL_EVENT_SHARE_PCT = 5.0
MAX_EVENTS_EXPLAINED = 4


def snapshot_item_label(snapshot: str) -> str:
    """The label the timeline uses to find its own evidence."""
    return f"Client wealth at {snapshot}"


def detect(context) -> list[DetectedSignal]:
    timeline = context.timeline
    if not timeline.points:
        return []

    builder = SignalBuilder(
        context.client_id, SignalType.EXPLANATION, status=CaseStatus.NORMAL
    )

    # Every Client Case quotes the client's own objectives and profile, so
    # every case needs an evidence item behind that quotation.
    builder.item(
        "profile",
        PROFILE_ITEM_LABEL,
        {
            "objectives": str(context.client["objectives"]),
            "riskProfile": str(context.client["risk_profile"]),
            "riskToleranceScore": float(context.client["risk_tolerance_score"]),
            "liquidityNeeds": str(context.client["liquidity_needs"]),
            "lifeStage": str(context.client["life_stage"]),
            "sourceOfWealth": str(context.client["source_of_wealth"]),
            "investmentHorizonYears": int(context.client["investment_horizon_years"]),
        },
        file=CLIENTS_FILE,
        record_key=context.client_id,
        field_name="objectives|risk_profile|liquidity_needs",
    )

    snapshot_items: list[str] = []
    for point in timeline.points:
        snapshot_items.append(
            builder.item(
                f"total-{point.snapshot_date}",
                snapshot_item_label(point.snapshot_date),
                {
                    "amount": point.total_usd,
                    "currency": "USD",
                    "byAssetClassUsd": point.by_asset_class_usd,
                },
                file=HOLDINGS_FILE,
                record_key=f"{context.client_id}|{point.snapshot_date}",
                field_name="market_value_usd",
            )
        )

    builder.metric(
        "period-change",
        "Change in client wealth across the supplied period",
        "(latest total - baseline total) / baseline total x 100",
        {
            "baselineDate": timeline.first.snapshot_date,
            "baselineUsd": timeline.first.total_usd,
            "latestDate": timeline.last.snapshot_date,
            "latestUsd": timeline.last.total_usd,
        },
        Measure(value=round(timeline.change_pct, 4), unit="percent"),
        timeline.last.snapshot_date,
    )
    # The summary quotes the change in money as well as in percent, so that
    # figure gets its own inspectable formula rather than leaving the RM to
    # subtract two totals in their head.
    builder.metric(
        "period-change-amount",
        "Change in client wealth across the supplied period, in USD",
        "latest total - baseline total",
        {
            "baselineDate": timeline.first.snapshot_date,
            "baselineUsd": timeline.first.total_usd,
            "latestDate": timeline.last.snapshot_date,
            "latestUsd": timeline.last.total_usd,
        },
        Measure(
            value=round(timeline.change_usd, 2), unit="currency", currency="USD"
        ),
        timeline.last.snapshot_date,
    )

    direction = "rose" if timeline.change_usd >= 0 else "fell"
    builder.fact(
        "period-change",
        f"Between {timeline.first.snapshot_date} and {timeline.last.snapshot_date} this "
        f"client's wealth {direction} from USD {timeline.first.total_usd:,.0f} to "
        f"USD {timeline.last.total_usd:,.0f}, a change of {timeline.change_pct:+.2f}%.",
        snapshot_items,
    )

    _explain_asset_classes(context, builder, snapshot_items)
    links = _explain_events(context, builder, snapshot_items)

    summary = (
        f"Wealth {direction} {abs(timeline.change_pct):.2f}% across the five supplied "
        f"snapshots (USD {abs(timeline.change_usd):,.0f})."
    )
    if links:
        summary += f" {len(links)} recorded event(s) reach holdings this client owns."

    return [
        builder.finish(
            summary=summary,
            time_horizon=(
                f"{timeline.first.snapshot_date} to {timeline.last.snapshot_date}"
            ),
            severity_rank=15,
        )
    ]


def _explain_asset_classes(context, builder: SignalBuilder, snapshot_items) -> None:
    """Name the asset classes that actually moved the number."""
    timeline = context.timeline
    moves = sorted(
        (
            (asset_class, timeline.asset_class_change_usd(asset_class))
            for asset_class in timeline.last.by_asset_class_usd
        ),
        key=lambda item: -abs(item[1]),
    )
    material = [(name, change) for name, change in moves if abs(change) > 0][:3]
    if not material:
        return

    described = "; ".join(
        f"{name} {'up' if change >= 0 else 'down'} USD {abs(change):,.0f}"
        for name, change in material
    )
    builder.fact(
        "asset-class-change",
        f"By asset class over the same period: {described}.",
        snapshot_items,
    )


def _explain_events(context, builder: SignalBuilder, snapshot_items) -> list[EventLink]:
    """Link Controlled Event Source records to holdings the client owns."""
    total = context.exposure.total_usd
    if total <= 0:
        return []

    material = [
        link
        for link in context.event_links
        if 100.0 * link.matched_value_usd / total >= MATERIAL_EVENT_SHARE_PCT
    ]
    material.sort(key=lambda link: (-link.matched_value_usd, link.event_date))
    material = material[:MAX_EVENTS_EXPLAINED]

    for link in material:
        event_item = builder.item(
            f"event-{link.event_date}-{link.event_index}",
            f"Recorded event, {link.event_date}",
            {
                "eventDate": link.event_date,
                "eventType": link.event_type,
                "region": link.region,
                "description": link.description,
                "primaryTransmission": link.primary_transmission,
                "severity": link.severity,
            },
            file=EVENTS_FILE,
            record_key=f"row {link.event_index}|{link.event_date}",
            field_name="description|primary_transmission",
        )
        holdings_item = builder.item(
            f"event-holdings-{link.event_date}-{link.event_index}",
            f"Holdings reached by the {link.event_date} event",
            {
                "byChannel": [
                    {
                        "channel": channel,
                        "instruments": [
                            {"instrumentId": iid, "name": name, "marketValueUsd": value}
                            for iid, name, value in hits
                        ],
                    }
                    for channel, hits in link.matches_by_channel
                ],
                "totalUsd": link.matched_value_usd,
            },
            file=HOLDINGS_FILE,
            record_key=f"{context.client_id}|{context.snapshot}",
            field_name="market_value_usd",
        )
        share_pct = 100.0 * link.matched_value_usd / total

        # Name each holding under the channel that actually reached it.
        described = "; ".join(
            f"{', '.join(name for _, name, _ in hits[:2])} via '{channel}'"
            for channel, hits in link.matches_by_channel
        )
        builder.interpretation(
            f"event-{link.event_date}-{link.event_index}",
            f"On {link.event_date} the event log records: {link.description} Its "
            f"declared transmission channels are '{link.primary_transmission}'. The "
            f"client's exposure runs through {described}. Together those holdings are "
            f"worth USD {link.matched_value_usd:,.0f}, or {share_pct:.1f}% of their "
            "wealth. That connection is what the event record supports; it is not a "
            "measured attribution of the change in value.",
            [event_item, holdings_item],
        )

    if material:
        builder.assumption(
            "controlled-event-source",
            "Every statement about a 2026 event comes from event_log.csv. The engine "
            "does not use outside knowledge of world events, and it links an event to "
            "a client only where a declared transmission channel matches an instrument "
            "they hold.",
            [],
        )
        builder.uncertainty(
            "attribution-limits",
            "Linking an event to a holding is not performance attribution. The dataset "
            "supplies five dated snapshots, not a return series, so the engine does not "
            "claim how much of any change a given event caused.",
            snapshot_items,
        )
    return material
