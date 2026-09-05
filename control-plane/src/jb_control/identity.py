"""OIDC token validation.

Validation happens on the server against the issuer's published keys. Nothing
the browser asserts about who it is survives this boundary: the subject, roles
and expiry all come from the verified token.

The checks are the standard ones, written out rather than left to defaults,
because each has been a real breach at some point: unverified signature,
`alg: none`, an RSA public key accepted as an HMAC secret, a token minted for a
different audience, and a token past expiry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

import jwt
from jwt import PyJWKClient

from jb_control.errors import AuthenticationError

# Asymmetric only. A symmetric algorithm here would let a caller sign tokens
# with the public key everyone already has.
PERMITTED_ALGORITHMS = ("RS256", "RS384", "RS512", "ES256", "ES384")

REQUIRED_CLAIMS = ("iss", "aud", "sub", "exp", "iat")


@dataclass(frozen=True)
class Principal:
    """Who the caller is, according to the token — not according to the request."""

    subject: str
    issuer: str
    roles: tuple[str, ...] = ()
    expires_at: datetime | None = None

    def has_role(self, role: str) -> bool:
        return role in self.roles


class KeyResolver(Protocol):
    """Supplies the signing key for a token. Backed by JWKS in production."""

    def key_for(self, token: str) -> Any: ...


@dataclass
class StaticKeyResolver:
    """A fixed key set, for tests and offline sandbox profiles."""

    keys_by_id: dict[str, Any] = field(default_factory=dict)

    def key_for(self, token: str) -> Any:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as error:
            raise AuthenticationError("malformed_token_header") from error
        key_id = header.get("kid")
        if key_id is None:
            raise AuthenticationError("missing_kid")
        key = self.keys_by_id.get(key_id)
        if key is None:
            raise AuthenticationError("unknown_signing_key")
        return key


@dataclass
class JwksKeyResolver:
    """Resolves signing keys from the issuer's published JWKS endpoint."""

    jwks_uri: str
    _client: PyJWKClient | None = None

    def key_for(self, token: str) -> Any:
        if self._client is None:
            self._client = PyJWKClient(self.jwks_uri)
        try:
            return self._client.get_signing_key_from_jwt(token).key
        except Exception as error:  # network, rotation, malformed JWKS
            # Failing closed matters more here than distinguishing the cause.
            raise AuthenticationError("signing_key_unavailable") from error


@dataclass
class TokenValidator:
    """Validates a bearer token and returns the trusted principal."""

    issuer: str
    audience: str
    key_resolver: KeyResolver
    roles_claim: str = "groups"
    leeway_seconds: int = 0

    def validate(self, token: str | None) -> Principal:
        if not token:
            raise AuthenticationError("missing_token")

        key = self.key_resolver.key_for(token)
        try:
            claims = jwt.decode(
                token,
                key=key,
                algorithms=list(PERMITTED_ALGORITHMS),
                audience=self.audience,
                issuer=self.issuer,
                leeway=self.leeway_seconds,
                options={
                    "require": list(REQUIRED_CLAIMS),
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": True,
                },
            )
        except jwt.ExpiredSignatureError as error:
            raise AuthenticationError("token_expired") from error
        except jwt.ImmatureSignatureError as error:
            raise AuthenticationError("token_not_yet_valid") from error
        except jwt.InvalidAudienceError as error:
            raise AuthenticationError("wrong_audience") from error
        except jwt.InvalidIssuerError as error:
            raise AuthenticationError("wrong_issuer") from error
        except jwt.MissingRequiredClaimError as error:
            raise AuthenticationError("missing_required_claim") from error
        except jwt.InvalidSignatureError as error:
            raise AuthenticationError("bad_signature") from error
        except jwt.PyJWTError as error:
            raise AuthenticationError("invalid_token") from error

        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject.strip():
            raise AuthenticationError("missing_subject")

        raw_roles = claims.get(self.roles_claim, [])
        if isinstance(raw_roles, str):
            raw_roles = [raw_roles]
        roles = tuple(sorted(str(role) for role in raw_roles))

        expires_at = None
        if isinstance(claims.get("exp"), (int, float)):
            expires_at = datetime.fromtimestamp(float(claims["exp"]), tz=timezone.utc)

        return Principal(
            subject=subject, issuer=self.issuer, roles=roles, expires_at=expires_at
        )
