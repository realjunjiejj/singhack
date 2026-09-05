"""The composed path, end to end: identity, authorization, audit, approval."""

from __future__ import annotations

import json

import pytest

from jb_control.errors import (
    AuthenticationError,
    AuthorizationError,
    DependencyUnavailableError,
    OutputValidationError,
)
from jb_control.gateway import stable_error
from jb_control.telemetry import TelemetrySink, pseudonymous
from tests.conftest import PURPOSE, SPECIALIST_PURPOSE


# -- the authorised path ---------------------------------------------------


def test_an_assigned_rm_completes_the_path(control_plane, alpha_token, hartono_packet):
    case = control_plane.view_case(alpha_token, "CASE-CL-0001", purpose=PURPOSE)
    assert case["clientId"] == "CL-0001"

    packet = control_plane.view_evidence(alpha_token, "CASE-CL-0001", hartono_packet, purpose=PURPOSE)
    assert packet["packetId"] == hartono_packet

    prepared = control_plane.prepare_conversation(
        alpha_token, "CASE-CL-0001", hartono_packet, purpose=PURPOSE
    )
    assert prepared["source"] == "cached"

    control_plane.edit_brief(alpha_token, "CASE-CL-0001", {"openingQuestion": "Shall we review the buffer?"}, purpose=PURPOSE)
    brief = control_plane.approve_brief(alpha_token, "CASE-CL-0001", purpose=PURPOSE)

    assert brief.is_approved_for(control_plane.artifact_version)
    assert brief.conversation_prepared


def test_every_step_is_audited(control_plane, alpha_token, hartono_packet):
    correlation = "trace-golden-path"
    control_plane.view_case(alpha_token, "CASE-CL-0001", purpose=PURPOSE, correlation_id=correlation)
    control_plane.view_evidence(alpha_token, "CASE-CL-0001", hartono_packet, purpose=PURPOSE, correlation_id=correlation)
    control_plane.approve_brief(alpha_token, "CASE-CL-0001", purpose=PURPOSE, correlation_id=correlation)

    trail = control_plane.audit_log.by_correlation(correlation)
    assert [event["action"] for event in trail] == ["view_case", "view_evidence", "approve_brief"]
    assert all(event["outcome"] == "allowed" for event in trail)
    assert all(event["versions"]["artifact"] == control_plane.artifact_version for event in trail)
    assert control_plane.audit_log.verify_chain()


# -- denial ----------------------------------------------------------------


def test_another_rms_case_is_refused_and_recorded(control_plane, beta_token):
    with pytest.raises(AuthorizationError):
        control_plane.view_case(beta_token, "CASE-CL-0001", purpose=PURPOSE)
    events = control_plane.audit_log.events()
    assert events[-1]["outcome"] == "denied"
    assert events[-1]["actor"]["subject"] == "rm-beta"


def test_a_missing_token_is_refused_and_recorded(control_plane):
    with pytest.raises(AuthenticationError):
        control_plane.view_case(None, "CASE-CL-0001", purpose=PURPOSE)
    assert control_plane.audit_log.events()[-1]["outcome"] == "denied"


def test_a_foreign_packet_is_refused(control_plane, alpha_token, margarethe_packet):
    with pytest.raises(AuthorizationError):
        control_plane.view_evidence(alpha_token, "CASE-CL-0001", margarethe_packet, purpose=PURPOSE)


def test_denial_reveals_nothing_about_the_target(control_plane, beta_token):
    """Forbidden and non-existent must look identical from outside."""
    try:
        control_plane.view_case(beta_token, "CASE-CL-0001", purpose=PURPOSE)
    except AuthorizationError as error:
        forbidden = stable_error(error)
    try:
        control_plane.view_case(beta_token, "CASE-DOES-NOT-EXIST", purpose=PURPOSE)
    except AuthorizationError as error:
        missing = stable_error(error)

    assert forbidden == missing
    assert "CASE-CL-0001" not in json.dumps(forbidden)


def test_a_specialist_may_prepare_but_not_approve(control_plane, specialist_token, hartono_packet):
    control_plane.view_case(specialist_token, "CASE-CL-0001", purpose=SPECIALIST_PURPOSE)
    control_plane.prepare_conversation(
        specialist_token, "CASE-CL-0001", hartono_packet, purpose=SPECIALIST_PURPOSE
    )
    with pytest.raises(AuthorizationError):
        control_plane.approve_brief(specialist_token, "CASE-CL-0001", purpose=PURPOSE)


# -- fail closed -----------------------------------------------------------


def test_an_unavailable_authorization_store_denies(control_plane, alpha_token, store):
    store.available = False
    with pytest.raises(DependencyUnavailableError):
        control_plane.view_case(alpha_token, "CASE-CL-0001", purpose=PURPOSE)


def test_a_failed_audit_write_denies_the_request(control_plane, alpha_token):
    """An action that cannot be recorded must not happen."""
    control_plane.audit_log.available = False
    with pytest.raises(DependencyUnavailableError):
        control_plane.view_case(alpha_token, "CASE-CL-0001", purpose=PURPOSE)


