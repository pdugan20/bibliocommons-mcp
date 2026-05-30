"""MCP Apps integration helpers.

Wires the prebuilt React bundles in ``_ui_bundles.py`` into the MCP server as
UI resources following the MCP Apps extension (``io.modelcontextprotocol/ui``),
matching the wire format the shipping ``@modelcontextprotocol/ext-apps`` SDK
(v1.7) negotiates — the same one the sibling ``rewind`` server uses and that
renders in Claude Desktop and the mobile app.

Three pieces matter:

- :func:`advertise_ui_extension` — declare the ``io.modelcontextprotocol/ui``
  extension in the server's ``initialize`` capabilities. **Load-bearing:**
  without it the host sees a tool's ``_meta.ui.resourceUri`` but silently skips
  rendering, because capability negotiation failed.

- :func:`register_ui_resource` — register one HTML bundle as a ``ui://``
  resource with mime ``text/html;profile=mcp-app`` and a per-bundle CSP under
  ``_meta.ui.csp`` so the host iframe loads Syndetics jacket images.

- :func:`ui_tool_meta` — the ``meta`` dict to attach to a ``@mcp.tool(...)`` so
  the host renders the referenced UI resource when the tool returns; the
  result's ``structuredContent`` is delivered to the bundle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp.resources import FunctionResource
from pydantic import AnyUrl

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

# MCP Apps extension id (the key under `capabilities.extensions`).
UI_EXTENSION_ID = "io.modelcontextprotocol/ui"

# Resource mime type the extension expects (the `;profile=mcp-app` suffix is
# how the host recognizes an MCP App resource, not a plain HTML resource).
UI_MIME_TYPE = "text/html;profile=mcp-app"

# Per-bundle `_meta`/`meta` use the short `ui` key (+ a legacy `ui/resourceUri`
# fallback), matching ext-apps 1.7 / rewind — NOT the full extension-id key.

# Image hosts our bundles load jacket art from. The host iframe enforces these
# as the resource's CSP `resourceDomains` and silently drops any cover whose
# host isn't listed — so every jacket provider a library can return must be here:
#   - Syndetics: BiblioCommons's primary jacket provider (physical items).
#   - cor-cdn-static.bibliocommons.com: BC's own fallback covers.
#   - *.od-cdn.com: OverDrive's CDN — where Libby/digital (eBook, eAudiobook)
#     covers come from; sharded across img1/img2/… hosts.
IMAGE_DOMAINS = [
    "https://secure.syndetics.com",
    "https://*.syndetics.com",
    "https://cor-cdn-static.bibliocommons.com",
    "https://*.od-cdn.com",
]


def ui_resource_uri(name: str) -> str:
    """Stable URI for a UI bundle resource — shared by the resource
    registration and the tools that reference it, so they can't drift."""
    return f"ui://bibliocommons-mcp/{name}"


def advertise_ui_extension(mcp: FastMCP) -> None:
    """Advertise the MCP Apps UI extension in the ``initialize`` response.

    The installed Python SDK's ``ServerCapabilities`` has no typed
    ``extensions`` field (only ``experimental``), but the model allows extra
    keys — so we inject ``extensions`` by wrapping the low-level server's
    ``create_initialization_options`` (used by both the stdio and Streamable
    HTTP transports). Idempotent.
    """
    server = mcp._mcp_server
    if getattr(server, "_ui_extension_advertised", False):
        return
    original = server.create_initialization_options

    def _with_ui_extension(*args: Any, **kwargs: Any):
        opts = original(*args, **kwargs)
        caps = opts.capabilities
        extensions = dict(getattr(caps, "extensions", None) or {})
        extensions[UI_EXTENSION_ID] = {"mimeTypes": [UI_MIME_TYPE]}
        new_caps = caps.model_copy(update={"extensions": extensions})
        return opts.model_copy(update={"capabilities": new_caps})

    server.create_initialization_options = _with_ui_extension
    server._ui_extension_advertised = True


def register_ui_resource(
    mcp: FastMCP,
    *,
    name: str,
    title: str,
    html: str,
    description: str | None = None,
    resource_domains: list[str] | None = None,
) -> str:
    """Register a UI bundle as an MCP App resource and return its URI.

    The returned URI is what callers pass to :func:`ui_tool_meta` on the
    tool(s) that should render this bundle.
    """
    uri = ui_resource_uri(name)
    meta: dict[str, Any] = {
        "ui": {"csp": {"resourceDomains": resource_domains or IMAGE_DOMAINS}}
    }
    resource = FunctionResource(
        uri=AnyUrl(uri),
        name=name,
        title=title,
        description=description,
        mime_type=UI_MIME_TYPE,
        # Bundles are large (~500KB) but already in memory; hand them back on
        # read. The SDK won't read until a client asks.
        fn=lambda html=html: html,
        meta=meta,
    )
    mcp.add_resource(resource)
    return uri


def ui_tool_meta(resource_uri: str) -> dict[str, Any]:
    """Return the ``meta=`` dict for a tool that should render UI.

    Pass to ``@mcp.tool(..., meta=ui_tool_meta(...))``. The host reads
    ``_meta.ui.resourceUri`` (with the legacy ``ui/resourceUri`` fallback),
    loads the referenced UI resource when the tool returns, and posts the
    tool's ``structuredContent`` into it.
    """
    return {
        "ui": {"resourceUri": resource_uri},
        "ui/resourceUri": resource_uri,
    }
