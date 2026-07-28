"""End-to-end smoke test: spawn the server over stdio, complete the MCP
handshake, list the tools, and verify the schemas + annotations the
client sees.

This is the closest thing we have to an integration test of the MCP
wire protocol. It catches things that schema-level unit tests miss —
missing imports at startup, broken tool registration, server crashes
during ``initialize``, etc.

The test runs as a subprocess so it exercises the real
``bibliocommons-mcp`` console-script path. Fake credentials in the env
satisfy ``Config.load()``'s fail-fast check; no real network is touched
because we never invoke a tool, only enumerate them.
"""

from __future__ import annotations

import asyncio
import sys

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

EXPECTED_TOOLS = {
    "search",
    "availability",
    "place_hold",
    "borrow_digital",
    "place_digital_hold",
    "list_holds",
    "ready_for_pickup",
    "cancel_hold",
    "list_loans",
    "renew_loan",
    "check_in_loan",
    "list_branches",
    "library_health",
}


async def _handshake_and_list():
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "bibliocommons_mcp"],
        env={
            "BIBLIOCOMMONS_LIBRARY": "seattle",
            "BIBLIOCOMMONS_CARD": "smoke-test",
            "BIBLIOCOMMONS_PIN": "smoke-test",
            "BIBLIOCOMMONS_MCP_LOG_LEVEL": "ERROR",
            # Keep PATH so the subprocess can find python
            "PATH": __import__("os").environ.get("PATH", ""),
        },
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            tools = await session.list_tools()
            return init, tools


@pytest.mark.timeout(30)
def test_server_boots_and_lists_expected_tools():
    init, tools = asyncio.run(_handshake_and_list())

    # Handshake
    # ClientSession exercises the SDK's compatibility path while the modern
    # Client tests in test_mcp_v2 negotiate 2026-07-28.
    assert init.protocol_version == "2025-11-25"
    assert init.server_info.name == "bibliocommons-mcp"
    # Instructions should be advertised to the client
    assert init.instructions
    assert "BiblioCommons" in init.instructions

    # All expected tools registered
    names = {t.name for t in tools.tools}
    assert names == EXPECTED_TOOLS, f"missing or extra tools: {names ^ EXPECTED_TOOLS}"


@pytest.mark.timeout(30)
def test_every_tool_has_title_and_output_schema():
    _, tools = asyncio.run(_handshake_and_list())
    for t in tools.tools:
        assert t.title, f"tool {t.name!r} has no title"
        assert t.input_schema, f"tool {t.name!r} has no inputSchema"
        assert t.output_schema, f"tool {t.name!r} has no outputSchema"


@pytest.mark.timeout(30)
def test_annotations_advertise_safety_correctly():
    """Read-only tools must declare readOnlyHint; cancel_hold must declare
    destructiveHint. Clients use these to gate confirmation prompts."""
    _, tools = asyncio.run(_handshake_and_list())
    by_name = {t.name: t for t in tools.tools}

    read_only = {
        "search",
        "availability",
        "list_holds",
        "ready_for_pickup",
        "list_loans",
        "list_branches",
        "library_health",
    }
    for name in read_only:
        ann = by_name[name].annotations
        assert ann is not None, f"{name} missing annotations"
        assert ann.read_only_hint is True, f"{name} should be readOnlyHint=True"

    for name in ("cancel_hold",):
        ann = by_name[name].annotations
        assert ann is not None
        assert ann.destructive_hint is True, f"{name} must be destructiveHint=True"

    # Mutations are neither read-only nor destructive
    for name in ("place_hold", "borrow_digital"):
        ann = by_name[name].annotations
        assert ann is not None, f"{name} missing annotations"
        assert ann.read_only_hint is not True, f"{name} must not be read-only"
        assert ann.destructive_hint is not True, f"{name} must not be destructive"
