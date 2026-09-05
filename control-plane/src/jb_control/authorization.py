"""Relationship-based authorization, deny by default.

The relationships mirror `contracts/authorization-model.fga`, which is the
model intended for OpenFGA. This module evaluates those semantics locally so
the decisions are testable without a server; moving to hosted OpenFGA replaces
the evaluator, not the model.

Two rules carry most of the weight:

* an object is reachable only through its declared parent, so a packet
  identifier alone never grants access;
* the server resolves identifiers against stored tuples before deciding, so a
  browser can ask for anything and still be told no.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from jb_control.errors import AuthorizationError, DependencyUnavailableError

MODEL_VERSION = "1.0.0"


class Action(StrEnum):
    """The actions the control plane enforces separately."""

    VIEW_CASE = "view_case"
    VIEW_EVIDENCE = "view_evidence"
    PREPARE_CONVERSATION = "prepare_conversation"
    EDIT_BRIEF = "edit_brief"
    APPROVE_BRIEF = "approve_brief"
    DELEGATE_SPECIALIST = "delegate_specialist"
    DISMISS_CASE = "dismiss_case"
    EXPORT_CLIENT_READY = "export_client_ready"


# Which relation on the case satisfies each action. Delegation deliberately
# does not extend to changing, approving, dismissing or exporting: a delegated
# specialist advises, the assigned RM remains responsible.
ACTION_RELATIONS: dict[Action, tuple[str, ...]] = {
    Action.VIEW_CASE: ("assigned_rm", "delegated_specialist"),
    Action.VIEW_EVIDENCE: ("assigned_rm", "delegated_specialist"),
    Action.PREPARE_CONVERSATION: ("assigned_rm", "delegated_specialist"),
    Action.EDIT_BRIEF: ("assigned_rm",),
    Action.APPROVE_BRIEF: ("assigned_rm",),
    Action.DELEGATE_SPECIALIST: ("assigned_rm",),
    Action.DISMISS_CASE: ("assigned_rm",),
    Action.EXPORT_CLIENT_READY: ("assigned_rm",),
}

# Actions that may be requested under each declared purpose.
PURPOSE_ACTIONS: dict[str, frozenset[Action]] = {
    "client_advisory_preparation": frozenset(
        {
            Action.VIEW_CASE,
            Action.VIEW_EVIDENCE,
            Action.PREPARE_CONVERSATION,
            Action.EDIT_BRIEF,
            Action.APPROVE_BRIEF,
            Action.EXPORT_CLIENT_READY,
            Action.DISMISS_CASE,
        }
    ),
    "specialist_review": frozenset(
        {Action.VIEW_CASE, Action.VIEW_EVIDENCE, Action.PREPARE_CONVERSATION}
    ),
    "supervision": frozenset({Action.VIEW_CASE, Action.DELEGATE_SPECIALIST}),
}


@dataclass(frozen=True)
class Decision:
    """The outcome of one authorization check, with the reason it came out that way."""

    permitted: bool
    relation: str | None
    reason: str
    model_version: str = MODEL_VERSION


@dataclass
class RelationshipStore:
    """The tuples the model is evaluated against.

    In production this is OpenFGA. Here it is an explicit in-memory graph with
    the same shape, so the tests exercise real relationship traversal rather
    than a stubbed yes.
    """

    # client id -> subjects who are the assigned RM
    client_assigned_rm: dict[str, set[str]] = field(default_factory=dict)
    # case id -> client id
    case_subject: dict[str, str] = field(default_factory=dict)
    # case id -> subjects delegated to review that case
    case_delegated_specialist: dict[str, set[str]] = field(default_factory=dict)
    # packet id -> case id
    packet_parent: dict[str, str] = field(default_factory=dict)
    # team name -> members, for team#member style assignment
    team_members: dict[str, set[str]] = field(default_factory=dict)
    available: bool = True

    # -- writes used by sandbox seeding -----------------------------------
    def assign_rm(self, client_id: str, subject: str) -> None:
        self.client_assigned_rm.setdefault(client_id, set()).add(subject)

    def add_case(self, case_id: str, client_id: str) -> None:
        self.case_subject[case_id] = client_id

    def add_packet(self, packet_id: str, case_id: str) -> None:
        self.packet_parent[packet_id] = case_id

    def delegate(self, case_id: str, subject: str) -> None:
        self.case_delegated_specialist.setdefault(case_id, set()).add(subject)

    def revoke_delegation(self, case_id: str, subject: str) -> None:
        self.case_delegated_specialist.get(case_id, set()).discard(subject)

    def add_team_member(self, team: str, subject: str) -> None:
        self.team_members.setdefault(team, set()).add(subject)

    # -- reads -------------------------------------------------------------
    def _require_available(self) -> None:
        if not self.available:
            raise DependencyUnavailableError("authorization_store_unavailable")

    def case_client(self, case_id: str) -> str | None:
        self._require_available()
        return self.case_subject.get(case_id)

    def packet_case(self, packet_id: str) -> str | None:
        self._require_available()
        return self.packet_parent.get(packet_id)

    def is_assigned_rm(self, subject: str, client_id: str) -> bool:
        self._require_available()
        direct = self.client_assigned_rm.get(client_id, set())
        if subject in direct:
            return True
        # `[user, team#member]` in the model: assignment may name a team.
        return any(
            entry.startswith("team:") and subject in self.team_members.get(entry[5:], set())
            for entry in direct
        )

    def is_delegated_specialist(self, subject: str, case_id: str) -> bool:
        self._require_available()
        return subject in self.case_delegated_specialist.get(case_id, set())


@dataclass
class Authorizer:
    """Deny-by-default checks over the relationship model."""

    store: RelationshipStore

    def check(
        self,
        subject: str,
        action: Action,
        *,
        case_id: str,
        purpose: str,
        client_id: str | None = None,
        packet_id: str | None = None,
    ) -> Decision:
        """Decide whether `subject` may perform `action` on this case.

        `client_id` and `packet_id` are the values the caller supplied. They
        are checked *against* the stored graph rather than trusted: a request
        naming a client the caller is assigned to, paired with a case belonging
        to someone else, is the classic object-level authorization attack and
        is refused here.
        """
        permitted_actions = PURPOSE_ACTIONS.get(purpose)
        if permitted_actions is None:
            return Decision(False, None, "unknown_purpose")
        if action not in permitted_actions:
            return Decision(False, None, "action_not_permitted_for_purpose")

        resolved_client = self.store.case_client(case_id)
        if resolved_client is None:
            # Non-existent and forbidden are the same answer on purpose.
            return Decision(False, None, "case_not_resolvable")

        if client_id is not None and client_id != resolved_client:
            return Decision(False, None, "client_case_mismatch")

        if packet_id is not None:
            parent = self.store.packet_case(packet_id)
            if parent is None or parent != case_id:
                return Decision(False, None, "packet_outside_case")

        for relation in ACTION_RELATIONS[action]:
            if relation == "assigned_rm" and self.store.is_assigned_rm(
                subject, resolved_client
            ):
                return Decision(True, relation, "assigned_rm")
            if relation == "delegated_specialist" and self.store.is_delegated_specialist(
                subject, case_id
            ):
                return Decision(True, relation, "delegated_specialist")

        return Decision(False, None, "no_relation")

    def require(
        self,
        subject: str,
        action: Action,
        *,
        case_id: str,
        purpose: str,
        client_id: str | None = None,
        packet_id: str | None = None,
    ) -> Decision:
        decision = self.check(
            subject,
            action,
            case_id=case_id,
            purpose=purpose,
            client_id=client_id,
            packet_id=packet_id,
        )
        if not decision.permitted:
            raise AuthorizationError(decision.reason)
        return decision
