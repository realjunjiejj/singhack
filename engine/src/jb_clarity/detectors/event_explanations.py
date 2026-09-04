"""Ground portfolio moves in the supplied Controlled Event Source.

This detector does not claim that a market event caused a client's return. It
only surfaces a defensible transmission path when the supplied five-snapshot
history and a declared event channel point in the same direction.
"""

from __future__ import annotations

from jb_clarity.domain.enums import CaseStatus, SignalType
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder

_DURATION_CHANNELS = {"duration", "long-duration fixed income"}


def detect(context) -> list[DetectedSignal]:
    """Explain a material fixed-income decline using grounded duration events."""
    first_value = context.timeline.first.asset_class_usd("Fixed Income")
    last_value = context.timeline.last.asset_class_usd("Fixed Income")
    if first_value <= 0:
        return []

    change_usd = last_value - first_value
    change_pct = 100.0 * change_usd / first_value
    material_decline_pct = float(
        context.config["eventExplanations"]["fixedIncomeDeclinePct"]
    )
    if change_pct > -material_decline_pct:
        return []

    relevant = [
        link
        for link in context.event_links
        if _DURATION_CHANNELS.intersection(link.matched_channels)
        and "yield" in link.description.lower()
    ]
    if not relevant:
        return []

    # The latest matching event is closest to the current snapshot and usually
    # carries the most up-to-date rate context. The earlier history remains in
    # the Controlled Event Source and is not silently blended into causation.
    event = relevant[-1]
    builder = SignalBuilder(
        context.client_id,
        SignalType.EXPLANATION,
        status=CaseStatus.ACTIVE,
        discriminator="fixed-income-duration",
    )

    first_item = builder.item(
        "fixed-income-first",
        f"Fixed Income at {context.timeline.first.snapshot_date}",
        first_value,
        file="holdings.csv",
        record_key=f"{context.client_id}|{context.timeline.first.snapshot_date}|Fixed Income",
        field_name="market_value_usd",
    )
    last_item = builder.item(
        "fixed-income-last",
        f"Fixed Income at {context.timeline.last.snapshot_date}",
        last_value,
        file="holdings.csv",
        record_key=f"{context.client_id}|{context.timeline.last.snapshot_date}|Fixed Income",
        field_name="market_value_usd",
    )
    event_item = builder.item(
        f"event-{event.event_index}",
        f"{event.event_type} event on {event.event_date}",
        {
            "description": event.description,
            "primaryTransmission": event.primary_transmission,
            "severity": event.severity,
        },
        file="event_log.csv",
        record_key=f"{event.event_date}|{event.event_type}|{event.region}",
        field_name="primary_transmission",
    )
    holding_items = []
    for instrument_id, instrument_name, market_value in event.matched_instruments[:5]:
        holding_items.append(
            builder.item(
                f"holding-{instrument_id}",
                f"{instrument_name} at {context.snapshot}",
                market_value,
                file="holdings.csv",
                record_key=f"{context.client_id}|{instrument_id}|{context.snapshot}",
                field_name="market_value_usd",
            )
        )

    builder.fact(
        "fixed-income-change",
        f"Fixed Income fell from USD {first_value:,.0f} to USD {last_value:,.0f} "
        f"across the supplied snapshots, a change of {change_pct:.2f}%.",
        [first_item, last_item],
    )
    builder.fact(
        "controlled-event",
        f"The Controlled Event Source records on {event.event_date}: "
        f"{event.description}",
        [event_item],
    )
    builder.interpretation(
        "duration-transmission",
        "Rising yields are a defensible transmission channel for the decline because "
        f"the client holds {', '.join(name for _, name, _ in event.matched_instruments[:3])}, "
        "which the supplied instrument data maps to duration exposure. This explains "
        "a plausible path, not proof that the event was the sole cause.",
        [event_item, *holding_items],
    )
    builder.uncertainty(
        "not-causation",
        "The supplied data does not include security-level return attribution, yield "
        "sensitivity or cash-flow-adjusted performance, so causal attribution cannot "
        "be quantified.",
        [first_item, last_item, event_item],
    )

    return [
        builder.finish(
            summary=(
                f"Fixed Income fell {abs(change_pct):.1f}%; the Controlled Event Source "
                "records rising yields through a duration channel."
            ),
            time_horizon=(
                f"{context.timeline.first.snapshot_date} to "
                f"{context.timeline.last.snapshot_date}"
            ),
            severity_rank=54,
        )
    ]
