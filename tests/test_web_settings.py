"""Tests for the /account credential-capture settings page.

No network: the WorkOS code exchange and the BiblioCommons credential check are
injected fakes. Drives the routes through a Starlette TestClient (https base so
the Secure session cookies round-trip).
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from bibliocommons_mcp.credentials import InMemoryCredentialStore
from bibliocommons_mcp.web_settings import (
    AccountSettings,
    WebSettingsConfig,
    WebSettingsConfigError,
    web_settings_from_env,
)

CFG = WebSettingsConfig(
    client_id="client_x",
    api_key="sk_test_x",
    public_base="https://getbiblio.app",
    session_secret="unit-secret",
)


def _make(store, *, exchange=None, validate=None, validate_raises=False):
    async def _ex(code):
        return "user_42"

    async def _val(library, card, pin):
        if validate_raises:
            raise RuntimeError("bad creds")
        return None

    app = AccountSettings(
        CFG, store, exchange_code=exchange or _ex, validate_credentials=validate or _val
    )
    return TestClient(Starlette(routes=app.routes), base_url="https://testserver")


def _authenticate(tc):
    """Run login → callback so the client holds a valid session cookie."""
    r = tc.get("/account/login", follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers["location"]
    assert "/user_management/authorize" in loc
    assert "client_id=client_x" in loc
    state = parse_qs(urlparse(loc).query)["state"][0]
    r = tc.get(
        "/account/callback",
        params={"code": "abc", "state": state},
        follow_redirects=False,
    )
    assert r.status_code == 302 and r.headers["location"] == "/account"


def test_account_requires_login():
    tc = _make(InMemoryCredentialStore())
    r = tc.get("/account", follow_redirects=False)
    assert r.status_code == 302 and r.headers["location"] == "/account/login"


def test_login_redirects_to_workos_with_redirect_uri():
    tc = _make(InMemoryCredentialStore())
    r = tc.get("/account/login", follow_redirects=False)
    loc = r.headers["location"]
    assert "redirect_uri=https%3A%2F%2Fgetbiblio.app%2Faccount%2Fcallback" in loc
    assert "provider=authkit" in loc


def test_callback_bad_state_rejected():
    tc = _make(InMemoryCredentialStore())
    tc.get("/account/login", follow_redirects=False)  # sets a state cookie
    r = tc.get(
        "/account/callback",
        params={"code": "abc", "state": "not-the-state"},
        follow_redirects=False,
    )
    assert r.status_code == 400


def test_callback_then_form_renders():
    tc = _make(InMemoryCredentialStore())
    _authenticate(tc)
    r = tc.get("/account")
    assert r.status_code == 200
    assert "Connect your library card" in r.text


def test_save_validates_and_stores():
    store = InMemoryCredentialStore()
    tc = _make(store)
    _authenticate(tc)
    r = tc.post(
        "/account",
        data={
            "library": "seattle",
            "card": "12345",
            "pin": "6789",
            "default_pickup_branch": "Central",
        },
    )
    assert r.status_code == 200 and "Saved" in r.text
    creds = store.get("user_42")
    assert creds is not None
    assert creds.library == "seattle"
    assert creds.card == "12345" and creds.pin == "6789"
    assert creds.default_pickup_branch == "Central"


def test_save_rejects_bad_credentials():
    store = InMemoryCredentialStore()
    tc = _make(store, validate_raises=True)
    _authenticate(tc)
    r = tc.post("/account", data={"library": "seattle", "card": "x", "pin": "y"})
    assert r.status_code == 400
    assert store.get("user_42") is None  # nothing stored on failed validation


def test_save_requires_all_fields():
    store = InMemoryCredentialStore()
    tc = _make(store)
    _authenticate(tc)
    r = tc.post("/account", data={"library": "seattle", "card": "", "pin": ""})
    assert r.status_code == 400
    assert store.get("user_42") is None


def test_save_requires_session():
    """POST without a session cookie redirects to login, stores nothing."""
    store = InMemoryCredentialStore()
    tc = _make(store)
    r = tc.post(
        "/account",
        data={"library": "seattle", "card": "1", "pin": "2"},
        follow_redirects=False,
    )
    assert r.status_code == 302 and r.headers["location"] == "/account/login"
    assert store.get("user_42") is None


# ---- env factory ----


def test_env_disabled_without_api_key(monkeypatch):
    monkeypatch.setenv("WORKOS_CLIENT_ID", "client_x")
    monkeypatch.delenv("WORKOS_API_KEY", raising=False)
    assert web_settings_from_env() is None


def test_env_derives_public_base_from_resource(monkeypatch):
    monkeypatch.setenv("WORKOS_CLIENT_ID", "client_x")
    monkeypatch.setenv("WORKOS_API_KEY", "sk_test_x")
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_RESOURCE", "https://getbiblio.app/mcp")
    monkeypatch.delenv("BIBLIOCOMMONS_MCP_PUBLIC_URL", raising=False)
    cfg = web_settings_from_env()
    assert cfg is not None
    assert cfg.public_base == "https://getbiblio.app"
    assert cfg.redirect_uri == "https://getbiblio.app/account/callback"
    assert cfg.session_secret  # derived from api key


def test_env_missing_public_base_raises(monkeypatch):
    monkeypatch.setenv("WORKOS_CLIENT_ID", "client_x")
    monkeypatch.setenv("WORKOS_API_KEY", "sk_test_x")
    monkeypatch.delenv("BIBLIOCOMMONS_MCP_RESOURCE", raising=False)
    monkeypatch.delenv("BIBLIOCOMMONS_MCP_PUBLIC_URL", raising=False)
    with pytest.raises(WebSettingsConfigError, match="public origin"):
        web_settings_from_env()
