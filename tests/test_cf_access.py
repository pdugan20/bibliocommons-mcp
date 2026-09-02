"""Unit tests for the Cloudflare Access OAuth Resource-Server token verifier.

No network: the JWKS client is replaced with a fake that returns a locally
generated RSA key, and tokens are minted with that key. Mirrors
tests/test_auth.py's structure since both verifiers share JwksTokenVerifier.
"""

from __future__ import annotations

import asyncio
import time
import types

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from bibliocommons_mcp.auth import AuthConfigError
from bibliocommons_mcp.cf_access import (
    CloudflareAccessAccessToken,
    CloudflareAccessTokenVerifier,
    cf_access_auth_from_env,
)

TEAM_DOMAIN = "https://myteam.cloudflareaccess.com"
AUD = "aud-tag-abc123"


@pytest.fixture(scope="module")
def keypair():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return priv, priv.public_key()


def _mint(priv, **overrides) -> str:
    now = int(time.time())
    claims = {
        "sub": "user-sub-123",
        "iss": TEAM_DOMAIN,
        "aud": AUD,
        "iat": now,
        "exp": now + 3600,
        "email": "person@example.com",
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, priv, algorithm="RS256", headers={"kid": "k1"})


def _verifier(public_key, *, audience: str | None = AUD, issuer: str = TEAM_DOMAIN):
    v = CloudflareAccessTokenVerifier(
        issuer=issuer, jwks_url="https://unused", audience=audience
    )
    v._jwk_client = types.SimpleNamespace(
        get_signing_key_from_jwt=lambda _t: types.SimpleNamespace(key=public_key)
    )
    return v


def _verify(verifier, token):
    return asyncio.run(verifier.verify_token(token))


# ---- verifier: happy path ----


def test_valid_token(keypair):
    priv, pub = keypair
    tok = _verify(_verifier(pub), _mint(priv))
    assert isinstance(tok, CloudflareAccessAccessToken)
    assert tok.subject == "user-sub-123"
    assert tok.scopes == []  # Access issues no OAuth scopes
    assert tok.client_id == AUD
    assert tok.email == "person@example.com"
    assert tok.claims["iss"] == TEAM_DOMAIN


def test_client_id_from_list_aud(keypair):
    """`aud` may be a list; client_id normalizes to its first element."""
    priv, pub = keypair
    tok = _verify(_verifier(pub), _mint(priv, aud=[AUD, "other-aud"]))
    assert tok is not None
    assert tok.client_id == AUD


def test_client_id_falls_back_when_aud_missing(keypair):
    """No configured audience + no `aud` claim: falls back to a placeholder."""
    priv, pub = keypair
    tok = _verify(_verifier(pub, audience=None), _mint(priv, aud=None))
    assert tok is not None
    assert tok.client_id == "cf-access"


# ---- verifier: rejection cases (all assert None, not an exception) ----


def test_wrong_audience_rejected(keypair):
    priv, pub = keypair
    assert _verify(_verifier(pub), _mint(priv, aud="some-other-app")) is None


def test_wrong_issuer_rejected(keypair):
    priv, pub = keypair
    assert _verify(_verifier(pub), _mint(priv, iss="https://evil.example")) is None


def test_expired_token_rejected(keypair):
    priv, pub = keypair
    assert _verify(_verifier(pub), _mint(priv, exp=int(time.time()) - 3600)) is None


def test_bad_signature_rejected(keypair):
    _, pub = keypair
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    assert _verify(_verifier(pub), _mint(other)) is None


def test_malformed_token_rejected(keypair):
    _, pub = keypair
    assert _verify(_verifier(pub), "not-a-jwt") is None


# ---- env factory ----


def test_env_unset_returns_none(monkeypatch):
    monkeypatch.delenv("CF_ACCESS_TEAM_DOMAIN", raising=False)
    monkeypatch.delenv("CF_ACCESS_AUD", raising=False)
    assert cf_access_auth_from_env() is None


def test_env_missing_aud_raises(monkeypatch):
    monkeypatch.setenv("CF_ACCESS_TEAM_DOMAIN", "myteam.cloudflareaccess.com")
    monkeypatch.delenv("CF_ACCESS_AUD", raising=False)
    with pytest.raises(AuthConfigError, match="CF_ACCESS_AUD"):
        cf_access_auth_from_env()


@pytest.mark.parametrize(
    "raw_domain",
    ["myteam.cloudflareaccess.com", "https://myteam.cloudflareaccess.com"],
)
def test_env_normalizes_team_domain(monkeypatch, raw_domain):
    monkeypatch.setenv("CF_ACCESS_TEAM_DOMAIN", raw_domain)
    monkeypatch.setenv("CF_ACCESS_AUD", AUD)
    result = cf_access_auth_from_env()
    assert result is not None
    verifier, settings = result
    assert verifier._issuer == "https://myteam.cloudflareaccess.com"
    assert (
        verifier._jwk_client.uri
        == "https://myteam.cloudflareaccess.com/cdn-cgi/access/certs"
    )
    assert str(settings.issuer_url).rstrip("/") == "https://myteam.cloudflareaccess.com"
    assert settings.resource_server_url is None
    assert settings.required_scopes == []
