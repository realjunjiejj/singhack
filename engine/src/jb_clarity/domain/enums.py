"""Canonical enumerations.

Values mirror `contracts/workbench.schema.json` exactly. The glossary in
`CONTEXT.md` governs the vocabulary used here.
"""

from __future__ import annotations

from enum import StrEnum


class UrgencyTier(StrEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    WATCH = "Watch"


class ConfidenceLevel(StrEnum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class CaseStatus(StrEnum):
    """Status of a signal or Client Case.

    `active` and `near` describe the present. `historical-resolved` records a
    condition that occurred in a supplied snapshot and no longer holds.
    """

    ACTIVE = "active"
    NEAR = "near"
    HISTORICAL_RESOLVED = "historical-resolved"
    NORMAL = "normal"


class GuidedAction(StrEnum):
    EXPLAIN = "explain"
    SHOW_EVIDENCE = "show-evidence"
    PREPARE_CONVERSATION = "prepare-conversation"
    REQUEST_INFORMATION = "request-information"
    INVOLVE_SPECIALIST = "involve-specialist"
    CONFIRM_OPEN_LOOP = "confirm-open-loop"
    DEFER_OPEN_LOOP = "defer-open-loop"
    ASSIGN_OPEN_LOOP = "assign-open-loop"
    DISMISS_OPEN_LOOP = "dismiss-open-loop"
    DISMISS_CASE = "dismiss-case"


class GovernanceStatus(StrEnum):
    DUE_SOON = "due-soon"
    DUE_TODAY = "due-today"
    OVERDUE = "overdue"
    FUTURE = "future"


class OpenLoopState(StrEnum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    DEFERRED = "deferred"
    ASSIGNED = "assigned"
    DISMISSED = "dismissed"


class DataQualityStatus(StrEnum):
    CLEAR = "clear"
    ATTENTION = "attention"
    BLOCKED = "blocked"


class IssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    MATERIAL = "material"


class SignalType(StrEnum):
    """Anticipatory Signal families. Also used as Evidence Packet keys."""

    CREDIT = "credit"
    CASH_NEED = "cash-need"
    LIQUIDITY_RESTRICTION = "liquidity-restriction"
    CONCENTRATION = "concentration"
    MANDATE = "mandate"
    EXCLUSION = "exclusion"
    SUITABILITY = "suitability"
    GOVERNANCE = "governance"
    RELATIONSHIP = "relationship"
    EXPLANATION = "explanation"
    DATA_CONFLICT = "data-conflict"
    TAX_AWARE = "tax-aware"
    LIFE_EVENT = "life-event"


class ScoringFactor(StrEnum):
    """Versioned Urgency factors. Every emitted point names one of these."""

    TIME_URGENCY = "time urgency"
    THRESHOLD_HISTORY = "threshold or historical breach"
    SUITABILITY_MISMATCH = "suitability or objective mismatch"
    FINANCIAL_EXPOSURE = "financial exposure"
    RELATIONSHIP_SIGNAL = "relationship signal"


class SafetyOverrideRuleId(StrEnum):
    """The only three conditions that may assign Critical Urgency."""

    ACTIVE_FACILITY_BREACH = "SO-1-ACTIVE-FACILITY-BREACH"
    UNCOVERED_NEAR_OBLIGATION = "SO-2-UNCOVERED-NEAR-OBLIGATION"
    UNWAIVED_BINDING_EXCLUSION = "SO-3-UNWAIVED-BINDING-EXCLUSION"


SAFETY_OVERRIDE_RULES = {
    SafetyOverrideRuleId.ACTIVE_FACILITY_BREACH: (
        "Active facility breach at the as-of date."
    ),
    SafetyOverrideRuleId.UNCOVERED_NEAR_OBLIGATION: (
        "Confirmed obligation beginning within 90 days with Eligible Liquidity "
        "coverage below 100%."
    ),
    SafetyOverrideRuleId.UNWAIVED_BINDING_EXCLUSION: (
        "Unwaived binding mandate exclusion or compliance breach."
    ),
}

LIQUIDITY_TIERS = ["Daily", "Weekly", "Monthly", "Quarterly Gate", "Illiquid"]
