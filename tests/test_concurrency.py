"""Thread-safety checks for MCP SDK v2's synchronous handler workers."""

from __future__ import annotations

import threading
import time
import types
from concurrent.futures import ThreadPoolExecutor

from bibliocommons_mcp.branches import Branches
from bibliocommons_mcp.cache import TTLCache
from bibliocommons_mcp.client import Client


class _Response:
    status_code = 200
    text = "{}"

    def __init__(self, body: dict | None = None) -> None:
        self._body = body or {}

    def json(self) -> dict:
        return self._body

    def raise_for_status(self) -> None:
        pass


def test_ttl_cache_is_safe_under_concurrent_access():
    cache = TTLCache[int](ttl=60, maxsize=32)

    def exercise(worker: int) -> None:
        for offset in range(200):
            key = f"{worker}-{offset % 40}"
            cache.put(key, offset)
            cache.get(key)
            if offset % 7 == 0:
                cache.pop(key)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(exercise, range(8)))

    assert len(cache) <= 32


def test_branch_catalog_loads_once_across_workers():
    class SlowHttp:
        def __init__(self) -> None:
            self.calls = 0
            self.lock = threading.Lock()

        def get(self, _url: str) -> _Response:
            with self.lock:
                self.calls += 1
            time.sleep(0.01)
            return _Response({"entities": {"branches": {"LCY": {"name": "Lake City"}}}})

    http = SlowHttp()
    branches = Branches("seattle", http)
    with ThreadPoolExecutor(max_workers=8) as pool:
        resolved = list(pool.map(lambda _: branches.resolve("LCY"), range(16)))

    assert all(branch.code == "LCY" for branch in resolved)
    assert http.calls == 1


def test_gateway_session_requests_are_serialized_per_client():
    class SlowHttp:
        def __init__(self) -> None:
            self.active = 0
            self.max_active = 0
            self.lock = threading.Lock()

        def get(self, _url: str, **_kwargs) -> _Response:
            with self.lock:
                self.active += 1
                self.max_active = max(self.max_active, self.active)
            time.sleep(0.01)
            with self.lock:
                self.active -= 1
            return _Response()

    client = Client("seattle")
    http = SlowHttp()
    client._bc = types.SimpleNamespace(httpx_client=http)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda i: client.search(f"query-{i}"), range(16)))

    assert http.max_active == 1
