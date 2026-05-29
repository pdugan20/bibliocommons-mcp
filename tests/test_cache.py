"""Unit tests for the TTL + LRU cache (per-user client cache backing store)."""

from __future__ import annotations

import pytest

from bibliocommons_mcp.cache import TTLCache


class _Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


def test_get_returns_put_value():
    c = TTLCache(ttl=10, maxsize=5)
    c.put("a", 1)
    assert c.get("a") == 1
    assert c.get("missing") is None


def test_entry_expires_after_idle_ttl():
    clock = _Clock()
    c = TTLCache(ttl=10, maxsize=5, clock=clock)
    c.put("a", 1)
    clock.advance(11)
    assert c.get("a") is None
    assert len(c) == 0  # expired entry dropped on access


def test_access_refreshes_idle_timer():
    clock = _Clock()
    c = TTLCache(ttl=10, maxsize=5, clock=clock)
    c.put("a", 1)
    clock.advance(6)
    assert c.get("a") == 1  # within TTL, refreshes last-used
    clock.advance(6)  # 12s since put, but only 6s since last access
    assert c.get("a") == 1


def test_lru_eviction_when_over_capacity():
    c = TTLCache(ttl=1000, maxsize=2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")  # make "a" most-recently-used so "b" is the LRU
    c.put("c", 3)  # over cap -> evict LRU ("b")
    assert c.get("a") == 1
    assert c.get("c") == 3
    assert c.get("b") is None


def test_put_evicts_expired():
    clock = _Clock()
    c = TTLCache(ttl=10, maxsize=5, clock=clock)
    c.put("a", 1)
    clock.advance(11)
    c.put("b", 2)  # triggers expired sweep
    assert c.get("a") is None
    assert c.get("b") == 2


def test_pop_and_clear():
    c = TTLCache(ttl=10, maxsize=5)
    c.put("a", 1)
    c.pop("a")
    assert c.get("a") is None
    c.put("b", 2)
    c.clear()
    assert len(c) == 0


def test_rejects_nonpositive_bounds():
    with pytest.raises(ValueError):
        TTLCache(ttl=0, maxsize=5)
    with pytest.raises(ValueError):
        TTLCache(ttl=10, maxsize=0)
