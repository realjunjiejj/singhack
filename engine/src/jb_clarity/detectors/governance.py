"""Governance Clocks: time-sensitive compliance and administrative deadlines.

Wording is calculated from the as-of date, never hard-coded, so a review that
is only due soon is never described as overdue.
"""

from __future__ import annotations

from datetime import date

from jb_clarity.domain.enums import (
    CaseStatus,
    GovernanceStatus,
    ScoringFactor,
    SignalType,
)
from jb_clarity.domain.models import GovernanceClock
from jb_clarity.evidence import ids
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder

CLIENTS_FILE = "clients.csv"


def classify(due: date, as_of: date, due_soon_days: int) -> GovernanceStatus:
    if due < as_of:
        return GovernanceStatus.OVERDUE
    if due == as_of:
        return GovernanceStatus.DUE_TODAY
    if (due - as_of).days <= due_soon_days:
        return GovernanceStatus.DUE_SOON
    return GovernanceStatus.FUTURE


def detect(context) -> tuple[list[GovernanceClock], DetectedSignal | None]:
    due_soon_days = int(context.config["governance"]["dueSoonDays"])
    raw = context.client.get("kyc_review_due")
    if raw is None or str(raw) == "nan":
        return [], None

    due = date.fromisoformat(str(raw))
    status = classify(due, context.as_of, due_soon_days)
    days_remaining = (due - context.as_of).days

    builder = SignalBuilder(
        context.client_id, SignalType.GOVERNANCE, status=CaseStatus.NORMAL
    )
    item = builder.item(
        "kyc",
        "KYC review due date",
        str(raw),
        file=CLIENTS_FILE,
        record_key=context.client_id,
        field_name="kyc_review_due",
    )

    if status == GovernanceStatus.OVERDUE:
        summary = (
            f"The KYC review was due on {due.isoformat()}, {abs(days_remaining)} days "
            "before the as-of date."
        )
    elif status == GovernanceStatus.DUE_TODAY:
        summary = f"The KYC review is due today, {due.isoformat()}."
    elif status == GovernanceStatus.DUE_SOON:
        summary = (
            f"The KYC review is due on {due.isoformat()}, in {days_remaining} days."
        )
    else:
        summary = f"The KYC review is due on {due.isoformat()}, in {days_remaining} days."

    builder.fact("kyc", summary, [item])

    clock = GovernanceClock(
        id=ids.governance_clock_id(context.client_id, "KYC"),
        type="KYC review",
        due_date=due,
        days_remaining=days_remaining,
        status=status,
        summary=summary,
        evidence_item_ids=[item],
    )

    settings = context.factor(ScoringFactor.TIME_URGENCY)
    if status == GovernanceStatus.OVERDUE:
        builder.score(
            ScoringFactor.TIME_URGENCY,
            float(settings["governanceOverduePoints"]),
            f"The KYC review passed its due date on {due.isoformat()}.",
        )
    elif status in (GovernanceStatus.DUE_TODAY, GovernanceStatus.DUE_SOON):
        builder.score(
            ScoringFactor.TIME_URGENCY,
            float(settings["governanceDueSoonPoints"]),
            f"The KYC review is due on {due.isoformat()}, within "
            f"{due_soon_days} days of the as-of date.",
        )

    severity = {
        GovernanceStatus.OVERDUE: 75,
        GovernanceStatus.DUE_TODAY: 70,
        GovernanceStatus.DUE_SOON: 40,
        GovernanceStatus.FUTURE: 5,
    }[status]

    signal = builder.finish(
        summary=summary,
        time_horizon=f"{days_remaining} days",
        days_remaining=days_remaining,
        severity_rank=severity,
    )
    return [clock], signal
