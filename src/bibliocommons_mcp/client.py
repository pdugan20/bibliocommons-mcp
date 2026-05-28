"""BiblioCommons gateway client.

Wraps python-bibliocommons for the modern login flow, then layers
endpoints discovered during the spike:
  - search bibs with format facet
  - bib availability
  - place / cancel hold
  - borrow available digital item
  - list holds / loans
  - hold quota readout
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx
from bibliocommons import BiblioCommonsClient

from .branches import Branches

GATEWAY = "https://gateway.bibliocommons.com"


class BCError(RuntimeError):
    """Wraps a gateway error with status code + parsed message."""

    def __init__(self, status: int, message: str, classification: str | None = None):
        super().__init__(f"[{status}] {message}")
        self.status = status
        self.message = message
        self.classification = classification


@dataclass
class HoldQuotas:
    ils_used: int
    ils_total: int
    overdrive_used: int
    overdrive_total: int

    @property
    def ils_remaining(self) -> int:
        return max(0, self.ils_total - self.ils_used)

    @property
    def overdrive_remaining(self) -> int:
        return max(0, self.overdrive_total - self.overdrive_used)


class Client:
    """Authenticated gateway client for a single BiblioCommons library."""

    def __init__(self, library: str):
        self.library = library
        self._bc = BiblioCommonsClient(library_subdomain=library)
        self._authed = False
        self._catalog_origin = f"https://{library}.bibliocommons.com"
        self.branches = Branches(library, self._http_lazy())

    # --- internals ---

    def _http_lazy(self):
        """Httpx client proxy that calls self.http after auth (deferred)."""
        outer = self

        class _Proxy:
            def get(self, *a, **kw):
                return outer.http.get(*a, **kw)

            def post(self, *a, **kw):
                return outer.http.post(*a, **kw)

        return _Proxy()

    @property
    def http(self) -> httpx.Client:
        return self._bc.httpx_client

    def authenticate(self, card: str, pin: str) -> None:
        if self._authed:
            return
        self._bc.authenticate(username=card, password=pin)
        self._authed = True

    @property
    def account_id(self) -> int:
        if not self._authed:
            raise RuntimeError("must authenticate() first")
        return self._bc.account_id

    def _base(self) -> str:
        return f"{GATEWAY}/v2/libraries/{self.library}"

    def _post(self, path: str, body: dict, locale: str = "en-US") -> dict:
        url = f"{self._base()}{path}?locale={locale}"
        r = self.http.post(url, json=body, headers=self._post_headers())
        return self._unwrap(r)

    def _delete(self, path: str, body: dict, locale: str = "en-US") -> dict:
        url = f"{self._base()}{path}?locale={locale}"
        r = self.http.request("DELETE", url, json=body, headers=self._post_headers())
        return self._unwrap(r)

    def _patch(self, path: str, body: dict, locale: str = "en-US") -> dict:
        # PATCH on the checkouts collection does NOT need `errorMessageLocale`
        # in the body (unlike _post/_delete). Web UI doesn't send it; the
        # gateway accepts without it. Don't add it back "defensively" — BC
        # has rejected unknown fields in the past.
        url = f"{self._base()}{path}?locale={locale}"
        r = self.http.request("PATCH", url, json=body, headers=self._post_headers())
        return self._unwrap(r)

    def _get(self, path: str, params: dict | None = None) -> dict:
        url = f"{self._base()}{path}"
        r = self.http.get(url, params=params or {})
        return self._unwrap(r)

    def _post_headers(self) -> dict:
        return {
            "Origin": self._catalog_origin,
            "Referer": f"{self._catalog_origin}/",
            "Accept": "application/json",
        }

    @staticmethod
    def _unwrap(r: httpx.Response) -> dict:
        try:
            data = r.json()
        except Exception:
            data = {}
        if r.status_code >= 400:
            err = data.get("error", {}) if isinstance(data, dict) else {}
            raise BCError(
                status=r.status_code,
                message=err.get("message") or r.text[:200] or "unknown error",
                classification=err.get("classification"),
            )
        return data

    # --- public API ---

    def search(
        self,
        query: str,
        *,
        format: str | None = None,
        page: int = 1,
        sort_by: str | None = None,
        available_only: bool = False,
    ) -> dict:
        params: dict[str, Any] = {
            "query": query,
            "searchType": "keyword",
            "page": page,
        }
        if format:
            params["f_FORMAT"] = format
        if sort_by:
            params["sortBy"] = sort_by
        if available_only:
            # facet for available-now items
            params["f_NEWLY_ACQUIRED"] = (
                "AVAILABLE"  # best-guess; harmless if unsupported
            )
        return self._get("/bibs/search", params)

    def availability(self, bib_id: str) -> dict:
        return self._get(f"/bibs/{bib_id}/availability")

    def list_holds(self) -> dict:
        return self._get("/holds", {"accountId": self.account_id, "size": 100})

    def list_loans(self) -> dict:
        return self._get("/checkouts", {"accountId": self.account_id, "size": 100})

    def hold_quotas(self) -> HoldQuotas:
        data = self.list_holds()
        quotas = (
            data.get("borrowing", {})
            .get("summaries", {})
            .get("holds", {})
            .get("quotas", [])
        )
        ils_used = ils_total = od_used = od_total = 0
        for q in quotas:
            if q.get("type") == "ILS":
                ils_used = q.get("total") or 0
                ils_total = (q.get("total") or 0) + (q.get("remaining") or 0)
            elif q.get("type") == "OverDriveAPI":
                od_total = q.get("total") or 0
                od_used = od_total - (q.get("remaining") or 0)
        return HoldQuotas(
            ils_used=ils_used,
            ils_total=ils_total,
            overdrive_used=od_used,
            overdrive_total=od_total,
        )

    def place_physical_hold(self, bib_id: str, branch_code: str) -> dict:
        body = {
            "metadataId": bib_id,
            "materialType": "PHYSICAL",
            "accountId": self.account_id,
            "enableSingleClickHolds": False,
            "materialParams": {
                "branchId": branch_code,
                "expiryDate": None,
                "errorMessageLocale": "en-US",
            },
        }
        return self._post("/holds", body)

    def borrow_digital(self, bib_id: str) -> dict:
        """Check out an available digital item (immediate borrow, not a hold)."""
        body = {
            "metadataId": bib_id,
            "materialType": "DIGITAL",
            "accountId": self.account_id,
        }
        return self._post("/checkouts", body)

    def cancel_holds(self, holds: list[tuple[str, str]]) -> dict:
        """Cancel one or more holds. Each `holds` entry is (hold_id, metadata_id)."""
        if not holds:
            raise ValueError("no holds to cancel")
        body = {
            "accountId": self.account_id,
            "metadataIds": [m for _, m in holds],
            "holdIds": [h for h, _ in holds],
            "errorMessageLocale": "en-US",
        }
        return self._delete("/holds", body)

    def check_in_loan(self, checkout_id: str, metadata_id: str) -> dict:
        """Return a digital checkout early (the "check in" / "return now" button).

        Endpoint shape captured 2026-05-27: a per-resource DELETE — not the
        bulk PATCH that renew uses. Body is required even though `checkout_id`
        is in the URL; BC's ILS adapter wants the bib reference for
        auditing (same pattern as cancel_holds requiring both holdIds and
        metadataIds).

        Unlike `/holds` endpoints, this one does NOT need `errorMessageLocale`
        in the body — `_post`/`_delete` enforce that invariant for holds,
        but check-in's body shape is just `{metadataId, accountId}`. Match
        the wire exactly.

        Response is minimal: `{"id": <metadataId>}`. No new state in the
        response — caller refetches list_loans if it needs the current
        view.

        Only digital items have a `checkIn` action; physical items return
        through the ILS at the branch.
        """
        path = f"/checkouts/{checkout_id}"
        body = {
            "metadataId": metadata_id,
            "accountId": self.account_id,
        }
        # Reuse the existing `_delete` — its URL builder appends
        # ?locale=en-US, which is what we want. The body invariant
        # (errorMessageLocale being required) is enforced at the
        # _post/_delete layer for holds; for /checkouts here we
        # deliberately omit it because the captured wire didn't carry it.
        url = f"{self._base()}{path}?locale=en-US"
        r = self.http.request("DELETE", url, json=body, headers=self._post_headers())
        return self._unwrap(r)

    def renew_checkouts(self, checkout_ids: list[str]) -> dict:
        """Renew one or more checkouts in a single PATCH.

        Body shape lifted verbatim from the web UI's renew call (captured
        2026-05-27). The `renew: true` discriminator is what tells the
        gateway this PATCH is a renewal rather than e.g. a digital check-in
        (which uses `checkIn: true` on the same endpoint family).

        The response envelope mirrors `list_loans`: a `failures` array
        plus `entities.checkouts[id]` for every successfully renewed item
        with the new `dueDate` and incremented `timesRenewed`.
        """
        if not checkout_ids:
            raise ValueError("no checkouts to renew")
        body = {
            "accountId": self.account_id,
            "checkoutIds": list(checkout_ids),
            "renew": True,
        }
        return self._patch("/checkouts", body)

    def find_user_account_id(self) -> int | None:
        """Backup: scrape currentUserId from /v2/holds catalog page (user_id, not
        accountId). Kept for diagnostic purposes — python-bibliocommons's
        account_id (+1 offset) is the borrowing-side accountId we use for POSTs.
        """
        r = self.http.get(f"{self._catalog_origin}/v2/holds")
        m = re.search(r'"currentUserId":\s*(\d+)', r.text)
        return int(m.group(1)) if m else None
