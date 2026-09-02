"""Tests for server._auth_from_env's WorkOS / Cloudflare Access dispatch.

No network: both env-driven factories only construct JWKS clients (no
fetch at construction time), so this stays fully offline.
"""

from __future__ import annotations

import pytest

import bibliocommons_mcp.server as srv
from bibliocommons_mcp.auth import AuthConfigError

WORKOS_ENV = {
    "WORKOS_CLIENT_ID": "client_01XYZ",
    "BIBLIOCOMMONS_MCP_RESOURCE": "https://getbiblio.app/mcp",
}
CF_ENV = {
    "CF_ACCESS_TEAM_DOMAIN": "myteam.cloudflareaccess.com",
    "CF_ACCESS_AUD": "aud-tag-abc123",
}
ALL_KEYS = (
    "WORKOS_JWKS_URL",
    "WORKOS_CLIENT_ID",
    "WORKOS_ISSUER",
    "BIBLIOCOMMONS_MCP_RESOURCE",
    "CF_ACCESS_TEAM_DOMAIN",
    "CF_ACCESS_AUD",
)


@pytest.fixture(autouse=True)
def _clean_auth_env(monkeypatch):
    for key in ALL_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_neither_configured_returns_none():
    assert srv._auth_from_env() is None


def test_workos_only(monkeypatch):
    for k, v in WORKOS_ENV.items():
        monkeypatch.setenv(k, v)
    result = srv._auth_from_env()
    assert result is not None
    _verifier, _settings, backend = result
    assert backend == "WorkOS OAuth"


def test_cf_access_only(monkeypatch):
    for k, v in CF_ENV.items():
        monkeypatch.setenv(k, v)
    result = srv._auth_from_env()
    assert result is not None
    _verifier, _settings, backend = result
    assert backend == "Cloudflare Access"


def test_both_configured_raises(monkeypatch):
    for k, v in {**WORKOS_ENV, **CF_ENV}.items():
        monkeypatch.setenv(k, v)
    with pytest.raises(AuthConfigError, match="Only one Resource-Server"):
        srv._auth_from_env()
