"""Normalisation of supplied values into comparable, dated facts.

The dataset expresses obligations with a free-text `recurrence` and a
`certainty` phrase. Both are normalised here so downstream detectors compare
like with like, and so wording is always derived from dates rather than
hard-coded.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

import pandas as pd

CONFIRMED = "Confirmed"
LIKELY = "Likely"
CONDITIONAL = "Conditional"
ASPIRATIONAL = "Aspirational"

# Ordered strongest first. A certainty phrase that matches nothing is treated
# as Conditional rather than silently promoted to Confirmed.
_CERTAINTY_PATTERNS = (
    (CONFIRMED, re.compile(r"^confirmed", re.IGNORECASE)),
    (LIKELY, re.compile(r"^likely", re.IGNORECASE)),
    (ASPIRATIONAL, re.compile(r"aspirational", re.IGNORECASE)),
    (CONDITIONAL, re.compile(r"conditional", re.IGNORECASE)),
)

_RECURRING = re.compile(r"annual|recurring|quarterly|monthly", re.IGNORECASE)
_IRREGULAR = re.compile(r"irregular", re.IGNORECASE)


def normalise_certainty(raw: str | float | None) -> str:
    """Map a free-text certainty phrase onto a comparable category."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return CONDITIONAL
    text = str(raw).strip()
    for label, pattern in _CERTAINTY_PATTERNS:
        if pattern.search(text):
            return label
    return CONDITIONAL


@dataclass(frozen=True)
class CashNeedOccurrence:
    """The next time a planned cash need actually falls due."""

    need_id: str
    client_id: str
    description: str
    currency: str
    amount: float
    certainty: str
    recurrence: str
    window_from: date
    window_to: date
    next_due: date
    days_remaining: int
    in_open_window: bool

    @property
    def is_confirmed(self) -> bool:
        return self.certainty == CONFIRMED

    @property
    def is_actionable(self) -> bool:
        """Confirmed and Likely needs are planned against; the rest are noted."""
        return self.certainty in (CONFIRMED, LIKELY)


def _anniversary_on_or_after(anchor: date, as_of: date) -> date:
    """Next yearly anniversary of `anchor` falling on or after `as_of`."""
    if anchor >= as_of:
        return anchor
    year = as_of.year
    while True:
        try:
            candidate = anchor.replace(year=year)
        except ValueError:  # 29 February in a non-leap year
            candidate = anchor.replace(year=year, day=28)
        if candidate >= as_of:
            return candidate
        year += 1


def next_occurrence(row: pd.Series, as_of: date) -> CashNeedOccurrence:
    """Resolve one `planned_cash_needs` row to its next due date."""
    window_from = date.fromisoformat(str(row["due_from"]))
    window_to = date.fromisoformat(str(row["due_to"]))
    recurrence = str(row["recurrence"])

    if _RECURRING.search(recurrence):
        candidate = _anniversary_on_or_after(window_from, as_of)
        next_due = min(candidate, window_to) if candidate > window_to else candidate
    elif _IRREGULAR.search(recurrence):
        # An irregular call inside an open window may land at any time; treat
        # the window opening as the planning date and never move it earlier.
        next_due = window_from if window_from >= as_of else as_of
    else:  # one-off
        next_due = window_from

    return CashNeedOccurrence(
        need_id=str(row["need_id"]),
        client_id=str(row["client_id"]),
        description=str(row["description"]),
        currency=str(row["currency"]),
        amount=float(row["amount"]),
        certainty=normalise_certainty(row.get("certainty")),
        recurrence=recurrence,
        window_from=window_from,
        window_to=window_to,
        next_due=next_due,
        days_remaining=(next_due - as_of).days,
        in_open_window=window_from <= as_of <= window_to,
    )


def occurrences(cash_needs: pd.DataFrame, as_of: date) -> list[CashNeedOccurrence]:
    """Resolve every supplied cash need, ordered by how soon it falls due."""
    resolved = [next_occurrence(row, as_of) for _, row in cash_needs.iterrows()]
    return sorted(resolved, key=lambda o: (o.days_remaining, o.need_id))


def excerpt(text: str, limit: int = 220) -> str:
    """A short, exact excerpt of note text, cut on a sentence where possible."""
    cleaned = " ".join(str(text).split())
    if len(cleaned) <= limit:
        return cleaned
    cut = cleaned[:limit]
    stop = cut.rfind(". ")
    if stop > limit * 0.5:
        return cut[: stop + 1]
    return cut.rstrip() + "..."


def excerpt_around(text: str, pattern: re.Pattern[str], limit: int = 240) -> str:
    """An exact excerpt containing the phrase that triggered a detection.

    Quoting the opening of a note is useless when the evidence is three
    sentences in, so the window is centred on the match and then widened to
    whole sentences. The text itself is never altered.
    """
    cleaned = " ".join(str(text).split())
    match = pattern.search(cleaned)
    if match is None or len(cleaned) <= limit:
        return excerpt(cleaned, limit)

    # Widen from the match to the sentence that contains it.
    start = cleaned.rfind(". ", 0, match.start())
    start = 0 if start == -1 else start + 2
    end = cleaned.find(". ", match.end())
    end = len(cleaned) if end == -1 else end + 1

    if end - start > limit:
        end = start + limit
        return cleaned[start:end].rstrip() + "..."

    # Use any remaining budget to include the preceding sentence for context.
    remaining = limit - (end - start)
    if remaining > 40 and start > 0:
        previous = cleaned.rfind(". ", 0, start - 2)
        previous = 0 if previous == -1 else previous + 2
        if start - previous <= remaining:
            start = previous
    return cleaned[start:end].strip()
