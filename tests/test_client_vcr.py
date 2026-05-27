"""VCR-backed integration tests for read-only client endpoints.

Cassettes live in tests/cassettes/. They replay deterministically — no
network in CI. To re-record, run:

    BIBLIOCOMMONS_RECORD_CASSETTES=1 pytest tests/test_client_vcr.py

You need a working ~/.config/bibliocommons-mcp/config.toml to re-record.
The conftest.py fixtures strip auth cookies/tokens before write, but
always diff cassettes before committing.
"""

from __future__ import annotations

import os

import pytest


def _live_credentials_available() -> bool:
    """Re-recording needs live credentials — either env vars or the home
    config file."""
    from pathlib import Path

    if os.environ.get("BIBLIOCOMMONS_CARD") and os.environ.get("BIBLIOCOMMONS_PIN"):
        return True
    return (Path.home() / ".config/bibliocommons-mcp/config.toml").exists()


pytestmark = pytest.mark.skipif(
    os.environ.get("BIBLIOCOMMONS_RECORD_CASSETTES")
    and not _live_credentials_available(),
    reason="Re-record mode requires live credentials (env or ~/.config)",
)


def _auth_client():
    """Build a real Client. Outside of record mode, the cassette intercepts
    the network entirely — the credentials in our fixtures are stand-ins."""
    from bibliocommons_mcp.client import Client

    library = os.environ.get("BIBLIOCOMMONS_LIBRARY", "seattle")
    card = os.environ.get("BIBLIOCOMMONS_CARD", "1000000000000")
    pin = os.environ.get("BIBLIOCOMMONS_PIN", "0000")
    c = Client(library)
    c.authenticate(card, pin)
    return c


def test_list_branches_via_vcr(cassette):
    c = _auth_client()
    branches = c.branches.all()
    assert len(branches) > 10
    codes = {b.code for b in branches}
    # Seattle's Lake City is the canonical example
    assert "LCY" in codes
    # Sanity: every branch has a name
    assert all(b.name for b in branches)


def test_search_music_cd_via_vcr(cassette):
    c = _auth_client()
    data = c.search("weezer", format="MUSIC_CD", page=1)
    bibs = data.get("entities", {}).get("bibs", {})
    assert len(bibs) > 0
    # every hit should have format MUSIC_CD
    for b in bibs.values():
        assert b.get("briefInfo", {}).get("format") == "MUSIC_CD"


def test_availability_shape_via_vcr(cassette):
    c = _auth_client()
    # bib is a stable Weezer CD; if it ever leaves the catalog, the
    # cassette still replays the recorded response.
    data = c.availability("S30C2056939")
    ents = data.get("entities", {})
    assert "availabilities" in ents
    assert "bibItems" in ents
