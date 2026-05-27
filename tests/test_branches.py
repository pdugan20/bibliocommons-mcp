"""Unit tests for the Branches resolver. No network — uses an in-process
fake HTTP client returning canned JSON."""

from __future__ import annotations

import pytest

from bibliocommons_mcp.branches import Branches, BranchNotFound

# Realistic SPL branches subset
_FAKE_BRANCHES_JSON = {
    "entities": {
        "branches": {
            "BAL": {"code": "BAL", "name": "Ballard Branch"},
            "LOCK7": {"code": "LOCK7", "name": "Ballard Branch: SPL Lockers"},
            "BEA": {"code": "BEA", "name": "Beacon Hill Branch"},
            "CEN": {"code": "CEN", "name": "Central Library"},
            "LCY": {"code": "LCY", "name": "Lake City Branch"},
            "MGM": {"code": "MGM", "name": "Madrona-Sally Goldmark Branch"},
            "MAG": {"code": "MAG", "name": "Magnolia Branch"},
        }
    }
}


class _FakeResp:
    def __init__(self, json_data):
        self._json = json_data
        self.status_code = 200

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


class _FakeHttp:
    def __init__(self, json_data):
        self._json = json_data
        self.calls = 0

    def get(self, url, **kw):
        self.calls += 1
        return _FakeResp(self._json)


@pytest.fixture
def branches():
    return Branches("seattle", _FakeHttp(_FAKE_BRANCHES_JSON))


def test_resolve_by_exact_code(branches):
    assert branches.resolve("LCY").name == "Lake City Branch"


def test_resolve_by_lowercase_code(branches):
    # User-typed "lcy" should still work
    assert branches.resolve("lcy").code == "LCY"


def test_resolve_by_full_name(branches):
    assert branches.resolve("Lake City Branch").code == "LCY"


def test_resolve_by_partial_name_case_insensitive(branches):
    assert branches.resolve("lake city").code == "LCY"


def test_resolve_prefers_non_locker_when_ambiguous(branches):
    # "ballard" matches both Ballard Branch (BAL) + Ballard Lockers (LOCK7).
    # The non-locker variant should win.
    assert branches.resolve("Ballard").code == "BAL"


def test_resolve_raises_on_unknown(branches):
    with pytest.raises(BranchNotFound):
        branches.resolve("Hogwarts")


def test_resolve_raises_when_truly_ambiguous(branches):
    # "M" matches both MGM (Madrona) and MAG (Magnolia)
    with pytest.raises(BranchNotFound, match="ambiguous"):
        branches.resolve("M")


def test_all_returns_full_list(branches):
    all_b = branches.all()
    assert len(all_b) == 7
    codes = {b.code for b in all_b}
    assert "LCY" in codes
    assert "LOCK7" in codes


def test_lookup_is_cached(branches):
    """Subsequent resolves should reuse the cached map (no extra HTTP calls)."""
    branches.resolve("LCY")
    branches.resolve("CEN")
    branches.resolve("BAL")
    # the FakeHttp records calls — assert only one
    assert branches._http.calls == 1


def test_empty_name_raises(branches):
    with pytest.raises(ValueError):
        branches.resolve("")
