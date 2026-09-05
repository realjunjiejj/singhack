"""The composed request path.

    token → identity → authorization → purpose → projection → generation
          → output validation → RM review → explicit approval

Every step can only narrow what happens. Nothing downstream can re-widen
access, and every outcome — allowed, denied or failed — writes one audit event
before the caller hears anything.

This module owns control decisions, not financial ones. It never ranks, scores,
recalculates or reinterprets a Client Case; it decides who may see the artifact
the engine already produced, and records that decision.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from jb_control import audit as audit_module
from jb_control.authorization import Action, Authorizer, Decision
from jb_control.audit import AuditLog, content_hash
from jb_control.errors import (
    AuthenticationError,
    AuthorizationError,
    ControlPlaneError,
    DependencyUnavailableError,
    OutputValidationError,
    ProjectionError,
)
from jb_control.identity import Principal, TokenValidator
from jb_control.projection import ModelInput, Redactor, project_packet, validate_generated
from jb_control.telemetry import TelemetrySink, pseudonymous


@dataclass
class BriefState:
    """RM-editable state, with approval bound to what was approved."""

    case_id: str
    revision: int = 1
    content: dict[str, Any] = field(default_factory=dict)
    approved_revision: int | None = None
    approved_artifact_version: str | None = None
    conversation_prepared: bool = False

    def is_approved_for(self, artifact_version: str) -> bool:
        """Approval holds only for the revision and evidence it was given to.

        Editing the brief or regenerating the artifact both invalidate it: an
        approval is a statement about specific content, not a permanent flag.
        """
        return (
            self.approved_revision is not None
            and self.approved_revision == self.revision
            and self.approved_artifact_version == artifact_version
        )


@dataclass
class ControlPlane:
    """The bank-sandbox control envelope around the Workbench artifact."""

    validator: TokenValidator
    authorizer: Authorizer
    audit_log: AuditLog
    artifact: dict[str, Any]
    artifact_version: str
    telemetry: TelemetrySink = field(default_factory=TelemetrySink)
    redactor: Redactor = field(default_factory=Redactor)
    rules_config_version: str = "scoring.v1.json@1.0.0"
    briefs: dict[str, BriefState] = field(default_factory=dict)

    # -- internals ---------------------------------------------------------
    def _packets(self) -> dict[str, dict[str, Any]]:
        return {p["packetId"]: p for p in self.artifact.get("evidencePackets", [])}

    def _cases(self) -> dict[str, dict[str, Any]]:
        return {c["caseId"]: c for c in self.artifact.get("clientCases", [])}

    def _record(
        self,
        principal: Principal | None,
        action: str,
        outcome: str,
        purpose: str,
        decision: Decision | None,
        correlation_id: str,
        *,
        subject_refs: dict[str, str] | None = None,
        reason: str | None = None,
        revision: dict[str, int | None] | None = None,
        hashes: dict[str, str | None] | None = None,
    ) -> None:
        actor = (
            {
                "subject": principal.subject,
                "issuer": principal.issuer,
                "roles": list(principal.roles),
            }
            if principal
            else {"subject": "unauthenticated", "issuer": "unknown", "roles": []}
        )
        policy = {
            "decision": "permit" if outcome == "allowed" else ("deny" if outcome == "denied" else "error"),
            "modelVersion": decision.model_version if decision else "1.0.0",
        }
        if decision and decision.relation:
            policy["reference"] = decision.relation
        self.audit_log.record(
            actor=actor,
            action=action,
            outcome=outcome,
            purpose=purpose,
            policy=policy,
            correlation_id=correlation_id,
            subject_refs=subject_refs or {},
            versions={
                "artifact": self.artifact_version,
                "rulesConfig": self.rules_config_version,
            },
            revision=revision or {},
            content_hashes=hashes or {},
            reason=reason,
        )
        self.telemetry.emit(
            "control_plane.request",
            {
                "jb.action": action,
                "jb.outcome": outcome,
                "jb.policy.decision": policy["decision"],
                "jb.correlation_id": correlation_id,
            },
        )

    def _authenticate(
        self, token: str | None, action: str, purpose: str, correlation_id: str
    ) -> Principal:
        try:
            return self.validator.validate(token)
        except AuthenticationError as error:
            self._record(None, action, "denied", purpose, None, correlation_id, reason=error.reason)
            raise

    def _authorize(
        self,
        principal: Principal,
        action: Action,
        purpose: str,
        correlation_id: str,
        *,
        case_id: str,
        client_id: str | None = None,
        packet_id: str | None = None,
    ) -> Decision:
        try:
            decision = self.authorizer.check(
                principal.subject,
                action,
                case_id=case_id,
                purpose=purpose,
                client_id=client_id,
                packet_id=packet_id,
            )
        except DependencyUnavailableError as error:
            # Fail closed, and still try to record why.
            try:
                self._record(principal, str(action), "failed", purpose, None, correlation_id, reason=error.reason)
            except DependencyUnavailableError:
                pass
            raise

        if not decision.permitted:
            self._record(
                principal, str(action), "denied", purpose, decision, correlation_id,
                reason=decision.reason,
            )
            raise AuthorizationError(decision.reason)
        return decision

    # -- operations --------------------------------------------------------
    def view_case(
        self, token: str | None, case_id: str, *, purpose: str, client_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        correlation_id = correlation_id or str(uuid.uuid4())
        principal = self._authenticate(token, str(Action.VIEW_CASE), purpose, correlation_id)
        decision = self._authorize(
            principal, Action.VIEW_CASE, purpose, correlation_id,
            case_id=case_id, client_id=client_id,
        )
        case = self._cases().get(case_id)
        if case is None:
            self._record(principal, str(Action.VIEW_CASE), "failed", purpose, decision, correlation_id, reason="case_absent_from_artifact")
            raise AuthorizationError("case_absent_from_artifact")
        self._record(
            principal, str(Action.VIEW_CASE), "allowed", purpose, decision, correlation_id,
            subject_refs={"caseId": case_id, "clientId": case["clientId"]},
        )
        return case

    def view_evidence(
        self, token: str | None, case_id: str, packet_id: str, *, purpose: str,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        correlation_id = correlation_id or str(uuid.uuid4())
        principal = self._authenticate(token, str(Action.VIEW_EVIDENCE), purpose, correlation_id)
        decision = self._authorize(
            principal, Action.VIEW_EVIDENCE, purpose, correlation_id,
            case_id=case_id, packet_id=packet_id,
        )
        packet = self._packets().get(packet_id)
        if packet is None or packet.get("caseId") != case_id:
            self._record(principal, str(Action.VIEW_EVIDENCE), "denied", purpose, decision, correlation_id, reason="packet_outside_case")
            raise AuthorizationError("packet_outside_case")
        self._record(
            principal, str(Action.VIEW_EVIDENCE), "allowed", purpose, decision, correlation_id,
            subject_refs={"caseId": case_id, "packetId": packet_id},
        )
        return packet

    def prepare_conversation(
        self,
        token: str | None,
        case_id: str,
        packet_id: str,
        *,
        purpose: str,
        task: str = "draft_meeting_brief",
        language_adapter: Callable[[ModelInput], dict[str, Any]] | None = None,
        canonical_text: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Project one packet, optionally generate, validate, return a draft.

        With no adapter the cached canonical content stands, which is the
        offline path the demonstration runs on.
        """
        correlation_id = correlation_id or str(uuid.uuid4())
        action = str(Action.PREPARE_CONVERSATION)
        principal = self._authenticate(token, action, purpose, correlation_id)
        decision = self._authorize(
            principal, Action.PREPARE_CONVERSATION, purpose, correlation_id,
            case_id=case_id, packet_id=packet_id,
        )

        packet = self._packets().get(packet_id)
        if packet is None or packet.get("caseId") != case_id:
            self._record(principal, action, "denied", purpose, decision, correlation_id, reason="packet_outside_case")
            raise AuthorizationError("packet_outside_case")

        try:
            model_input = project_packet(packet, task=task, redactor=self.redactor)
        except ProjectionError as error:
            self._record(principal, action, "failed", purpose, decision, correlation_id, reason=error.reason)
            raise

        if language_adapter is None:
            self._record(
                principal, action, "allowed", purpose, decision, correlation_id,
                subject_refs={"caseId": case_id, "packetId": packet_id},
                reason="cached_content_used",
            )
            return {"source": "cached", "modelInput": model_input.as_dict()}

        try:
            generated = validate_generated(
                language_adapter(model_input), model_input, canonical_text=canonical_text
            )
        except OutputValidationError as error:
            # Fail closed to cached content rather than showing unvalidated text.
            self._record(principal, action, "failed", purpose, decision, correlation_id, reason=error.reason)
            raise

        self._record(
            principal, action, "allowed", purpose, decision, correlation_id,
            subject_refs={"caseId": case_id, "packetId": packet_id},
        )
        return {"source": "generated", "draft": generated}

    def edit_brief(
        self, token: str | None, case_id: str, content: dict[str, Any], *, purpose: str,
        correlation_id: str | None = None,
    ) -> BriefState:
        correlation_id = correlation_id or str(uuid.uuid4())
        action = str(Action.EDIT_BRIEF)
        principal = self._authenticate(token, action, purpose, correlation_id)
        decision = self._authorize(principal, Action.EDIT_BRIEF, purpose, correlation_id, case_id=case_id)

        brief = self.briefs.setdefault(case_id, BriefState(case_id=case_id))
        before = content_hash(brief.content)
        previous_revision = brief.revision

        brief.content = content
        brief.revision += 1
        # Editing invalidates approval and the prepared state: the RM approved
        # different words.
        brief.approved_revision = None
        brief.approved_artifact_version = None
        brief.conversation_prepared = False

        self._record(
            principal, action, "allowed", purpose, decision, correlation_id,
            subject_refs={"caseId": case_id, "briefId": case_id},
            revision={"previous": previous_revision, "resulting": brief.revision},
            hashes={"before": before, "after": content_hash(brief.content)},
        )
        return brief

    def approve_brief(
        self, token: str | None, case_id: str, *, purpose: str,
        correlation_id: str | None = None,
    ) -> BriefState:
        correlation_id = correlation_id or str(uuid.uuid4())
        action = str(Action.APPROVE_BRIEF)
        principal = self._authenticate(token, action, purpose, correlation_id)
        decision = self._authorize(principal, Action.APPROVE_BRIEF, purpose, correlation_id, case_id=case_id)

        brief = self.briefs.setdefault(case_id, BriefState(case_id=case_id))
        brief.approved_revision = brief.revision
        brief.approved_artifact_version = self.artifact_version
        brief.conversation_prepared = True

        self._record(
            principal, action, "allowed", purpose, decision, correlation_id,
            subject_refs={"caseId": case_id, "briefId": case_id},
            revision={"previous": brief.revision, "resulting": brief.revision},
            hashes={"before": None, "after": content_hash(brief.content)},
        )
        return brief

    def adopt_artifact(self, artifact: dict[str, Any], artifact_version: str) -> None:
        """Swap in a regenerated artifact.

        Approvals bound to the previous version stop being current. Nothing is
        deleted; `is_approved_for` simply stops answering yes.
        """
        self.artifact = artifact
        self.artifact_version = artifact_version


def stable_error(error: ControlPlaneError) -> dict[str, str]:
    """The only shape an error ever takes on the way out."""
    return error.as_response()


__all__ = [
    "BriefState",
    "ControlPlane",
    "stable_error",
    "audit_module",
    "pseudonymous",
]
