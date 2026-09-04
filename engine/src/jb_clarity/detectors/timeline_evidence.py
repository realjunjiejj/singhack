"""Source-cited evidence for every point in the five-snapshot timeline."""

from __future__ import annotations

from jb_clarity.domain.enums import CaseStatus, SignalType
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder


def detect(context) -> list[DetectedSignal]:
    if not context.timeline.points:
        return []

    builder = SignalBuilder(
        context.client_id,
        SignalType.TIMELINE,
        status=CaseStatus.NORMAL,
    )
    item_ids: list[str] = []
    for point in context.timeline.points:
        item_ids.append(
            builder.item(
                f"snapshot-{point.snapshot_date}",
                f"Total client market value at {point.snapshot_date}",
                point.total_usd,
                file="holdings.csv",
                record_key=f"{context.client_id}|{point.snapshot_date}",
                field_name="market_value_usd",
            )
        )

    first = context.timeline.first
    last = context.timeline.last
    builder.fact(
        "period-change",
        f"Total market value moved from USD {first.total_usd:,.2f} on "
        f"{first.snapshot_date} to USD {last.total_usd:,.2f} on "
        f"{last.snapshot_date} across the supplied holdings snapshots.",
        [item_ids[0], item_ids[-1]],
    )
    return [
        builder.finish(
            summary="Five supplied portfolio snapshots are available for comparison.",
            time_horizon=f"{first.snapshot_date} to {last.snapshot_date}",
            severity_rank=0,
        )
    ]
