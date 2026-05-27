"""MCP Apps integration helpers.

This module wires the prebuilt React bundles in ``_ui_bundles.py`` into
the MCP server as UI resources following the MCP Apps extension
(``io.modelcontextprotocol/ui``, spec rev 2026-01-26 — currently
Draft).

Two functions matter for the rest of the codebase:

- :func:`register_ui_resource` — register one HTML bundle as a
  ``ui://`` MCP resource, attaching a Content-Security-Policy in the
  resource's ``_meta`` so the host iframe will load Syndetics jacket
  images.

- :func:`ui_tool_meta` — return the ``meta`` dict to attach to a
  ``@mcp.tool(...)`` so the host knows which UI resource to render
  when the tool returns. The result's ``structuredContent`` is what
  the bundle receives via ``ui/notifications/tool-result``.

The spec is still Draft, so the meta keys are versioned per the
``protocolVersion`` constant below. If the spec lands under a
different namespace, this is the single file to edit.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp.resources import FunctionResource
from pydantic import AnyUrl

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

# MCP Apps extension namespace. Both resources and tools annotate
# under this key so hosts can discover and bind them.
UI_META_KEY = "io.modelcontextprotocol/ui"

# Spec revision we target. Matches the version the
# `@modelcontextprotocol/ext-apps` JS SDK negotiates against in
# `web/package.json`.
UI_PROTOCOL_VERSION = "2026-01-26"

# Default CSP for our bundles. Bundles are entirely self-contained
# HTML (Vite + vite-plugin-singlefile inlines every script/style), so
# `'self'` plus inline + the two image hosts that serve our jackets
# is sufficient. `data:` covers the 1×1 transparent placeholders the
# components fall back to when a jacket is missing.
#
# Syndetics is BiblioCommons's third-party jacket provider; its URLs
# come back in the gateway's `briefInfo.jacket` field. The CDN host
# serves BC's own fallback covers.
DEFAULT_IMG_SRC = (
    "'self' data: https://secure.syndetics.com https://*.syndetics.com "
    "https://cor-cdn-static.bibliocommons.com"
)
DEFAULT_STYLE_SRC = "'self' 'unsafe-inline'"
DEFAULT_SCRIPT_SRC = "'self' 'unsafe-inline'"


def ui_resource_uri(name: str) -> str:
    """Stable URI for a UI bundle resource.

    Used by both the resource registration and the tools that
    reference it. Keeping it in one place means tools and resources
    can't drift.
    """
    return f"ui://bibliocommons-mcp/{name}"


def register_ui_resource(
    mcp: FastMCP,
    *,
    name: str,
    title: str,
    html: str,
    description: str | None = None,
    img_src: str = DEFAULT_IMG_SRC,
    style_src: str = DEFAULT_STYLE_SRC,
    script_src: str = DEFAULT_SCRIPT_SRC,
) -> str:
    """Register a UI bundle as an MCP resource and return its URI.

    The returned URI is what callers pass to :func:`ui_tool_meta` on
    the tool(s) that should render this bundle.
    """
    uri = ui_resource_uri(name)
    # Build the CSP string from the per-bundle directive args. Bundles
    # vary in what they fetch (search renders more jackets than a
    # zero-state holds card), so we let each caller widen the policy
    # if needed.
    csp = "; ".join(
        [
            "default-src 'none'",
            f"img-src {img_src}",
            f"style-src {style_src}",
            f"script-src {script_src}",
            "connect-src 'none'",
            "frame-src 'none'",
        ]
    )
    meta: dict[str, Any] = {
        UI_META_KEY: {
            "version": UI_PROTOCOL_VERSION,
            "csp": csp,
        }
    }
    resource = FunctionResource(
        uri=AnyUrl(uri),
        name=name,
        title=title,
        description=description,
        mime_type="text/html",
        # FunctionResource calls `fn()` on read. The bundles are large
        # (~500KB each) but already in memory, so the callable just
        # hands them back. Lazy is fine; the SDK won't read until a
        # client asks for it.
        fn=lambda html=html: html,
        meta=meta,
    )
    mcp.add_resource(resource)
    return uri


def ui_tool_meta(resource_uri: str) -> dict[str, Any]:
    """Return the ``meta=`` dict for a tool that should render UI.

    Pass to ``@mcp.tool(..., meta=ui_tool_meta(...))``. The host reads
    this and, when the tool returns, loads the referenced UI resource
    and posts the tool's ``structuredContent`` into it via
    ``ui/notifications/tool-result``.
    """
    return {
        UI_META_KEY: {
            "version": UI_PROTOCOL_VERSION,
            "resourceUri": resource_uri,
        }
    }
