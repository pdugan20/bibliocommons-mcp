"""Tests for the public favicon + landing routes."""

from __future__ import annotations

import asyncio

import bibliocommons_mcp.server as srv


def test_favicon_404_when_missing(monkeypatch):
    monkeypatch.setattr(srv, "_static_bytes", lambda name: None)
    assert asyncio.run(srv.favicon(None)).status_code == 404


def test_favicon_served_when_present(monkeypatch):
    monkeypatch.setattr(srv, "_static_bytes", lambda name: b"\x00\x00\x01\x00ICO")
    resp = asyncio.run(srv.favicon(None))
    assert resp.status_code == 200
    assert resp.media_type == "image/x-icon"
    assert resp.body == b"\x00\x00\x01\x00ICO"


def test_favicon_svg_served(monkeypatch):
    monkeypatch.setattr(srv, "_static_bytes", lambda name: b"<svg/>")
    resp = asyncio.run(srv.favicon_svg(None))
    assert resp.status_code == 200
    assert resp.media_type == "image/svg+xml"


def test_apple_touch_icon_always_404():
    """Apple-touch icons get flattened onto an opaque background by Google's
    favicon service; we deliberately serve none so the transparent
    favicon.ico/.svg are used at every size.
    """
    assert asyncio.run(srv.apple_touch_icon(None)).status_code == 404


def test_real_assets_are_packaged():
    """The actual committed assets load via importlib.resources."""
    assert srv._static_bytes("favicon.ico")
    assert srv._static_bytes("favicon.svg")


def test_packaged_favicons_are_transparent():
    """Both favicon frames stay RGBA (no baked-in background) — an opaque
    icon is what regresses the Google favicon cache to a white/black JPEG.
    """
    ico = srv._static_bytes("favicon.ico")
    frames = [i for i in range(len(ico)) if ico.startswith(b"\x89PNG", i)]
    assert len(frames) >= 2
    for start in frames:
        # PNG IHDR colour type lives 25 bytes past the signature; 6 = RGBA.
        assert ico[start + 25] == 6
    svg = srv._static_bytes("favicon.svg").decode()
    assert 'fill="none"' in svg


def test_landing_page_links_all_icons():
    body = asyncio.run(srv.index(None)).body.decode()
    assert '<link rel="icon" href="/favicon.ico"' in body
    assert 'type="image/svg+xml" href="/favicon.svg"' in body
    assert "apple-touch-icon" not in body
    assert "/mcp" in body
