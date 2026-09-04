"""Governance Clocks and Open Loop candidates."""

from __future__ import annotations

import re
from datetime import date

from jb_clarity.detectors.governance import classify
from jb_clarity.domain.enums import GovernanceStatus

AS_OF = date(2026, 8, 26)


def test_governance_status_boundaries():
    assert classify(date(2026, 8, 25), AS_OF, 30) == GovernanceStatus.OVERDUE
    assert classify(AS_OF, AS_OF, 30) == GovernanceStatus.DUE_TODAY
    assert classify(date(2026, 8, 27), AS_OF, 30) == GovernanceStatus.DUE_SOON
    assert classify(date(2026, 9, 25), AS_OF, 30) == GovernanceStatus.DUE_SOON
    assert classify(date(2026, 9, 26), AS_OF, 30) == GovernanceStatus.FUTURE


def test_no_client_is_overdue_at_the_fixed_as_of_date(model):
    for case in model.client_cases:
        for clock in case.governance_clocks:
            assert clock.status != GovernanceStatus.OVERDUE


def test_tan_boon_huat_is_due_soon_not_overdue(cases_by_client):
    clocks = cases_by_client["CL-0011"].governance_clocks
    assert len(clocks) == 1
    clock = clocks[0]
    assert clock.due_date == date(2026, 8, 31)
    assert clock.days_remaining == 5
    assert clock.status == GovernanceStatus.DUE_SOON
    assert "due" in clock.summary.lower()
    assert "overdue" not in clock.summary.lower()


def test_governance_wording_is_calculated_from_dates(model):
    for case in model.client_cases:
        for clock in case.governance_clocks:
            assert clock.due_date.isoformat() in clock.summary
            expected = (clock.due_date - date(2026, 8, 26)).days
            assert clock.days_remaining == expected


def test_every_client_has_a_kyc_clock(model):
    assert all(case.governance_clocks for case in model.client_cases)


def test_open_loops_always_require_confirmation(model):
    for case in model.client_cases:
        for loop in case.open_loops:
            assert loop.confirmation_required is True
            assert loop.state == "candidate"
            assert loop.source_excerpt.strip()
            assert loop.why_open.strip()
            assert loop.evidence_item_ids


def test_open_loop_excerpts_are_quoted_verbatim_from_their_note(model, challenge_data):
    """An excerpt must be findable in the note, not a paraphrase of it."""
    notes = {note.note_id: note for note in challenge_data.notes}
    pattern = re.compile(r"^OL-(?P<client>CL-\d+)-(?P<note>N-\d+)-(?P<category>.+)$")
    for case in model.client_cases:
        for loop in case.open_loops:
            match = pattern.match(loop.id)
            assert match, f"unexpected open loop id {loop.id}"
            note = notes[match.group("note")]
            assert loop.note_date == note.note_date
            cleaned = " ".join(note.note.split())
            quoted = loop.source_excerpt.rstrip(". ").removesuffix("..")
            assert quoted in cleaned, f"{loop.id} excerpt is not verbatim"


def test_an_explicit_non_reply_is_high_confidence(cases_by_client):
    """CL-0004's 19 August note says the bank has not replied."""
    loops = cases_by_client["CL-0004"].open_loops
    questions = [loop for loop in loops if "question" in loop.summary]
    assert questions
    loop = questions[0]
    assert loop.note_date == date(2026, 8, 19)
    assert loop.confidence.level == "High"
    assert "deposits" in loop.source_excerpt.lower()


def test_a_question_answered_in_the_same_note_is_low_confidence(cases_by_client):
    """CL-0012's note records the question and the answer together."""
    loops = [
        loop
        for loop in cases_by_client["CL-0012"].open_loops
        if "question" in loop.summary
    ]
    assert loops
    assert loops[0].confidence.level == "Low"
    assert any("already be closed" in reason for reason in loops[0].confidence.reasons)


def test_repeated_deferral_is_detected_for_both_affected_clients(cases_by_client):
    for client_id, note_date in (("CL-0011", date(2026, 5, 20)), ("CL-0009", date(2026, 3, 2))):
        loops = [
            loop
            for loop in cases_by_client[client_id].open_loops
            if "raised again" in loop.summary
        ]
        assert loops, f"{client_id} should show a repeated deferral"
        assert loops[0].note_date == note_date
        assert loops[0].confidence.level == "High"


def test_client_constraints_are_captured_as_loops(cases_by_client):
    loops = cases_by_client["CL-0001"].open_loops
    constraints = [loop for loop in loops if "constraint" in loop.summary]
    assert constraints
    assert "legacy shareholding" in constraints[0].source_excerpt


def test_open_loop_ids_are_unique_within_a_case(model):
    for case in model.client_cases:
        ids = [loop.id for loop in case.open_loops]
        assert len(ids) == len(set(ids))


def test_relationship_signals_lower_confidence_because_they_need_confirming(
    cases_by_client,
):
    reasons = " ".join(cases_by_client["CL-0011"].confidence.reasons).lower()
    assert "confirmation" in reasons or "free-text" in reasons
