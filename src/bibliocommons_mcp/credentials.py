"""Per-user library credentials for the multi-tenant remote transport.

In multi-user mode (WorkOS auth on), each authenticated subject maps to their
own ``{library, card, pin, ...}`` — the per-user analogue of the single-server
``Config``. Per the credential-model decision (per-session; see
docs/projects/remote-mcp-mobile.md §2), the default store is **in-memory** and
holds nothing on disk: a process restart drops it and the user re-authenticates
(rare, since BiblioCommons sessions last ~1 year while the process stays warm).
The raw PIN is never persisted to durable storage.

The ``CredentialStore`` protocol leaves room for the documented upgrade
(persisting the *encrypted session cookie* — never the PIN) without touching
call sites.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Protocol


@dataclass(frozen=True)
class UserCredentials:
    """One user's library settings — the per-user analogue of ``Config``.

    Mirrors the ``Config`` attribute surface (library/card/pin/defaults) so
    tools can treat the global config and a per-user record interchangeably
    via ``server._effective_cfg()``.
    """

    library: str
    card: str | None = None
    pin: str | None = None
    default_pickup_branch: str | None = None
    default_format: str | None = None
    digital_notification_email: str | None = None

    @property
    def has_credentials(self) -> bool:
        return bool(self.card and self.pin)


class CredentialStore(Protocol):
    """Maps an authenticated subject → their ``UserCredentials`` (or None)."""

    def get(self, subject: str) -> UserCredentials | None: ...

    def put(self, subject: str, creds: UserCredentials) -> None: ...

    def delete(self, subject: str) -> None: ...


class InMemoryCredentialStore:
    """Process-local, non-persistent store (the per-session default)."""

    def __init__(self) -> None:
        self._by_subject: dict[str, UserCredentials] = {}
        self._lock = RLock()

    def get(self, subject: str) -> UserCredentials | None:
        with self._lock:
            return self._by_subject.get(subject)

    def put(self, subject: str, creds: UserCredentials) -> None:
        with self._lock:
            self._by_subject[subject] = creds

    def delete(self, subject: str) -> None:
        with self._lock:
            self._by_subject.pop(subject, None)
