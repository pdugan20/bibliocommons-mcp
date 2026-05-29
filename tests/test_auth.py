"""Unit tests for the WorkOS OAuth Resource-Server token verifier.

No network: the JWKS client is replaced with a fake that returns a locally
generated RSA key, and tokens are minted with that key. Covers signature,
issuer (incl. the trailing-slash quirk), audience, expiry, and required-claim
checks, plus the env-driven config factory.
"""

from __future__ import annotations

import asyncio
import time
import types

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from bibliocommons_mcp.auth import (
    AuthConfigError,
    WorkOSAccessToken,
    WorkOSTokenVerifier,
    workos_auth_from_env,
)

ISSUER = "https://api.workos.com"
AUDIENCE = "https://getbiblio.app/mcp"


@pytest.fixture(scope="module")
def keypair():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return priv, priv.public_key()


def _mint(priv, **overrides) -> str:
    now = int(time.time())
    claims = {
        "sub": "user_01ABC",
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + 3600,
        "scope": "openid profile email",
        "client_id": "client_01CLAUDE",
    }
    claims.update(overrides)
    # Allow tests to drop a claim entirely by passing it as None.
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, priv, algorithm="RS256", headers={"kid": "k1"})


def _verifier(public_key, *, audience: str | None = AUDIENCE, issuer: str = ISSUER):
    v = WorkOSTokenVerifier(issuer=issuer, jwks_url="https://unused", audience=audience)
    v._jwk_client = types.SimpleNamespace(
        get_signing_key_from_jwt=lambda _t: types.SimpleNamespace(key=public_key)
    )
    return v


def _verify(verifier, token):
    return asyncio.run(verifier.verify_token(token))


def test_valid_token(keypair):
    priv, pub = keypair
    tok = _verify(_verifier(pub), _mint(priv))
    assert isinstance(tok, WorkOSAccessToken)
    assert tok.subject == "user_01ABC"
    assert tok.scopes == ["openid", "profile", "email"]
    assert tok.resource == AUDIENCE
    assert tok.client_id == "client_01CLAUDE"
    assert tok.claims["iss"] == ISSUER


def test_issuer_trailing_slash_accepted(keypair):
    """WorkOS emits `iss` with/without a trailing slash across versions."""
    priv, pub = keypair
    tok = _verify(_verifier(pub), _mint(priv, iss="https://api.workos.com/"))
    assert tok is not None and tok.subject == "user_01ABC"


def test_wrong_issuer_rejected(keypair):
    priv, pub = keypair
    assert _verify(_verifier(pub), _mint(priv, iss="https://evil.example")) is None


def test_expired_token_rejected(keypair):
    priv, pub = keypair
    # Well past the verifier's 60s clock-skew leeway.
    assert _verify(_verifier(pub), _mint(priv, exp=int(time.time()) - 3600)) is None


def test_wrong_audience_rejected(keypair):
    priv, pub = keypair
    assert _verify(_verifier(pub), _mint(priv, aud="https://someone-else/mcp")) is None


def test_missing_sub_rejected(keypair):
    priv, pub = keypair
    assert _verify(_verifier(pub), _mint(priv, sub=None)) is None


def test_bad_signature_rejected(keypair):
    _, pub = keypair
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    # Signed by a different key than the verifier trusts.
    assert _verify(_verifier(pub), _mint(other)) is None


def test_audience_not_checked_when_unset(keypair):
    """With no configured audience, tokens lacking `aud` still validate."""
    priv, pub = keypair
    tok = _verify(_verifier(pub, audience=None), _mint(priv, aud=None))
    assert tok is not None and tok.resource is None


# ---- env factory ----


def test_env_no_workos_returns_none(monkeypatch):
    for k in ("WORKOS_JWKS_URL", "WORKOS_CLIENT_ID", "WORKOS_ISSUER"):
        monkeypatch.delenv(k, raising=False)
    assert workos_auth_from_env() is None


def test_env_client_id_derives_jwks(monkeypatch):
    monkeypatch.delenv("WORKOS_JWKS_URL", raising=False)
    monkeypatch.setenv("WORKOS_CLIENT_ID", "client_01XYZ")
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_RESOURCE", AUDIENCE)
    monkeypatch.delenv("WORKOS_ISSUER", raising=False)
    result = workos_auth_from_env()
    assert result is not None
    verifier, settings = result
    assert verifier._jwk_client.get_signing_key_from_jwt  # constructed
    assert str(settings.resource_server_url).rstrip("/") == AUDIENCE
    assert verifier._issuer == ISSUER  # default


def test_env_missing_resource_raises(monkeypatch):
    monkeypatch.setenv("WORKOS_CLIENT_ID", "client_01XYZ")
    monkeypatch.delenv("BIBLIOCOMMONS_MCP_RESOURCE", raising=False)
    monkeypatch.delenv("WORKOS_JWKS_URL", raising=False)
    with pytest.raises(AuthConfigError, match="BIBLIOCOMMONS_MCP_RESOURCE"):
        workos_auth_from_env()
