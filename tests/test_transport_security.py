"""Tests for Streamable HTTP Host/Origin allowlist (DNS-rebinding protection)."""

from __future__ import annotations

import pytest

import bibliocommons_mcp.server as srv

_ENV = (
    "BIBLIOCOMMONS_MCP_PUBLIC_URL",
    "FLY_APP_NAME",
    "BIBLIOCOMMONS_MCP_ALLOWED_HOSTS",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for k in _ENV:
        monkeypatch.delenv(k, raising=False)


def test_none_without_public_host():
    # Local/dev: keep the SDK's secure localhost-only default.
    assert srv._transport_security() is None


def test_public_url_allows_host_and_origin(monkeypatch):
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_PUBLIC_URL", "https://getbiblio.app")
    ts = srv._transport_security()
    assert ts is not None
    assert "getbiblio.app" in ts.allowed_hosts
    assert "localhost" in ts.allowed_hosts and "127.0.0.1" in ts.allowed_hosts
    assert "https://getbiblio.app" in ts.allowed_origins


def test_fly_app_host_included(monkeypatch):
    monkeypatch.setenv("FLY_APP_NAME", "getbiblio-mcp")
    ts = srv._transport_security()
    assert ts is not None
    assert "getbiblio-mcp.fly.dev" in ts.allowed_hosts
    assert "https://getbiblio-mcp.fly.dev" in ts.allowed_origins


def test_extra_allowed_hosts(monkeypatch):
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_PUBLIC_URL", "https://getbiblio.app")
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_ALLOWED_HOSTS", "a.example, b.example")
    ts = srv._transport_security()
    assert "a.example" in ts.allowed_hosts
    assert "b.example" in ts.allowed_hosts
