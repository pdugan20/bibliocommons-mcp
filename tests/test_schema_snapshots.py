"""Snapshot tests for MCP tool schemas.

Catches unintentional changes to ``inputSchema``, ``outputSchema``,
``title``, ``description``, or ``annotations`` — silent edits to any of
these are tool-poisoning vectors for clients pinned against our surface.

When you intentionally change a schema (rename a field, add a new tool,
tighten a validator, edit a docstring), re-run with::

    pytest --snapshot-update tests/test_schema_snapshots.py

and review the diff to ``tests/__snapshots__/test_schema_snapshots.ambr``
in your PR. Reviewers should see the schema change explicitly.
"""

from __future__ import annotations

import asyncio
import textwrap

from bibliocommons_mcp.server import mcp


def _normalize_doc(text: str | None) -> str | None:
    """Strip leading-whitespace drift across Python versions.

    FastMCP's tool description can pick up slightly different
    indentation depending on the running Python version (3.11 vs
    3.12 vs 3.14). Normalize via ``textwrap.dedent`` + strip so the
    snapshot only diffs on intentional prose changes.
    """
    if not text:
        return text
    return textwrap.dedent(text).strip()


def _tool_signature(tool) -> dict:
    """Stable per-tool representation for snapshotting."""
    return {
        "title": tool.title,
        "description": _normalize_doc(tool.description),
        "inputSchema": tool.inputSchema,
        "outputSchema": tool.outputSchema,
        "annotations": (tool.annotations.model_dump() if tool.annotations else None),
    }


def test_tool_schemas_match_snapshot(snapshot):
    tools = asyncio.run(mcp.list_tools())
    by_name = {t.name: _tool_signature(t) for t in tools}
    assert by_name == snapshot
