"""Priority Queue ordering.

Ordering is fully determined by the data: Safety Overrides first, then score,
then the earliest confirmed obligation, then client identifier. Nothing here
knows which clients are used in the demonstration.
"""

from __future__ import annotations

from dataclasses import dataclass

from jb_clarity.domain.enums import UrgencyTier
from jb_clarity.domain.models import PriorityQueueItem

# Sorts after every real date, so a client with no confirmed obligation ranks
# last on that tie-break rather than first.
NO_CONFIRMED_OBLIGATION = 10**6


@dataclass(frozen=True)
class QueueCandidate:
    item: PriorityQueueItem
    days_to_confirmed_obligation: int | None

    def sort_key(self) -> tuple:
        return (
            0 if self.item.urgency.safety_override is not None else 1,
            -self.item.urgency.score,
            self.days_to_confirmed_obligation
            if self.days_to_confirmed_obligation is not None
            else NO_CONFIRMED_OBLIGATION,
            self.item.client_id,
        )


def order_queue(candidates: list[QueueCandidate]) -> list[PriorityQueueItem]:
    """Return queue items in stable, deterministic priority order."""
    ordered = sorted(candidates, key=QueueCandidate.sort_key)
    items: list[PriorityQueueItem] = []
    for rank, candidate in enumerate(ordered, start=1):
        item = candidate.item.model_copy(update={"rank": rank})
        items.append(item)
    return items


def summarise(items: list[PriorityQueueItem]) -> dict[str, int]:
    return {
        "critical": sum(1 for i in items if i.urgency.tier == UrgencyTier.CRITICAL),
        "high": sum(1 for i in items if i.urgency.tier == UrgencyTier.HIGH),
        "watch": sum(1 for i in items if i.urgency.tier == UrgencyTier.WATCH),
    }
