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


def test_apple_touch_icon_served(monkeypatch):
    monkeypatch.setattr(srv, "_static_bytes", lambda name: b"\x89PNG")
    resp = asyncio.run(srv.apple_touch_icon(None))
    assert resp.status_code == 200
    assert resp.media_type == "image/png"


def test_real_assets_are_packaged():
    """The actual committed assets load via importlib.resources."""
    assert srv._static_bytes("favicon.ico")
    assert srv._static_bytes("favicon.svg")
    assert srv._static_bytes("apple-touch-icon.png")


def test_landing_page_links_all_icons():
    body = asyncio.run(srv.index(None)).body.decode()
    assert '<link rel="icon" href="/favicon.ico"' in body
    assert 'type="image/svg+xml" href="/favicon.svg"' in body
    assert 'rel="apple-touch-icon" href="/apple-touch-icon.png"' in body
    assert "/mcp" in body
