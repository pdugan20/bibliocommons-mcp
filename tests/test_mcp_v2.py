"""MCP 2026-07-28 protocol and official Apps-extension integration tests."""

from __future__ import annotations

import asyncio

from mcp import Client
from mcp.client import advertise
from mcp.server.apps import APP_MIME_TYPE, EXTENSION_ID
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from starlette.testclient import TestClient

import bibliocommons_mcp.server as server_module

mcp = server_module.mcp

EXPECTED_UI_RESOURCES = {
    "ui://bibliocommons-mcp/holds",
    "ui://bibliocommons-mcp/loans",
    "ui://bibliocommons-mcp/search",
}


def _request_meta() -> dict:
    return {
        "io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientCapabilities": {
            "extensions": {EXTENSION_ID: {"mimeTypes": [APP_MIME_TYPE]}}
        },
        "io.modelcontextprotocol/clientInfo": {
            "name": "bibliocommons-mcp-tests",
            "version": "1",
        },
    }


async def _inspect_modern_connection() -> None:
    extension = advertise(EXTENSION_ID, {"mimeTypes": [APP_MIME_TYPE]})
    async with Client(mcp, extensions=[extension]) as client:
        assert client.protocol_version == "2026-07-28"
        assert EXTENSION_ID in (client.server_capabilities.extensions or {})

        tools = await client.list_tools()
        assert tools.ttl_ms == 300_000
        assert tools.cache_scope == "public"
        by_name = {tool.name: tool for tool in tools.tools}
        assert by_name["search"].meta["ui"]["resourceUri"].endswith("/search")

        resources = await client.list_resources()
        assert resources.ttl_ms == 3_600_000
        assert resources.cache_scope == "public"
        assert {str(resource.uri) for resource in resources.resources} == (
            EXPECTED_UI_RESOURCES
        )
        for resource in resources.resources:
            assert resource.mime_type == APP_MIME_TYPE

        search_app = await client.read_resource("ui://bibliocommons-mcp/search")
        assert search_app.ttl_ms == 86_400_000
        assert search_app.cache_scope == "public"
        assert "<!doctype html>" in search_app.contents[0].text.lower()


def test_modern_client_negotiates_apps_and_cache_hints():
    asyncio.run(_inspect_modern_connection())


def test_modern_streamable_http_is_sessionless():
    app = mcp.streamable_http_app(
        host="testserver",
        stateless_http=True,
        json_response=True,
    )
    with TestClient(app) as client:
        response = client.post(
            "/mcp",
            headers={
                "MCP-Protocol-Version": "2026-07-28",
                "Mcp-Method": "server/discover",
                "Accept": "application/json",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "server/discover",
                "params": {"_meta": _request_meta()},
            },
        )

    assert response.status_code == 200
    assert "Mcp-Session-Id" not in response.headers
    result = response.json()["result"]
    assert EXTENSION_ID in result["capabilities"]["extensions"]
    assert result["ttlMs"] == 300_000
    assert result["cacheScope"] == "public"


class _FakeTokenVerifier:
    async def verify_token(self, token: str) -> AccessToken | None:
        if token != "valid-token":
            return None
        return AccessToken(
            token=token,
            client_id="test-client",
            scopes=[],
            subject="user_01TEST",
            claims={"sub": "user_01TEST"},
        )


def test_modern_http_auth_preserves_subject_context(monkeypatch):
    settings = AuthSettings(
        issuer_url="https://auth.example",
        resource_server_url="https://resource.example/mcp",
        required_scopes=[],
    )
    monkeypatch.setattr(
        server_module,
        "workos_auth_from_env",
        lambda: (_FakeTokenVerifier(), settings),
    )
    server = server_module._build_mcp(server_module.Apps())

    @server.tool()
    def current_subject() -> str:
        return server_module._current_subject() or "missing"

    app = server.streamable_http_app(
        host="testserver",
        stateless_http=True,
        json_response=True,
    )
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "current_subject",
            "arguments": {},
            "_meta": _request_meta(),
        },
    }
    base_headers = {
        "MCP-Protocol-Version": "2026-07-28",
        "Mcp-Method": "tools/call",
        "Mcp-Name": "current_subject",
        "Accept": "application/json",
    }

    with TestClient(app) as client:
        metadata = client.get("/.well-known/oauth-protected-resource/mcp")
        unauthorized = client.post("/mcp", headers=base_headers, json=body)
        authorized = client.post(
            "/mcp",
            headers={**base_headers, "Authorization": "Bearer valid-token"},
            json=body,
        )

    assert metadata.status_code == 200
    assert metadata.json()["resource"] == "https://resource.example/mcp"
    assert metadata.json()["authorization_servers"] == ["https://auth.example"]
    assert unauthorized.status_code == 401
    assert "resource_metadata=" in unauthorized.headers["WWW-Authenticate"]
    assert authorized.status_code == 200
    result = authorized.json()["result"]
    assert result["content"] == [{"type": "text", "text": "user_01TEST"}]
