"""Shared fixtures: a real RSA-signed token issuer and a seeded Book."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from jb_control.audit import AuditLog
from jb_control.authorization import Authorizer, RelationshipStore
from jb_control.gateway import ControlPlane
from jb_control.identity import StaticKeyResolver, TokenValidator

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = REPO_ROOT / "artifacts" / "workbench.json"

ISSUER = "https://sandbox-idp.local/realms/aaactual"
AUDIENCE = "aaactual-workbench"
KEY_ID = "sandbox-key-1"

RM_ALPHA = "rm-alpha"          # assigned to CL-0001
RM_BETA = "rm-beta"            # assigned to CL-0003
SPECIALIST = "specialist-lending"
PURPOSE = "client_advisory_preparation"
SPECIALIST_PURPOSE = "specialist_review"


@pytest.fixture(scope="session")
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def other_key():
    """A second issuer's key, for forged-signature tests."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def mint(signing_key):
    """Mint a token. Every claim is overridable so each check can be isolated."""

    def _mint(
        subject: str = RM_ALPHA,
        *,
        issuer: str = ISSUER,
        audience: str = AUDIENCE,
        roles: list[str] | None = None,
        expires_in: int = 900,
        not_before: int = 0,
        key=None,
        key_id: str = KEY_ID,
        algorithm: str = "RS256",
        omit: tuple[str, ...] = (),
    ) -> str:
        now = datetime.now(timezone.utc)
        claims: dict[str, Any] = {
            "iss": issuer,
            "aud": audience,
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
            "nbf": int((now + timedelta(seconds=not_before)).timestamp()),
            "groups": roles if roles is not None else ["relationship-manager"],
        }
        for name in omit:
            claims.pop(name, None)
        return jwt.encode(
            claims, key or signing_key, algorithm=algorithm, headers={"kid": key_id}
        )

    return _mint


@pytest.fixture(scope="session")
def validator(signing_key) -> TokenValidator:
    return TokenValidator(
        issuer=ISSUER,
        audience=AUDIENCE,
        key_resolver=StaticKeyResolver({KEY_ID: signing_key.public_key()}),
    )


@pytest.fixture(scope="session")
def artifact() -> dict[str, Any]:
    assert ARTIFACT.exists(), f"Build the artifact first: {ARTIFACT}"
    with ARTIFACT.open(encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture
def store(artifact) -> RelationshipStore:
    """Two RMs with disjoint Books, plus one delegated case.

    Seeded from the real artifact so the packet/case parentage is genuine
    rather than invented for the test.
    """
    store = RelationshipStore()
    store.assign_rm("CL-0001", RM_ALPHA)
    store.assign_rm("CL-0003", RM_BETA)
    for case in artifact["clientCases"]:
        store.add_case(case["caseId"], case["clientId"])
    for packet in artifact["evidencePackets"]:
        store.add_packet(packet["packetId"], packet["caseId"])
    store.delegate("CASE-CL-0001", SPECIALIST)
    return store


@pytest.fixture
def audit_log(tmp_path) -> AuditLog:
    return AuditLog(tmp_path / "audit.jsonl")


@pytest.fixture
def control_plane(validator, store, audit_log, artifact) -> ControlPlane:
    return ControlPlane(
        validator=validator,
        authorizer=Authorizer(store),
        audit_log=audit_log,
        artifact=artifact,
        artifact_version="workbench@2026-09-04T13:54:07Z",
    )


@pytest.fixture
def alpha_token(mint) -> str:
    return mint(RM_ALPHA)


@pytest.fixture
def beta_token(mint) -> str:
    return mint(RM_BETA)


@pytest.fixture
def specialist_token(mint) -> str:
    return mint(SPECIALIST, roles=["specialist"])


@pytest.fixture
def hartono_packet(artifact) -> str:
    for packet in artifact["evidencePackets"]:
        if packet["caseId"] == "CASE-CL-0001":
            return packet["packetId"]
    raise AssertionError("No packet for CASE-CL-0001 in the artifact")


@pytest.fixture
def margarethe_packet(artifact) -> str:
    for packet in artifact["evidencePackets"]:
        if packet["caseId"] == "CASE-CL-0003":
            return packet["packetId"]
    raise AssertionError("No packet for CASE-CL-0003 in the artifact")
