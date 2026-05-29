"""A tiny in-memory cache with idle-TTL expiry + LRU size cap.

Used for the per-user authenticated-client cache (server.py). Both bounds
matter for a long-lived multi-tenant process: the TTL refreshes a user's
BiblioCommons session periodically and lets idle users fall out, and the size
cap stops unbounded growth. Eviction is cheap — a dropped entry just means the
next request re-authenticates from the still-stored credentials, so the user
is never re-prompted (that only happens on a full process restart, per the
per-session model in docs/projects/remote-mcp-mobile.md §2).

The clock is injectable so tests don't sleep.
"""

from __future__ import annotations

import time as _time
from collections import OrderedDict
from collections.abc import Callable
from typing import Generic, TypeVar

V = TypeVar("V")


class TTLCache(Generic[V]):
    def __init__(
        self,
        *,
        ttl: float,
        maxsize: int,
        clock: Callable[[], float] = _time.monotonic,
    ) -> None:
        if ttl <= 0 or maxsize <= 0:
            raise ValueError("ttl and maxsize must be positive")
        self._ttl = ttl
        self._maxsize = maxsize
        self._clock = clock
        # key -> (last_used, value); ordered by recency (LRU at the front).
        self._data: OrderedDict[str, tuple[float, V]] = OrderedDict()

    def get(self, key: str) -> V | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        last_used, value = entry
        now = self._clock()
        if now - last_used > self._ttl:
            del self._data[key]
            return None
        # Refresh recency + idle timer on access.
        self._data[key] = (now, value)
        self._data.move_to_end(key)
        return value

    def put(self, key: str, value: V) -> None:
        now = self._clock()
        self._data[key] = (now, value)
        self._data.move_to_end(key)
        self._evict_expired(now)
        while len(self._data) > self._maxsize:
            self._data.popitem(last=False)  # drop least-recently-used

    def pop(self, key: str) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()

    def _evict_expired(self, now: float) -> None:
        expired = [k for k, (ts, _) in self._data.items() if now - ts > self._ttl]
        for k in expired:
            del self._data[k]

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None
