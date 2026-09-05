"""Audit: completeness, append-only behaviour, and tamper evidence."""

from __future__ import annotations

import json

import jsonschema
import pytest

from jb_control.audit import GENESIS, AuditLog, content_hash
from jb_control.errors import DependencyUnavailableError
from tests.conftest import REPO_ROOT

SCHEMA_PATH = REPO_ROOT / "control-plane" / "contracts" / "audit-event.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    with SCHEMA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _write(log: AuditLog, outcome: str = "allowed", **overrides):
    payload = {
        "actor": {"subject": "rm-alpha", "issuer": "https://idp.local", "roles": ["relationship-manager"]},
        "action": "view_case",
        "outcome": outcome,
        "purpose": "client_advisory_preparation",
        "policy": {"decision": "permit" if outcome == "allowed" else "deny", "modelVersion": "1.0.0"},
        "correlation_id": "corr-1",
    }
    payload.update(overrides)
    return log.record(**payload)


def test_a_recorded_event_matches_the_published_schema(audit_log, schema):
    record = _write(audit_log)
    body = {key: value for key, value in record.items() if key != "chain"}
    jsonschema.Draft202012Validator(schema).validate(body)


def test_a_denial_is_recorded(audit_log):
    _write(audit_log, outcome="denied", reason="no_relation")
    events = audit_log.events()
    assert len(events) == 1
    assert events[0]["outcome"] == "denied"
    assert events[0]["reason"] == "no_relation"


def test_a_failure_is_recorded(audit_log):
    _write(audit_log, outcome="failed", reason="authorization_store_unavailable")
    assert audit_log.events()[0]["outcome"] == "failed"


def test_the_log_has_no_mutation_path(audit_log):
    """Append and read only. There is deliberately no update or delete."""
    _write(audit_log)
    for forbidden in ("update", "delete", "remove", "edit", "truncate"):
        assert not hasattr(audit_log, forbidden)


def test_returned_events_are_copies(audit_log):
    _write(audit_log)
    events = audit_log.events()
    events[0]["outcome"] = "allowed-but-tampered"
    assert audit_log.events()[0]["outcome"] == "allowed"


def test_the_chain_verifies_for_an_untouched_log(audit_log):
    for index in range(5):
        _write(audit_log, correlation_id=f"corr-{index}")
    assert audit_log.verify_chain()


def test_tampering_breaks_the_chain(audit_log):
    for index in range(3):
        _write(audit_log, correlation_id=f"corr-{index}")
    assert audit_log.verify_chain()
    audit_log._records[1]["outcome"] = "allowed"
    audit_log._records[1]["reason"] = "quietly changed"
    assert not audit_log.verify_chain()


def test_removing_a_record_breaks_the_chain(audit_log):
    for index in range(4):
        _write(audit_log, correlation_id=f"corr-{index}")
    del audit_log._records[2]
    assert not audit_log.verify_chain()


def test_the_first_record_links_to_the_genesis_hash(audit_log):
    record = _write(audit_log)
    assert record["chain"]["previous"] == GENESIS


def test_events_are_reconstructable_by_correlation_id(audit_log):
    _write(audit_log, correlation_id="request-a")
    _write(audit_log, correlation_id="request-b")
    _write(audit_log, correlation_id="request-a", action="view_evidence")
    trail = audit_log.by_correlation("request-a")
    assert [event["action"] for event in trail] == ["view_case", "view_evidence"]


def test_an_unavailable_store_refuses_the_write(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl", available=False)
    with pytest.raises(DependencyUnavailableError):
        _write(log)


def test_the_log_survives_a_restart(tmp_path):
    path = tmp_path / "audit.jsonl"
    first = AuditLog(path)
    _write(first, correlation_id="persisted")
    reopened = AuditLog(path)
    assert len(reopened.events()) == 1
    assert reopened.verify_chain()


def test_content_hashes_prove_change_without_copying_content():
    before = {"openingQuestion": "Could we review the facility buffer?"}
    after = {"openingQuestion": "Could we review the property funding?"}
    before_hash, after_hash = content_hash(before), content_hash(after)
    assert before_hash != after_hash
    assert len(before_hash) == 64
    # The hash reveals nothing about the wording it covers.
    assert "facility" not in before_hash


def test_no_client_narrative_is_stored(audit_log):
    """Audit carries identifiers, versions and hashes — never the text."""
    record = _write(
        audit_log,
        subject_refs={"caseId": "CASE-CL-0001", "clientId": "CL-0001"},
        content_hashes={"before": content_hash("secret wording"), "after": None},
    )
    blob = json.dumps(record)
    assert "secret wording" not in blob
    assert "CASE-CL-0001" in blob
