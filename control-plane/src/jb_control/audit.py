"""Append-only application audit.

Every decision writes one event, including denials and failures — an access
log that only records successes cannot answer "who tried".

The store exposes append and read. There is deliberately no update or delete
method, so tampering requires going around the application rather than through
it. Records are hash-chained, which makes an alteration or removal detectable
after the fact. That is not the same as immutability: WORM storage and
independent retention are production integrations, and the threat model says
so rather than implying this covers it.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from jb_control.errors import DependencyUnavailableError

SCHEMA_VERSION = "1.0.0"
GENESIS = "0" * 64


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(value: Any) -> str:
    """A stable hash of mutable RM state, so change is provable without copying it."""
    if value is None:
        return ""
    material = value if isinstance(value, str) else _canonical(value)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    schema_version: str
    occurred_at: str
    actor: dict[str, Any]
    action: str
    outcome: str
    purpose: str
    policy: dict[str, Any]
    correlation_id: str
    subject_refs: dict[str, str] = field(default_factory=dict)
    versions: dict[str, str] = field(default_factory=dict)
    revision: dict[str, int | None] = field(default_factory=dict)
    content_hashes: dict[str, str | None] = field(default_factory=dict)
    reason: str | None = None

    def to_record(self) -> dict[str, Any]:
        record: dict[str, Any] = {
            "eventId": self.event_id,
            "schemaVersion": self.schema_version,
            "occurredAt": self.occurred_at,
            "actor": self.actor,
            "action": self.action,
            "outcome": self.outcome,
            "purpose": self.purpose,
            "policy": self.policy,
            "correlationId": self.correlation_id,
        }
        if self.subject_refs:
            record["subjectRefs"] = self.subject_refs
        if self.versions:
            record["versions"] = self.versions
        if self.revision:
            record["revision"] = self.revision
        if self.content_hashes:
            record["contentHashes"] = self.content_hashes
        if self.reason:
            record["reason"] = self.reason
        return record


class AuditLog:
    """Append-only, hash-chained event log.

    The sandbox writes JSON lines. PostgreSQL with pgAudit underneath is the
    intended sandbox database; neither is a substitute for retention controls.
    """

    def __init__(
        self,
        path: Path | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
        available: bool = True,
    ) -> None:
        self._path = Path(path) if path else None
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._records: list[dict[str, Any]] = []
        self.available = available
        if self._path and self._path.exists():
            for line in self._path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self._records.append(json.loads(line))

    # -- append ------------------------------------------------------------
    def record(
        self,
        *,
        actor: dict[str, Any],
        action: str,
        outcome: str,
        purpose: str,
        policy: dict[str, Any],
        correlation_id: str,
        subject_refs: dict[str, str] | None = None,
        versions: dict[str, str] | None = None,
        revision: dict[str, int | None] | None = None,
        content_hashes: dict[str, str | None] | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        if not self.available:
            # An unauditable action must not happen at all.
            raise DependencyUnavailableError("audit_store_unavailable")

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            schema_version=SCHEMA_VERSION,
            occurred_at=self._clock().isoformat().replace("+00:00", "Z"),
            actor=actor,
            action=action,
            outcome=outcome,
            purpose=purpose,
            policy=policy,
            correlation_id=correlation_id,
            subject_refs=subject_refs or {},
            versions=versions or {},
            revision=revision or {},
            content_hashes=content_hashes or {},
            reason=reason,
        )
        record = event.to_record()
        previous = self._records[-1]["chain"]["hash"] if self._records else GENESIS
        record["chain"] = {
            "previous": previous,
            "hash": hashlib.sha256(
                (previous + _canonical(record)).encode("utf-8")
            ).hexdigest(),
        }
        self._records.append(record)
        if self._path:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    # -- read --------------------------------------------------------------
    def events(self) -> list[dict[str, Any]]:
        return [dict(record) for record in self._records]

    def by_correlation(self, correlation_id: str) -> list[dict[str, Any]]:
        """Reconstruct one request's path. This is the reviewer's entry point."""
        return [
            dict(record)
            for record in self._records
            if record.get("correlationId") == correlation_id
        ]

    def verify_chain(self) -> bool:
        """True when no record has been altered or removed."""
        previous = GENESIS
        for record in self._records:
            body = {key: value for key, value in record.items() if key != "chain"}
            expected = hashlib.sha256(
                (previous + _canonical(body)).encode("utf-8")
            ).hexdigest()
            chain = record.get("chain", {})
            if chain.get("previous") != previous or chain.get("hash") != expected:
                return False
            previous = chain["hash"]
        return True
