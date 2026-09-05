"""Payload-safe telemetry.

Observability is where client data leaks by accident: someone adds a span
attribute to debug a problem and a client name ends up in a third-party trace
store forever. So attributes are allowlisted and anything else is refused at
emission rather than filtered downstream.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from jb_control.errors import TelemetryPolicyError
from jb_control.projection import load_classification


def allowed_attributes() -> frozenset[str]:
    return frozenset(load_classification()["telemetryAttributeAllowlist"])


def pseudonymous(value: str, *, salt: str = "aaactual") -> str:
    """A stable, non-reversible correlation handle for an identifier."""
    return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()[:16]


@dataclass
class TelemetrySink:
    """Collects allowlisted signals. Stands in for an OpenTelemetry exporter."""

    spans: list[dict[str, Any]] = field(default_factory=list)

    def emit(self, name: str, attributes: dict[str, Any]) -> dict[str, Any]:
        permitted = allowed_attributes()
        rejected = sorted(set(attributes) - permitted)
        if rejected:
            # Refusing beats dropping silently: a developer adding an attribute
            # finds out immediately instead of shipping a leak.
            raise TelemetryPolicyError(f"denied_attributes:{','.join(rejected)}")
        span = {"name": name, "attributes": dict(attributes)}
        self.spans.append(span)
        return span
