"""Stable error shapes.

Every rejection returns a fixed code and a message written for an operator.
None of them echo the identifier that was requested, because "case CASE-CL-0007
not found" and "case CASE-CL-0007 forbidden" together are an enumeration oracle:
the difference tells an attacker which cases exist.
"""

from __future__ import annotations


class ControlPlaneError(Exception):
    """Base class. Carries a stable code and a leak-free message."""

    code = "control_plane_error"
    message = "The request could not be completed."

    def __init__(self, reason: str | None = None) -> None:
        super().__init__(self.message)
        # `reason` is for the audit record and operator logs only. It never
        # travels back to the caller.
        self.reason = reason or self.code

    def as_response(self) -> dict[str, str]:
        return {"error": self.code, "message": self.message}


class AuthenticationError(ControlPlaneError):
    code = "unauthenticated"
    message = "The request could not be authenticated."


class AuthorizationError(ControlPlaneError):
    """Denial and non-existence are deliberately indistinguishable."""

    code = "not_authorized"
    message = "The requested resource is not available to this user."


class PurposeError(ControlPlaneError):
    code = "purpose_not_permitted"
    message = "The declared purpose does not permit this action."


class DependencyUnavailableError(ControlPlaneError):
    """A required control could not run, so the request fails closed."""

    code = "dependency_unavailable"
    message = "A required control is unavailable, so the request was refused."


class ProjectionError(ControlPlaneError):
    code = "projection_failed"
    message = "The request could not be prepared safely and was refused."


class OutputValidationError(ControlPlaneError):
    code = "generated_output_rejected"
    message = "Generated content failed validation and was discarded."


class TelemetryPolicyError(ControlPlaneError):
    code = "telemetry_attribute_denied"
    message = "An attribute outside the telemetry allowlist was refused."
