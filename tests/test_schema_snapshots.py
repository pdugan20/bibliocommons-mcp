"""Snapshot tests for MCP tool schemas.

Catches unintentional changes to ``inputSchema``, ``outputSchema``,
``title``, or ``annotations`` — silent edits to any of these are
tool-poisoning vectors for clients pinned against our surface.

Note that ``description`` is intentionally excluded: MCPServer applies
Python-version-dependent whitespace normalization to docstrings, so
the same source can render slightly differently across 3.11 / 3.12 /
3.14. The other fields are the load-bearing contract.

When you intentionally change a schema (rename a field, add a new tool,
tighten a validator, edit a tool title), re-run with::

    pytest --snapshot-update tests/test_schema_snapshots.py

and review the diff to ``tests/__snapshots__/test_schema_snapshots.ambr``
in your PR. Reviewers should see the schema change explicitly.
"""

from __future__ import annotations

import asyncio

from bibliocommons_mcp.server import mcp


def _tool_signature(tool) -> dict:
    """Stable per-tool representation for snapshotting.

    Description is omitted — see module docstring for the reason.
    """
    return {
        "title": tool.title,
        "inputSchema": tool.input_schema,
        "outputSchema": tool.output_schema,
        "annotations": (
            tool.annotations.model_dump(by_alias=True) if tool.annotations else None
        ),
    }


def test_tool_schemas_match_snapshot(snapshot):
    tools = asyncio.run(mcp.list_tools())
    by_name = {t.name: _tool_signature(t) for t in tools}
    assert by_name == snapshot
