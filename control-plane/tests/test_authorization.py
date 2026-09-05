"""Deny-by-default object authorization: horizontal, vertical, and delegation."""

from __future__ import annotations

import pytest

from jb_control.authorization import Action, Authorizer
from jb_control.errors import AuthorizationError, DependencyUnavailableError
from tests.conftest import PURPOSE, RM_ALPHA, RM_BETA, SPECIALIST, SPECIALIST_PURPOSE


@pytest.fixture
def authorizer(store) -> Authorizer:
    return Authorizer(store)


# -- horizontal access ----------------------------------------------------


def test_an_rm_reaches_their_own_client(authorizer):
    decision = authorizer.check(RM_ALPHA, Action.VIEW_CASE, case_id="CASE-CL-0001", purpose=PURPOSE)
    assert decision.permitted
    assert decision.relation == "assigned_rm"


def test_an_rm_cannot_reach_another_rms_client(authorizer):
    decision = authorizer.check(RM_BETA, Action.VIEW_CASE, case_id="CASE-CL-0001", purpose=PURPOSE)
    assert not decision.permitted
    assert decision.reason == "no_relation"


def test_an_unassigned_client_is_denied_by_default(authorizer):
    """CL-0012 has no assignment at all; nobody gets it implicitly."""
    for subject in (RM_ALPHA, RM_BETA, SPECIALIST):
        assert not authorizer.check(subject, Action.VIEW_CASE, case_id="CASE-CL-0012", purpose=PURPOSE).permitted


def test_a_valid_client_paired_with_a_foreign_case_is_denied(authorizer):
    """The classic object-level attack: an id you own plus one you do not."""
    decision = authorizer.check(
        RM_ALPHA, Action.VIEW_CASE, case_id="CASE-CL-0003", purpose=PURPOSE, client_id="CL-0001",
    )
    assert not decision.permitted
    assert decision.reason == "client_case_mismatch"


def test_a_packet_from_another_case_is_denied(authorizer, margarethe_packet):
    decision = authorizer.check(
        RM_ALPHA, Action.VIEW_EVIDENCE, case_id="CASE-CL-0001",
        purpose=PURPOSE, packet_id=margarethe_packet,
    )
    assert not decision.permitted
    assert decision.reason == "packet_outside_case"


def test_a_packet_is_reachable_only_through_its_parent_case(authorizer, hartono_packet):
    assert authorizer.check(
        RM_ALPHA, Action.VIEW_EVIDENCE, case_id="CASE-CL-0001",
        purpose=PURPOSE, packet_id=hartono_packet,
    ).permitted


def test_an_unknown_case_is_indistinguishable_from_a_forbidden_one(authorizer):
    unknown = authorizer.check(RM_ALPHA, Action.VIEW_CASE, case_id="CASE-DOES-NOT-EXIST", purpose=PURPOSE)
    forbidden = authorizer.check(RM_BETA, Action.VIEW_CASE, case_id="CASE-CL-0001", purpose=PURPOSE)
    assert not unknown.permitted and not forbidden.permitted
    # The caller must not be able to tell these apart from the outcome alone.
    assert unknown.permitted == forbidden.permitted


# -- delegation ------------------------------------------------------------


def test_a_specialist_reaches_only_the_delegated_case(authorizer):
    assert authorizer.check(
        SPECIALIST, Action.VIEW_CASE, case_id="CASE-CL-0001", purpose=SPECIALIST_PURPOSE
    ).permitted
    assert not authorizer.check(
        SPECIALIST, Action.VIEW_CASE, case_id="CASE-CL-0003", purpose=SPECIALIST_PURPOSE
    ).permitted


def test_a_specialist_cannot_approve_or_export(authorizer):
    """Delegation is to advise, not to decide. The RM stays responsible."""
    for action in (
        Action.APPROVE_BRIEF,
        Action.EDIT_BRIEF,
        Action.EXPORT_CLIENT_READY,
        Action.DISMISS_CASE,
        Action.DELEGATE_SPECIALIST,
    ):
        assert not authorizer.check(
            SPECIALIST, action, case_id="CASE-CL-0001", purpose=PURPOSE
        ).permitted


def test_revoking_delegation_removes_access_immediately(authorizer, store):
    assert authorizer.check(SPECIALIST, Action.VIEW_CASE, case_id="CASE-CL-0001", purpose=SPECIALIST_PURPOSE).permitted
    store.revoke_delegation("CASE-CL-0001", SPECIALIST)
    assert not authorizer.check(SPECIALIST, Action.VIEW_CASE, case_id="CASE-CL-0001", purpose=SPECIALIST_PURPOSE).permitted


def test_delegation_on_one_case_does_not_widen_to_the_clients_other_cases(authorizer, store):
    """Delegation is recorded on the case, so it cannot leak via the client."""
    store.add_case("CASE-CL-0001-SECOND", "CL-0001")
    assert not authorizer.check(
        SPECIALIST, Action.VIEW_CASE, case_id="CASE-CL-0001-SECOND", purpose=SPECIALIST_PURPOSE
    ).permitted


# -- purpose ---------------------------------------------------------------


def test_an_action_outside_the_declared_purpose_is_denied(authorizer):
    decision = authorizer.check(
        RM_ALPHA, Action.APPROVE_BRIEF, case_id="CASE-CL-0001", purpose=SPECIALIST_PURPOSE
    )
    assert not decision.permitted
    assert decision.reason == "action_not_permitted_for_purpose"


def test_an_unknown_purpose_is_denied(authorizer):
    decision = authorizer.check(RM_ALPHA, Action.VIEW_CASE, case_id="CASE-CL-0001", purpose="curiosity")
    assert not decision.permitted
    assert decision.reason == "unknown_purpose"


# -- team assignment -------------------------------------------------------


def test_assignment_through_a_team_grants_access(authorizer, store):
    store.assign_rm("CL-0012", "team:asia-desk")
    store.add_team_member("asia-desk", "rm-gamma")
    assert authorizer.check("rm-gamma", Action.VIEW_CASE, case_id="CASE-CL-0012", purpose=PURPOSE).permitted
    assert not authorizer.check("rm-delta", Action.VIEW_CASE, case_id="CASE-CL-0012", purpose=PURPOSE).permitted


# -- failure modes ---------------------------------------------------------


def test_an_unavailable_store_fails_closed(authorizer, store):
    store.available = False
    with pytest.raises(DependencyUnavailableError):
        authorizer.check(RM_ALPHA, Action.VIEW_CASE, case_id="CASE-CL-0001", purpose=PURPOSE)


def test_require_raises_rather_than_returning_false(authorizer):
    with pytest.raises(AuthorizationError):
        authorizer.require(RM_BETA, Action.VIEW_CASE, case_id="CASE-CL-0001", purpose=PURPOSE)


def test_every_action_has_a_declared_relation():
    from jb_control.authorization import ACTION_RELATIONS

    for action in Action:
        assert ACTION_RELATIONS.get(action), f"{action} has no relation and would deny silently"
