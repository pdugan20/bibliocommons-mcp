"""Authentication compatibility tests. No live credentials or network calls."""

from __future__ import annotations

import httpx

from bibliocommons_mcp.client import Client


class _DuplicateCookieClient:
    """Reproduce the cookie lookup in bibliocommons 2026.0 after SSO."""

    def __init__(self) -> None:
        self.httpx_client = httpx.Client()

    def authenticate(self, username: str, password: str) -> None:
        assert username == "library-card"
        assert password == "library-pin"
        cookies = self.httpx_client.cookies
        for domain in ("chipublib.bibliocommons.com", ".bibliocommons.com"):
            cookies.set("bc_access_token", "test-access-token", domain=domain)
            cookies.set(
                "session_id",
                "00000000-0000-0000-0000-000000000000-41",
                domain=domain,
            )

        # This name-only access is the upstream failure: httpx cannot choose
        # between cookies with the same name on different domains.
        cookies["bc_access_token"]


def test_authenticate_recovers_duplicate_domain_cookies() -> None:
    client = Client("chipublib")
    upstream = _DuplicateCookieClient()
    client._bc = upstream

    client.authenticate("library-card", "library-pin")

    assert client.http.headers["X-Access-Token"] == "test-access-token"
    assert client.http.headers["X-Session-Id"].endswith("-41")
    assert client.account_id == 42
