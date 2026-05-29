"""Tests for the public /favicon.ico and / landing routes."""

from __future__ import annotations

import asyncio

import bibliocommons_mcp.server as srv


def test_favicon_404_when_missing(monkeypatch):
    monkeypatch.setattr(srv, "_favicon_bytes", lambda: None)
    resp = asyncio.run(srv.favicon(None))
    assert resp.status_code == 404


def test_favicon_served_when_present(monkeypatch):
    monkeypatch.setattr(srv, "_favicon_bytes", lambda: b"\x00\x00\x01\x00ICONDATA")
    resp = asyncio.run(srv.favicon(None))
    assert resp.status_code == 200
    assert resp.media_type == "image/x-icon"
    assert resp.body == b"\x00\x00\x01\x00ICONDATA"


def test_landing_page_links_favicon():
    resp = asyncio.run(srv.index(None))
    assert resp.status_code == 200
    body = resp.body.decode()
    assert '<link rel="icon" href="/favicon.ico"' in body
    assert "/mcp" in body
