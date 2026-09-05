"""Token validation: issuer, audience, signature, expiry, not-before, claims."""

from __future__ import annotations

import json

import jwt
import pytest

from jb_control.errors import AuthenticationError
from jb_control.identity import StaticKeyResolver, TokenValidator
from tests.conftest import AUDIENCE, ISSUER, KEY_ID, RM_ALPHA


def test_a_valid_token_yields_the_trusted_principal(validator, mint):
    principal = validator.validate(mint(RM_ALPHA, roles=["relationship-manager"]))
    assert principal.subject == RM_ALPHA
    assert principal.issuer == ISSUER
    assert principal.roles == ("relationship-manager",)
    assert principal.has_role("relationship-manager")


def test_a_missing_token_is_refused(validator):
    with pytest.raises(AuthenticationError) as excinfo:
        validator.validate(None)
    assert excinfo.value.reason == "missing_token"
    with pytest.raises(AuthenticationError) as excinfo:
        validator.validate("")
    assert excinfo.value.reason == "missing_token"


def test_a_malformed_token_is_refused(validator):
    with pytest.raises(AuthenticationError):
        validator.validate("not-a-jwt")


def test_an_expired_token_is_refused(validator, mint):
    with pytest.raises(AuthenticationError) as excinfo:
        validator.validate(mint(RM_ALPHA, expires_in=-30))
    assert excinfo.value.reason == "token_expired"


def test_a_token_used_before_its_time_is_refused(validator, mint):
    with pytest.raises(AuthenticationError) as excinfo:
        validator.validate(mint(RM_ALPHA, not_before=600))
    assert excinfo.value.reason == "token_not_yet_valid"


def test_a_token_for_another_audience_is_refused(validator, mint):
    with pytest.raises(AuthenticationError) as excinfo:
        validator.validate(mint(RM_ALPHA, audience="some-other-app"))
    assert excinfo.value.reason == "wrong_audience"


def test_a_token_from_another_issuer_is_refused(validator, mint):
    with pytest.raises(AuthenticationError) as excinfo:
        validator.validate(mint(RM_ALPHA, issuer="https://attacker.example/realms/x"))
    assert excinfo.value.reason == "wrong_issuer"


def test_a_token_signed_by_the_wrong_key_is_refused(validator, mint, other_key):
    """A correctly shaped token from a key we do not trust must not pass."""
    with pytest.raises(AuthenticationError):
        validator.validate(mint(RM_ALPHA, key=other_key))


def test_a_token_with_an_unknown_key_id_is_refused(validator, mint):
    with pytest.raises(AuthenticationError) as excinfo:
        validator.validate(mint(RM_ALPHA, key_id="rotated-away"))
    assert excinfo.value.reason == "unknown_signing_key"


def test_a_token_without_a_key_id_is_refused(validator, signing_key):
    token = jwt.encode({"sub": RM_ALPHA}, signing_key, algorithm="RS256")
    with pytest.raises(AuthenticationError) as excinfo:
        validator.validate(token)
    assert excinfo.value.reason == "missing_kid"


def test_an_unsigned_token_is_refused(validator):
    """`alg: none` is the oldest JWT attack and must never be accepted."""
    token = jwt.encode({"iss": ISSUER, "aud": AUDIENCE, "sub": RM_ALPHA}, key=None, algorithm="none", headers={"kid": KEY_ID})
    with pytest.raises(AuthenticationError):
        validator.validate(token)


def test_a_symmetric_token_signed_with_the_public_key_is_refused(validator, signing_key):
    """The classic algorithm-confusion attack.

    The verifier holds an RSA public key, which is not secret. If it accepted
    HS256, an attacker could use that public key as the HMAC secret and mint
    any token they liked. The token is assembled by hand because PyJWT refuses
    to encode this — an attacker would not be using PyJWT's guardrails.
    """
    import base64
    import hashlib
    import hmac

    from cryptography.hazmat.primitives import serialization

    public_pem = signing_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    def b64(raw: bytes) -> bytes:
        return base64.urlsafe_b64encode(raw).rstrip(b"=")

    header = b64(json.dumps({"alg": "HS256", "typ": "JWT", "kid": KEY_ID}).encode())
    payload = b64(
        json.dumps(
            {"iss": ISSUER, "aud": AUDIENCE, "sub": "attacker", "exp": 9999999999, "iat": 1}
        ).encode()
    )
    signing_input = header + b"." + payload
    signature = b64(hmac.new(public_pem, signing_input, hashlib.sha256).digest())
    forged = (signing_input + b"." + signature).decode()

    with pytest.raises(AuthenticationError):
        validator.validate(forged)


@pytest.mark.parametrize("claim", ["sub", "exp", "iat", "iss", "aud"])
def test_a_token_missing_a_required_claim_is_refused(validator, mint, claim):
    with pytest.raises(AuthenticationError):
        validator.validate(mint(RM_ALPHA, omit=(claim,)))


def test_roles_default_to_empty_rather_than_assumed(validator, mint):
    principal = validator.validate(mint(RM_ALPHA, roles=[]))
    assert principal.roles == ()
    assert not principal.has_role("relationship-manager")
