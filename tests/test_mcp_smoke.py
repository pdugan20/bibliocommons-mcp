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
    "list_holds",
    "cancel_hold",
    "list_loans",
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
    assert init.serverInfo.name == "bibliocommons-mcp"
    # Instructions should be advertised to the client
    assert init.instructions
    assert "BiblioCommons" in init.instructions

    # All 9 expected tools registered
    names = {t.name for t in tools.tools}
    assert names == EXPECTED_TOOLS, f"missing or extra tools: {names ^ EXPECTED_TOOLS}"


@pytest.mark.timeout(30)
def test_every_tool_has_title_and_output_schema():
    _, tools = asyncio.run(_handshake_and_list())
    for t in tools.tools:
        assert t.title, f"tool {t.name!r} has no title"
        assert t.inputSchema, f"tool {t.name!r} has no inputSchema"
        assert t.outputSchema, f"tool {t.name!r} has no outputSchema"


@pytest.mark.timeout(30)
def test_annotations_advertise_safety_correctly():
    """Read-only tools must declare readOnlyHint; cancel_hold must declare
    destructiveHint. Clients use these to gate confirmation prompts."""
    _, tools = asyncio.run(_handshake_and_list())
    by_name = {t.name: t for t in tools.tools}

    read_only = {"search", "availability", "list_holds", "list_loans",
                 "list_branches", "library_health"}
    for name in read_only:
        ann = by_name[name].annotations
        assert ann is not None, f"{name} missing annotations"
        assert ann.readOnlyHint is True, f"{name} should be readOnlyHint=True"

    cancel = by_name["cancel_hold"].annotations
    assert cancel is not None
    assert cancel.destructiveHint is True, "cancel_hold should be destructiveHint=True"

    # Mutations are neither read-only nor destructive
    for name in ("place_hold", "borrow_digital"):
        ann = by_name[name].annotations
        assert ann is not None, f"{name} missing annotations"
        assert ann.readOnlyHint is not True, f"{name} should NOT be readOnlyHint=True"
        assert ann.destructiveHint is not True, f"{name} should NOT be destructiveHint=True"
