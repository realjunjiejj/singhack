"""Open Loop candidates extracted from dated relationship-manager notes.

The engine proposes; the RM disposes. Every candidate carries its note date, an
exact excerpt, why it may still be open, and `confirmationRequired`, because an
interpretation of free text is not a fact about the relationship.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from jb_clarity.domain.enums import (
    CaseStatus,
    ConfidenceLevel,
    OpenLoopState,
    ScoringFactor,
    SignalType,
)
from jb_clarity.domain.models import Confidence, OpenLoop
from jb_clarity.evidence import ids
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder
from jb_clarity.ingestion.loader import RmNote
from jb_clarity.ingestion.normalization import excerpt_around

NOTES_FILE = "rm_notes.json"

UNANSWERED_QUESTION = "unanswered question"
REPEATED_DEFERRAL = "repeated deferral"
UNRESOLVED_COMMITMENT = "unresolved commitment"
CLIENT_CONSTRAINT = "client constraint"


@dataclass(frozen=True)
class LoopPattern:
    category: str
    pattern: re.Pattern[str]
    why_open: str
    explicit: bool = False


_QUESTION = re.compile(
    r"\b(asked|asking) (whether|what|how|why|if|for a view|for a|for the)\b",
    re.IGNORECASE,
)

# Bank-side action that answers or closes something. Two things reverse the
# meaning and are excluded: the client being the one who acted ("she replied"),
# and negation ("have not yet replied"), which is the strongest possible
# evidence that the loop is still open.
_RESOLUTION = re.compile(
    r"(?<!she )(?<!he )(?<!not )(?<!not yet )"
    r"\b(replied|responded|resolved|executed|completed|signed|"
    r"subscribed|explained|sent a (short )?note|waiver on file|proceeded)\b",
    re.IGNORECASE,
)


def _resolved_after_question(text: str) -> bool:
    """True when the note records bank action *after* its last open question.

    Order matters. A note can record an answer and then a fresh question that
    nobody has answered yet, which is the most common way a loop stays open.
    """
    questions = [m.start() for m in _QUESTION.finditer(text)]
    resolutions = [m.start() for m in _RESOLUTION.finditer(text)]
    if not resolutions:
        return False
    if not questions:
        return True
    return max(resolutions) > max(questions)


# Ordered by strength. An explicit pattern states in the note itself that
# nothing has been done yet, which is stronger evidence than an inference.
PATTERNS: tuple[LoopPattern, ...] = (
    LoopPattern(
        UNANSWERED_QUESTION,
        re.compile(r"have not (yet )?replied|not yet replied|we have not modelled", re.IGNORECASE),
        "The note states that the bank has not yet responded.",
        explicit=True,
    ),
    LoopPattern(
        REPEATED_DEFERRAL,
        re.compile(
            r"\b(second|third|fourth|fifth)\s+attempt|has not executed|"
            r"asked for more time|again in \d{4}",
            re.IGNORECASE,
        ),
        "The note records a decision that has been raised before and is still not settled.",
        explicit=True,
    ),
    LoopPattern(
        UNRESOLVED_COMMITMENT,
        re.compile(
            r"remains? unresolved|asked for a [^.]*\bbefore\b|recommend involving|"
            r"needs? (a proper conversation|monitoring)|before the next",
            re.IGNORECASE,
        ),
        "The note records something the bank undertook to do, with no later record of it being done.",
    ),
    LoopPattern(
        UNANSWERED_QUESTION,
        _QUESTION,
        "The note records a client question with no later record of an answer.",
    ),
    LoopPattern(
        CLIENT_CONSTRAINT,
        re.compile(
            r"did not want|does not want|unwilling|will not sell|"
            r"emotional attachment|dealing restrictions|considers it separate",
            re.IGNORECASE,
        ),
        "The note records a client constraint that changes what an otherwise reasonable action would mean.",
    ),
)

_CATEGORY_POINTS = {
    UNANSWERED_QUESTION: "unansweredQuestion",
    REPEATED_DEFERRAL: "repeatedDeferral",
    UNRESOLVED_COMMITMENT: "unresolvedCommitment",
    CLIENT_CONSTRAINT: "clientConstraint",
}


def detect(context) -> tuple[list[OpenLoop], DetectedSignal | None]:
    notes = context.notes
    if not notes:
        return [], None

    builder = SignalBuilder(context.client_id, SignalType.RELATIONSHIP, status=CaseStatus.ACTIVE)
    found: dict[str, tuple[RmNote, LoopPattern]] = {}

    for note in notes:
        # A single note often carries more than one kind of loop: a question
        # and a constraint, say. Patterns are ordered strongest first, so the
        # first match for a category in this note is the one that counts.
        matched_here: set[str] = set()
        for pattern in PATTERNS:
            if pattern.category in matched_here:
                continue
            if not pattern.pattern.search(note.note):
                continue
            matched_here.add(pattern.category)
            existing = found.get(pattern.category)
            if (
                existing is None
                or note.note_date > existing[0].note_date
                or (
                    note.note_date == existing[0].note_date
                    and pattern.explicit
                    and not existing[1].explicit
                )
            ):
                found[pattern.category] = (note, pattern)

    if not found:
        return [], None

    loops: list[OpenLoop] = []
    item_ids: list[str] = []

    for category in (
        UNANSWERED_QUESTION,
        REPEATED_DEFERRAL,
        UNRESOLVED_COMMITMENT,
        CLIENT_CONSTRAINT,
    ):
        if category not in found:
            continue
        note, pattern = found[category]
        later_notes = [n for n in notes if n.note_date > note.note_date]
        # Resolution recorded inside the same note ("Explained duration", "he
        # subscribed the following day") is direct evidence the item was
        # handled. Resolution language in a *later* note is not: it usually
        # refers to some other subject entirely, so it is not treated as
        # closing this loop.
        resolved_in_note = (
            not pattern.explicit
            and pattern.category in (UNANSWERED_QUESTION, UNRESOLVED_COMMITMENT)
            and _resolved_after_question(note.note)
        )

        quoted = excerpt_around(note.note, pattern.pattern)
        item_id = builder.item(
            f"note-{note.note_id}-{category}",
            f"{note.channel} note, {note.note_date.isoformat()}",
            quoted,
            file=NOTES_FILE,
            record_key=note.note_id,
            field_name="note",
        )
        item_ids.append(item_id)

        score = 85.0 if pattern.explicit else 70.0
        reasons = [
            f"Read from a dated {note.channel.lower()} note of "
            f"{note.note_date.isoformat()}.",
            "Requires RM confirmation before it becomes a tracked commitment.",
        ]
        if resolved_in_note:
            score -= 20.0
            reasons.append(
                "The same note records action taken, so this may already be closed."
            )
        if later_notes:
            score -= 5.0
            reasons.append(
                f"{len(later_notes)} later note(s) exist with no recorded outcome for this."
            )

        level = (
            ConfidenceLevel.HIGH
            if score >= 80
            else ConfidenceLevel.MEDIUM
            if score >= 55
            else ConfidenceLevel.LOW
        )

        loops.append(
            OpenLoop(
                id=ids.open_loop_id(context.client_id, note.note_id, category),
                summary=_summarise(category, note),
                note_date=note.note_date,
                source_excerpt=quoted,
                why_open=pattern.why_open,
                confidence=Confidence(level=level, score=score, reasons=reasons),
                confirmation_required=True,
                state=OpenLoopState.CANDIDATE,
                evidence_item_ids=[item_id],
            )
        )
        builder.uncertainty(
            f"loop-{note.note_id}",
            f"{_summarise(category, note)} This is read from a free-text note and is "
            "proposed for the RM to confirm, defer, assign or dismiss.",
            [item_id],
        )

    builder.deduct_confidence(
        "Relationship signals are interpretations of free-text notes awaiting RM "
        "confirmation.",
        context.config["confidence"]["deductions"]["requiresClientConfirmation"],
    )

    settings = context.factor(ScoringFactor.RELATIONSHIP_SIGNAL)
    best_category = next(
        category
        for category in (
            UNANSWERED_QUESTION,
            REPEATED_DEFERRAL,
            UNRESOLVED_COMMITMENT,
            CLIENT_CONSTRAINT,
        )
        if category in found
    )
    points = float(settings[_CATEGORY_POINTS[best_category]])
    bonus = float(context.config["urgency"]["additionalContributionBonus"])
    points = min(points + bonus * (len(found) - 1), float(settings["max"]))
    builder.score(
        ScoringFactor.RELATIONSHIP_SIGNAL,
        points,
        f"The most recent {best_category} is recorded in the "
        f"{found[best_category][0].note_date.isoformat()} note"
        + (f", with {len(found) - 1} other open relationship signal(s)." if len(found) > 1 else "."),
    )

    signal = builder.finish(
        summary=f"{len(loops)} Open Loop candidate(s) from dated RM notes.",
        time_horizon="since the note date",
        severity_rank=35,
    )
    return loops, signal


def _summarise(category: str, note: RmNote) -> str:
    return {
        UNANSWERED_QUESTION: (
            f"A client question from {note.note_date.isoformat()} has no recorded answer."
        ),
        REPEATED_DEFERRAL: (
            f"A decision raised again on {note.note_date.isoformat()} remains unresolved."
        ),
        UNRESOLVED_COMMITMENT: (
            f"A commitment recorded on {note.note_date.isoformat()} has no recorded outcome."
        ),
        CLIENT_CONSTRAINT: (
            f"A client constraint recorded on {note.note_date.isoformat()} still limits "
            "what can be proposed."
        ),
    }[category]
