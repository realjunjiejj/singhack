"""Connect recorded life stage and objectives to dated future cash needs."""

from __future__ import annotations

from jb_clarity.domain.enums import CaseStatus, SignalType
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder


def detect(context) -> list[DetectedSignal]:
    objectives = str(context.client["objectives"]).strip()
    life_stage = str(context.client["life_stage"]).strip()
    future = [need for need in context.occurrences if need.days_remaining >= 0]
    if not objectives and not life_stage and not future:
        return []

    builder = SignalBuilder(context.client_id, SignalType.LIFE_EVENT, status=CaseStatus.NORMAL)
    profile_item = builder.item(
        "profile",
        "Life stage and stated objectives",
        {"lifeStage": life_stage, "objectives": objectives},
        file="clients.csv",
        record_key=context.client_id,
        field_name="life_stage|objectives",
    )
    item_ids = [profile_item]
    nearest = future[0] if future else None
    if nearest is not None:
        item_ids.append(builder.item(
            "next-need",
            "Next recorded life-event cash need",
            {
                "description": nearest.description,
                "amount": nearest.amount,
                "currency": nearest.currency,
                "certainty": nearest.certainty,
                "nextDue": nearest.next_due.isoformat(),
                "daysRemaining": nearest.days_remaining,
            },
            file="planned_cash_needs.csv",
            record_key=nearest.need_id,
        ))
    builder.fact(
        "context",
        f"The client is recorded at life stage '{life_stage}' with objectives: {objectives}.",
        [profile_item],
    )
    if nearest is not None:
        builder.interpretation(
            "preparedness",
            f"The next recorded need is {nearest.description}, due in {nearest.days_remaining} days. The RM should compare this future with the supplied allocation and Eligible Liquidity before discussing options.",
            item_ids,
        )
    builder.uncertainty(
        "confirmation",
        "Objectives and life-stage records can become stale; the client should confirm priorities before the RM changes the plan.",
        [profile_item],
    )
    summary = f"{life_stage}: {objectives}"
    if nearest is not None:
        summary += f" Next recorded need: {nearest.description} in {nearest.days_remaining} days."
    elif not summary.rstrip().endswith((".", "?", "!")):
        summary += "."
    return [builder.finish(summary=summary, time_horizon=(f"{nearest.days_remaining} days" if nearest else "long term"), severity_rank=14)]
