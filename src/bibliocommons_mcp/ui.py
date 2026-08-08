"""MCP Apps integration helpers.

Wires the prebuilt React bundles in ``_ui_bundles.py`` into the MCP server as
UI resources following the MCP Apps extension (``io.modelcontextprotocol/ui``),
matching the wire format the shipping ``@modelcontextprotocol/ext-apps`` SDK
(v1.7) negotiates — the same one the sibling ``rewind`` server uses and that
renders in Claude Desktop and the mobile app.

Two pieces matter:

- :func:`register_ui_resource` — register one HTML bundle with the SDK's
  official :class:`~mcp.server.apps.Apps` extension. The extension advertises
  ``io.modelcontextprotocol/ui`` and serves the resource with the required
  ``text/html;profile=mcp-app`` MIME type.

- :func:`ui_tool_meta` — the ``meta`` dict to attach to a ``@mcp.tool(...)`` so
  the host renders the referenced UI resource when the tool returns; the
  result's ``structuredContent`` is delivered to the bundle.
"""

from __future__ import annotations

from typing import Any

from mcp.server.apps import APP_MIME_TYPE, EXTENSION_ID, Apps, ResourceCsp

# MCP Apps extension id (the key under `capabilities.extensions`).
UI_EXTENSION_ID = EXTENSION_ID

# Resource mime type the extension expects (the `;profile=mcp-app` suffix is
# how the host recognizes an MCP App resource, not a plain HTML resource).
UI_MIME_TYPE = APP_MIME_TYPE

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


def register_ui_resource(
    apps: Apps,
    *,
    name: str,
    title: str,
    html: str,
    description: str | None = None,
    resource_domains: list[str] | None = None,
) -> str:
    """Register a UI bundle with the official MCP Apps extension.

    The returned URI is what callers pass to :func:`ui_tool_meta` on the
    tool(s) that should render this bundle.
    """
    uri = ui_resource_uri(name)
    apps.add_html_resource(
        uri,
        html,
        name=name,
        title=title,
        description=description,
        csp=ResourceCsp(resource_domains=resource_domains or IMAGE_DOMAINS),
    )
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
