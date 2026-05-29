"""Tests for the Streamable HTTP transport + read-only (authless) mode.

No network: read-only tools never get far enough to hit the gateway because
account tools raise NotAuthenticated at `client.account_id` first, and the
catalog-mode boot path only constructs the client (login is skipped).
"""

from __future__ import annotations

import asyncio
import json

import pytest
from mcp.server.fastmcp.exceptions import ToolError

import bibliocommons_mcp.server as srv

# ---- transport selection ----


def test_http_not_requested_by_default(monkeypatch):
    monkeypatch.delenv("BIBLIOCOMMONS_MCP_TRANSPORT", raising=False)
    assert srv._http_requested([]) is False
    assert srv._http_requested(["init"]) is False


def test_http_requested_via_serve_flag(monkeypatch):
    monkeypatch.delenv("BIBLIOCOMMONS_MCP_TRANSPORT", raising=False)
    assert srv._http_requested(["serve", "--http"]) is True
    assert srv._http_requested(["serve"]) is False


@pytest.mark.parametrize("val", ["http", "streamable-http", "HTTP"])
def test_http_requested_via_env(monkeypatch, val):
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_TRANSPORT", val)
    assert srv._http_requested([]) is True


# ---- /healthz ----


def _call_healthz():
    return asyncio.run(srv.healthz(None))  # handler ignores the request


def test_healthz_ok_with_config(sample_config):
    resp = _call_healthz()
    assert resp.status_code == 200
    body = json.loads(resp.body)
    assert body["status"] == "ok"
    assert body["library"] == "seattle"
    assert body["mode"] == "authenticated"


def test_healthz_readonly_mode(tmp_path, monkeypatch):
    cfg_path = tmp_path / "no-creds.toml"
    cfg_path.write_text('library = "seattle"\n')
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_CONFIG", str(cfg_path))
    monkeypatch.delenv("BIBLIOCOMMONS_CARD", raising=False)
    monkeypatch.delenv("BIBLIOCOMMONS_PIN", raising=False)
    body = json.loads(_call_healthz().body)
    assert body["mode"] == "read-only"


def test_healthz_misconfigured(tmp_path, monkeypatch):
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_CONFIG", str(tmp_path / "nope.toml"))
    monkeypatch.delenv("BIBLIOCOMMONS_LIBRARY", raising=False)
    resp = _call_healthz()
    assert resp.status_code == 503
    assert json.loads(resp.body)["status"] == "misconfigured"


# ---- read-only catalog mode ----


@pytest.fixture
def readonly_env(tmp_path, monkeypatch):
    """Library configured, no credentials, fresh client globals."""
    cfg_path = tmp_path / "no-creds.toml"
    cfg_path.write_text('library = "seattle"\n')
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_CONFIG", str(cfg_path))
    monkeypatch.delenv("BIBLIOCOMMONS_CARD", raising=False)
    monkeypatch.delenv("BIBLIOCOMMONS_PIN", raising=False)
    monkeypatch.setattr(srv, "_client", None)
    monkeypatch.setattr(srv, "_cfg", None)
    yield


def test_readonly_boots_without_authenticating(readonly_env):
    client = srv._ensure_client()
    assert client.library == "seattle"
    assert client._authed is False
    assert srv._cfg is not None and srv._cfg.has_credentials is False


def test_account_tool_errors_cleanly_in_readonly_mode(readonly_env):
    with pytest.raises(ToolError, match="read-only catalog mode"):
        srv.list_holds()
