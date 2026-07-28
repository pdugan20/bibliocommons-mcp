"""Resolve branch names ↔ codes for any BiblioCommons library.

Branch codes are library-specific strings (e.g. LCY = Lake City, 56 =
Northtown). The mapping is fetched once from the gateway and cached in memory
for the lifetime of the process.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock

GATEWAY = "https://gateway.bibliocommons.com"


@dataclass(frozen=True)
class Branch:
    code: str
    name: str


class Branches:
    def __init__(self, library: str, http) -> None:
        self._library = library
        self._http = http
        self._by_code: dict[str, Branch] | None = None
        self._lock = RLock()

    def _load(self) -> dict[str, Branch]:
        with self._lock:
            if self._by_code is not None:
                return self._by_code
            r = self._http.get(f"{GATEWAY}/v2/libraries/{self._library}/branches")
            r.raise_for_status()
            ents = r.json().get("entities", {}).get("branches", {})
            self._by_code = {
                code: Branch(code=code, name=b.get("name") or code)
                for code, b in ents.items()
            }
            return self._by_code

    def all(self) -> list[Branch]:
        return list(self._load().values())

    def resolve(self, name_or_code: str) -> Branch:
        """Match by code (exact) or by name (case-insensitive substring)."""
        if not name_or_code:
            raise ValueError("branch name or code required")
        branches = self._load()
        # exact code match
        if name_or_code in branches:
            return branches[name_or_code]
        upper = name_or_code.upper()
        if upper in branches:
            return branches[upper]
        # name match (case-insensitive contains)
        needle = name_or_code.lower().strip()
        matches = [b for b in branches.values() if needle in b.name.lower()]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            # prefer non-locker branches when ambiguous (locker codes start with LOCK)
            non_locker = [m for m in matches if not m.code.startswith("LOCK")]
            if len(non_locker) == 1:
                return non_locker[0]
            names = ", ".join(f"{m.name} ({m.code})" for m in matches[:6])
            raise BranchNotFound(f"ambiguous branch {name_or_code!r}; matches: {names}")
        raise BranchNotFound(f"no branch matches {name_or_code!r}")


class BranchNotFound(LookupError):  # noqa: N818  follows LookupError naming
    pass