# -- language boundary -----------------------------------------------------


def test_a_validated_generation_is_returned(control_plane, alpha_token, hartono_packet):
    def adapter(model_input):
        citation = sorted(model_input.allowed_citation_ids)[0]
        return {"content": "A faithful restatement.", "citedEvidenceItemIds": [citation]}

    result = control_plane.prepare_conversation(
        alpha_token, "CASE-CL-0001", hartono_packet, purpose=PURPOSE, language_adapter=adapter
    )
    assert result["source"] == "generated"


def test_output_citing_an_unknown_item_is_rejected(control_plane, alpha_token, hartono_packet):
    def adapter(_):
        return {"content": "Invented.", "citedEvidenceItemIds": ["EV-NOT-REAL"]}

    with pytest.raises(OutputValidationError):
        control_plane.prepare_conversation(
            alpha_token, "CASE-CL-0001", hartono_packet, purpose=PURPOSE, language_adapter=adapter
        )
    assert control_plane.audit_log.events()[-1]["outcome"] == "failed"


def test_the_adapter_never_receives_evidence_items(control_plane, alpha_token, hartono_packet):
    seen: list = []

    def adapter(model_input):
        seen.append(model_input)
        citation = sorted(model_input.allowed_citation_ids)[0]
        return {"content": "Fine.", "citedEvidenceItemIds": [citation]}

    control_plane.prepare_conversation(
        alpha_token, "CASE-CL-0001", hartono_packet, purpose=PURPOSE, language_adapter=adapter
    )
    assert "items" not in seen[0].packet


# -- approval invariants ---------------------------------------------------


def test_approval_is_invalidated_by_a_later_edit(control_plane, alpha_token):
    control_plane.approve_brief(alpha_token, "CASE-CL-0001", purpose=PURPOSE)
    brief = control_plane.briefs["CASE-CL-0001"]
    assert brief.is_approved_for(control_plane.artifact_version)

    control_plane.edit_brief(alpha_token, "CASE-CL-0001", {"openingQuestion": "Changed."}, purpose=PURPOSE)
    assert not brief.is_approved_for(control_plane.artifact_version)
    assert not brief.conversation_prepared


def test_approval_is_invalidated_by_an_artifact_change(control_plane, alpha_token, artifact):
    """An approval is about specific evidence, not a permanent flag."""
    control_plane.approve_brief(alpha_token, "CASE-CL-0001", purpose=PURPOSE)
    brief = control_plane.briefs["CASE-CL-0001"]
    assert brief.is_approved_for(control_plane.artifact_version)

    control_plane.adopt_artifact(artifact, "workbench@2026-09-05T00:00:00Z")
    assert not brief.is_approved_for(control_plane.artifact_version)


def test_an_edit_records_both_revisions_and_hashes(control_plane, alpha_token):
    control_plane.edit_brief(alpha_token, "CASE-CL-0001", {"openingQuestion": "First."}, purpose=PURPOSE)
    control_plane.edit_brief(alpha_token, "CASE-CL-0001", {"openingQuestion": "Second."}, purpose=PURPOSE)
    event = control_plane.audit_log.events()[-1]
    assert event["revision"] == {"previous": 2, "resulting": 3}
    assert event["contentHashes"]["before"] != event["contentHashes"]["after"]
    assert "First." not in json.dumps(event)


def test_replaying_an_approval_does_not_duplicate_the_decision(control_plane, alpha_token):
    first = control_plane.approve_brief(alpha_token, "CASE-CL-0001", purpose=PURPOSE)
    second = control_plane.approve_brief(alpha_token, "CASE-CL-0001", purpose=PURPOSE)
    assert first.approved_revision == second.approved_revision
    assert first.revision == second.revision


# -- boundary of the whole slice -------------------------------------------


def test_no_action_can_send_or_execute(control_plane):
    """There is no route to a client, a trade, or an order. By construction."""
    surface = {name for name in dir(control_plane) if not name.startswith("_")}
    for forbidden in ("send", "email", "message", "trade", "order", "execute", "contact"):
        assert not any(forbidden in name for name in surface)


def test_telemetry_carries_no_client_content(control_plane, alpha_token, hartono_packet):
    control_plane.view_case(alpha_token, "CASE-CL-0001", purpose=PURPOSE)
    control_plane.view_evidence(alpha_token, "CASE-CL-0001", hartono_packet, purpose=PURPOSE)
    blob = json.dumps(control_plane.telemetry.spans)
    for leak in ("CL-0001", "CASE-CL-0001", "Hartono", hartono_packet):
        assert leak not in blob


def test_a_correlation_id_is_pseudonymous():
    handle = pseudonymous("CL-0001")
    assert "CL-0001" not in handle
    assert handle == pseudonymous("CL-0001")
    assert handle != pseudonymous("CL-0003")


def test_telemetry_refuses_an_attribute_outside_the_allowlist():
    from jb_control.errors import TelemetryPolicyError

    sink = TelemetrySink()
    with pytest.raises(TelemetryPolicyError):
        sink.emit("request", {"jb.action": "view_case", "client.name": "Hartono"})
    assert sink.spans == []
