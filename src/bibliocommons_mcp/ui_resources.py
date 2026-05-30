"""Wire the prebuilt React bundles into MCP as UI resources.

Importing :func:`register_all` from ``server.py`` registers three
``ui://`` resources (holds, loans, search) using the HTML constants
emitted by ``web/scripts/inline_bundles.mjs``. The function returns a
mapping of bundle name → resource URI so the tool decorators can
attach the right URI via :func:`ui_tool_meta`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._ui_bundles import HOLDS_HTML, LOANS_HTML, SEARCH_HTML
from .ui import advertise_ui_extension, register_ui_resource

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_all(mcp: FastMCP) -> dict[str, str]:
    """Register every UI bundle and return its name → URI map."""
    # Declare the MCP Apps extension in `initialize` — without this the host
    # silently skips rendering even though tools carry `_meta.ui.resourceUri`.
    advertise_ui_extension(mcp)
    holds_uri = register_ui_resource(
        mcp,
        name="holds",
        title="Holds list card",
        description=(
            "Renders the response of `list_holds` and `ready_for_pickup` "
            "as a stack of book cards with covers, status pills, and "
            "queue positions."
        ),
        html=HOLDS_HTML,
    )
    loans_uri = register_ui_resource(
        mcp,
        name="loans",
        title="Checkouts list card",
        description=(
            "Renders the response of `list_loans` as book cards with "
            "due-date urgency pills (overdue / due soon / normal)."
        ),
        html=LOANS_HTML,
    )
    search_uri = register_ui_resource(
        mcp,
        name="search",
        title="Search results card",
        description=(
            "Renders the response of `search` as book cards with "
            "covers, formats, and the pagination summary."
        ),
        html=SEARCH_HTML,
    )
    return {"holds": holds_uri, "loans": loans_uri, "search": search_uri}
