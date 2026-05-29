"""Per-user (multi-tenant) credential routing for the WorkOS-authed transport.

No network: `Client` is replaced with a fake, and the authenticated subject is
injected by stubbing `get_access_token`. Verifies that each subject resolves to
their own client/library, that an un-provisioned subject gets a clean setup
error, that clients are cached + isolated per subject, and that the
single-tenant (no-subject) path is unchanged.
"""

from __future__ import annotations

import types

import pytest
from mcp.server.fastmcp.exceptions import ToolError

import bibliocommons_mcp.server as srv
from bibliocommons_mcp.cache import TTLCache
from bibliocommons_mcp.credentials import InMemoryCredentialStore, UserCredentials


class _FakeClient:
    def __init__(self, library: str) -> None:
        self.library = library
        self._authed = False
        self.auth_calls: list[tuple[str, str]] = []

    def authenticate(self, card: str, pin: str) -> None:
        self.auth_calls.append((card, pin))
        self._authed = True


@pytest.fixture
def multiuser(monkeypatch):
    """Fresh per-user state + a fake Client; no global single-tenant client."""
    monkeypatch.setattr(srv, "Client", _FakeClient)
    monkeypatch.setattr(srv, "_cred_store", InMemoryCredentialStore())
    monkeypatch.setattr(srv, "_user_clients", TTLCache(ttl=3600, maxsize=100))
    monkeypatch.setattr(srv, "_client", None)
    monkeypatch.setattr(srv, "_cfg", None)

    def as_subject(subject: str | None):
        token = types.SimpleNamespace(subject=subject) if subject else None
        monkeypatch.setattr(srv, "get_access_token", lambda: token)

    return as_subject


def test_unprovisioned_subject_gets_setup_error(multiuser):
    multiuser("user_new")
    with pytest.raises(ToolError, match="No library account is configured"):
        srv.list_holds()


def test_setup_error_includes_settings_url(multiuser, monkeypatch):
    monkeypatch.setenv(
        "BIBLIOCOMMONS_MCP_SETTINGS_URL", "https://getbiblio.app/account"
    )
    multiuser("user_new")
    with pytest.raises(ToolError, match="https://getbiblio.app/account"):
        srv.list_holds()


def test_resolves_per_user_authenticated_client(multiuser):
    multiuser("user_a")
    srv._cred_store.put(
        "user_a", UserCredentials(library="seattle", card="111", pin="222")
    )
    client = srv._ensure_client()
    assert isinstance(client, _FakeClient)
    assert client.library == "seattle"
    assert client._authed and client.auth_calls == [("111", "222")]


def test_library_only_record_stays_unauthenticated(multiuser):
    """A record with a library but no card/PIN → catalog client, not logged in."""
    multiuser("user_cat")
    srv._cred_store.put("user_cat", UserCredentials(library="sfpl"))
    client = srv._ensure_client()
    assert client.library == "sfpl"
    assert client._authed is False
    assert srv._effective_cfg().library == "sfpl"


def test_clients_cached_and_isolated_per_subject(multiuser):
    srv._cred_store.put("user_a", UserCredentials(library="seattle", card="1", pin="2"))
    srv._cred_store.put("user_b", UserCredentials(library="sfpl", card="3", pin="4"))

    multiuser("user_a")
    a1 = srv._ensure_client()
    a2 = srv._ensure_client()
    assert a1 is a2  # cached
    assert a1.auth_calls == [("1", "2")]  # authenticated once

    multiuser("user_b")
    b = srv._ensure_client()
    assert b is not a1  # isolated
    assert b.library == "sfpl"


def test_single_tenant_path_when_no_subject(multiuser):
    """Subject None (stdio / authless M1) → the single-server client path."""
    multiuser(None)
    sentinel = _FakeClient("seattle")
    srv._client = sentinel  # pretend the single client is already initialized
    assert srv._ensure_client() is sentinel


def test_single_user_mode_uses_config_creds(multiuser, monkeypatch, tmp_path):
    """With BIBLIOCOMMONS_MCP_SINGLE_USER set, an authenticated user with no
    per-user record falls back to the server's own configured card/PIN."""
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_SINGLE_USER", "1")
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_CONFIG", str(tmp_path / "none.toml"))
    monkeypatch.setenv("BIBLIOCOMMONS_LIBRARY", "seattle")
    monkeypatch.setenv("BIBLIOCOMMONS_CARD", "owner-card")
    monkeypatch.setenv("BIBLIOCOMMONS_PIN", "owner-pin")
    multiuser("any_authenticated_user")  # authenticated, but no per-user record
    client = srv._ensure_client()
    assert client.library == "seattle"
    assert client._authed and client.auth_calls == [("owner-card", "owner-pin")]


def test_single_user_mode_off_errors_without_record(multiuser, monkeypatch):
    monkeypatch.delenv("BIBLIOCOMMONS_MCP_SINGLE_USER", raising=False)
    multiuser("any_authenticated_user")
    with pytest.raises(ToolError, match="No library account is configured"):
        srv.list_holds()
