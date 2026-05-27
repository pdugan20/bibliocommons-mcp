"""FastMCP server for bibliocommons-mcp.

Single library per server, configured via
``~/.config/bibliocommons-mcp/config.toml``. See ``docs/architecture.md``
for the gateway client's design and the painful endpoint-shape
discoveries it encodes.
"""

from __future__ import annotations

import functools
import logging
import os
import sys
import time
from typing import TYPE_CHECKING

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from .branches import BranchNotFound
from .client import BCError, Client
from .config import Config, ConfigError
from .models import (
    Availability,
    AvailabilityCopy,
    BibSummary,
    BorrowDigitalResult,
    BranchList,
    BulkCancelHoldsResult,
    BulkPlaceHoldResult,
    BulkRenewLoansResult,
    CancelHoldResult,
    DigitalFormat,
    Hold,
    HoldList,
    HoldRef,
    Jacket,
    LibraryHealth,
    Loan,
    LoanList,
    PlaceHoldResult,
    RenewLoanResult,
    SearchResult,
)
from .models import Branch as BranchModel

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


# ─────────────────────────────── server instructions ───────────────────────────────

INSTRUCTIONS = """
bibliocommons-mcp connects to one BiblioCommons-powered public library
(Seattle, SFPL, etc.) and exposes catalog search, holds, and account
management as MCP tools.

Common workflows:

- "find a CD and place a hold" — `search` (with `format="MUSIC_CD"`),
  pick a result, optionally `availability` to confirm a copy at the
  user's branch, then `place_hold`. The user's default pickup branch
  comes from config; respect their choice unless they specify another.
- "what am I waiting on" — `list_holds`. Position 1 means front of the
  queue; higher numbers mean farther back.
- "what's due back" — `list_loans`.
- "cancel a hold" — `list_holds` first to get the hold id, then
  `cancel_hold(hold_id, bib_id)`. **Irreversible** — losing queue
  position can't be recovered. Confirm before calling.
- "is the catalog working" — `library_health` is the right first call
  when something seems off.

Important constraints:

- One library per server instance; the configured subdomain is fixed
  at startup.
- `place_hold` requires a physical bib (CD, book, DVD, ...). For
  available digital items, use `borrow_digital` (immediate borrow).
- Joining a Libby waitlist for an unavailable digital item is not
  supported; tell the user to use Libby directly.
- Format codes are BiblioCommons facets like `MUSIC_CD`, `BK`,
  `EBOOK`, `EAUDIOBOOK`, `AUDIOBOOK_CD`, `DVD`.
- Branch IDs are 3-letter codes (e.g. `LCY` = Lake City). `place_hold`
  accepts names or codes; the resolver matches case-insensitive
  substrings and prefers regular branches over locker variants.
"""


# ─────────────────────── tool annotation presets ───────────────────────

# Reads from the catalog or the user's own account. Safe to call freely;
# clients should not require confirmation. `openWorldHint=True` because
# the underlying data (catalog, account state) changes over time.
READ_ONLY = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=True)

# Creates new account-side state (a hold, a checkout). Not idempotent —
# calling twice with the same args may 409 ("already on holds list") or
# create a second entry. Not destructive: place_hold can be cancelled,
# borrow_digital can be returned.
MUTATION = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=True,
)

# Removes existing account-side state in a way the user can't trivially
# reverse — cancelling a hold loses queue position. Clients should
# surface a confirmation prompt before calling.
DESTRUCTIVE = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=True,
)


# ─────────────────────────────── runtime ───────────────────────────────


mcp = FastMCP("bibliocommons-mcp", instructions=INSTRUCTIONS.strip())

# Register the prebuilt React bundles as MCP Apps UI resources. The
# mapping is used below by tools that want to render a card; passing
# `meta=ui_tool_meta(UI_RESOURCES[name])` to `@mcp.tool` tells a
# UI-capable host (Claude Desktop, Inspector) which bundle to mount.
from . import ui_resources  # noqa: E402  (import after FastMCP init)
from .ui import ui_tool_meta  # noqa: E402

UI_RESOURCES = ui_resources.register_all(mcp)

_cfg: Config | None = None
_client: Client | None = None


def _ensure_client() -> Client:
    """Lazy-init client. Called by every tool to avoid logging in until needed."""
    global _cfg, _client
    if _client is None:
        _cfg = Config.load()
        _client = Client(_cfg.library)
        _client.authenticate(_cfg.card, _cfg.pin)
    return _client


def _resolve_branch(name_or_code: str | None) -> str:
    """Resolve a branch name/code to a code, falling back to the config default."""
    client = _ensure_client()
    target = name_or_code or (_cfg.default_pickup_branch if _cfg else None)
    if not target:
        raise ToolError(
            "pickup_branch is required (or set default_pickup_branch in config)"
        )
    return client.branches.resolve(target).code


def _safe(fn: Callable) -> Callable:
    """Wrap a tool so known exceptions surface as ToolError with a clean message.

    BCError (gateway errors), BranchNotFound (resolver), and ValueError
    (caller mistakes) become ToolError. Anything else propagates and
    FastMCP renders the class + message.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (BCError, BranchNotFound, ValueError) as e:
            raise ToolError(str(e)) from e

    return wrapper


def _extract_jacket(brief_info: dict) -> Jacket | None:
    """Pull jacket cover-art URLs from a briefInfo dict.

    `briefInfo.jacket` is structured with `small`/`medium`/`large`/`local_url`
    keys plus a `type` field we ignore. Returns None if no jacket data.
    """
    raw = brief_info.get("jacket") if isinstance(brief_info, dict) else None
    if not raw or not isinstance(raw, dict):
        return None
    return Jacket(
        small=raw.get("small"),
        medium=raw.get("medium"),
        large=raw.get("large"),
        local_url=raw.get("local_url"),
    )


def _bib_summary(bib: dict) -> BibSummary:
    bi = bib.get("briefInfo", {})
    return BibSummary(
        bib_id=bib.get("id") or bi.get("metadataId") or "",
        title=bi.get("title"),
        subtitle=bi.get("subtitle"),
        authors=list(bi.get("authors") or []),
        format=bi.get("format"),
        year=bi.get("publicationDate"),
        call_number=bi.get("callNumber"),
        jacket=_extract_jacket(bi),
    )


def _loan_from_entity(checkout_id: str, c: dict, data: dict) -> Loan:
    """Project a `entities.checkouts[id]` dict into a `Loan` model."""
    branch_obj = c.get("branch") or {}
    return Loan(
        checkout_id=checkout_id,
        metadata_id=c.get("metadataId"),
        title=c.get("bibTitle") or c.get("title"),
        material_type=c.get("materialType"),
        due=c.get("dueDate"),
        call_number=c.get("callNumber"),
        branch=branch_obj.get("code") if branch_obj else None,
        jacket=_jacket_for(data, c.get("metadataId")),
        actions=list(c.get("actions") or []),
        times_renewed=c.get("timesRenewed") or 0,
    )


def _jacket_for(data: dict, metadata_id: str | None) -> Jacket | None:
    """Look up jacket via `entities.bibs[metadata_id].briefInfo.jacket`."""
    if not metadata_id:
        return None
    bib = data.get("entities", {}).get("bibs", {}).get(metadata_id)
    if not bib:
        return None
    return _extract_jacket(bib.get("briefInfo", {}))


# ─────────────────────────────── tools ───────────────────────────────


@mcp.tool(
    title="Search the catalog",
    annotations=READ_ONLY,
    meta=ui_tool_meta(UI_RESOURCES["search"]),
)
@_safe
def search(
    query: str,
    format: str | None = None,
    page: int = 1,
    sort_by: str | None = None,
) -> SearchResult:
    """Search the catalog by keyword, optionally filtered by format.

    Args:
        query: Keyword search string.
        format: Format facet (e.g. `MUSIC_CD`, `BK`, `EBOOK`, `EAUDIOBOOK`,
            `AUDIOBOOK_CD`, `DVD`). Omit for any format. Defaults to
            `default_format` from config if set.
        page: 1-indexed page number. The gateway returns up to 25
            results per page; use the `pages` field in the response to
            page further.
        sort_by: Optional sort key. One of `relevancy`, `newly_acquired`,
            `title`, `author`, `published_date`, `ugc_rating`.
    """
    client = _ensure_client()
    fmt = format or (_cfg.default_format if _cfg else None)
    data = client.search(query, format=fmt, page=page, sort_by=sort_by)
    bibs = data.get("entities", {}).get("bibs", {})
    pag = data.get("catalogSearch", {}).get("pagination", {})
    return SearchResult(
        page=pag.get("page"),
        pages=pag.get("pages"),
        total=pag.get("count"),
        results=[_bib_summary(bibs[bid]) for bid in bibs],
    )


@mcp.tool(title="Show per-branch availability", annotations=READ_ONLY)
@_safe
def availability(bib_id: str) -> Availability:
    """Show per-branch copy status for a bib.

    Args:
        bib_id: The bib id (e.g. `S30C3857930`). Get one from
            `search` results.
    """
    client = _ensure_client()
    data = client.availability(bib_id)
    summary = data.get("entities", {}).get("availabilities", {}).get(bib_id, {})
    items = data.get("entities", {}).get("bibItems", {})
    raw_formats = data.get("availability", {}).get("digitalFormats") or []
    return Availability(
        bib_id=bib_id,
        total_copies=summary.get("totalCopies"),
        available_copies=summary.get("availableCopies"),
        held_copies=summary.get("heldCopies"),
        status=summary.get("status"),
        digital_formats=[
            DigitalFormat(
                name=df.get("name", ""),
                has_download_link=df.get("hasDownloadLink"),
                must_be_read_online=df.get("mustBeReadOnline"),
            )
            for df in raw_formats
        ],
        copies=[
            AvailabilityCopy(
                branch_code=it.get("branch", {}).get("code"),
                branch_name=it.get("branch", {}).get("name"),
                status=it.get("availability", {}).get("status"),
                library_status=it.get("availability", {}).get("libraryStatus"),
                call_number=it.get("callNumber"),
                collection=it.get("collection"),
            )
            for it in items.values()
        ],
    )


def _place_hold_one(client: Client, bib_id: str, branch_code: str) -> PlaceHoldResult:
    """Place a single physical hold; shared by `place_hold` and `place_holds`."""
    data = client.place_physical_hold(bib_id, branch_code)
    holds = data.get("entities", {}).get("holds", {})
    if not holds:
        return PlaceHoldResult(success=False)
    hold_id = next(iter(holds))
    hold = holds[hold_id]
    return PlaceHoldResult(
        success=True,
        hold_id=hold_id,
        title=hold.get("bibTitle"),
        material_type=hold.get("materialType"),
        pickup_branch=(hold.get("pickupLocation") or {}).get("code"),
        position=hold.get("holdsPosition"),
        status=hold.get("status"),
        expiry=hold.get("expiryDate"),
    )


@mcp.tool(title="Place a physical hold", annotations=MUTATION)
@_safe
def place_hold(bib_id: str, pickup_branch: str | None = None) -> PlaceHoldResult:
    """Place a physical hold on a bib (CD, book, DVD, etc.).

    For multiple bibs, prefer `place_holds` — it batches with a built-in
    inter-call delay to avoid gateway rate-limiting.

    Args:
        bib_id: The bib id (e.g. `S30C3857930`).
        pickup_branch: Branch name or 3-letter code (e.g. `Lake City`
            or `LCY`). Defaults to `default_pickup_branch` from config.
            Names are matched case-insensitively; locker variants are
            de-prioritized when the query is ambiguous.
    """
    client = _ensure_client()
    branch_code = _resolve_branch(pickup_branch)
    return _place_hold_one(client, bib_id, branch_code)


@mcp.tool(title="Place holds on multiple bibs", annotations=MUTATION)
@_safe
def place_holds(
    bib_ids: list[str],
    pickup_branch: str | None = None,
    delay_seconds: float = 1.0,
) -> BulkPlaceHoldResult:
    """Place physical holds on several bibs at the same pickup branch.

    The gateway has no batch endpoint for placement, so this is N
    sequential POSTs. A short delay between each (default 1s) keeps
    the BC gateway from rate-limiting after several rapid requests.

    Per-bib failures don't stop the run — placement continues and the
    result splits successes (`placed`) and failures (`failures`) so the
    agent can report partial completion. Common failure causes: the
    user already has the item on hold (409), the item isn't holdable
    (reference-only), or a transient gateway 5xx.

    Args:
        bib_ids: List of bib IDs. Order is preserved during placement
            (first attempted first).
        pickup_branch: Branch name or 3-letter code applied to every
            hold. Defaults to `default_pickup_branch` from config.
        delay_seconds: Pause between each gateway call. The default of
            1s is conservative; lower for small batches if you're
            willing to risk a transient 429.
    """
    if not bib_ids:
        raise ToolError("bib_ids list is empty — nothing to place")

    client = _ensure_client()
    branch_code = _resolve_branch(pickup_branch)

    placed: dict[str, PlaceHoldResult] = {}
    failures: dict[str, str] = {}

    for i, bib_id in enumerate(bib_ids):
        if i > 0 and delay_seconds > 0:
            time.sleep(delay_seconds)
        try:
            placed[bib_id] = _place_hold_one(client, bib_id, branch_code)
        except BCError as e:
            failures[bib_id] = e.message

    return BulkPlaceHoldResult(placed=placed, failures=failures)


@mcp.tool(title="Borrow an available digital item", annotations=MUTATION)
@_safe
def borrow_digital(bib_id: str) -> BorrowDigitalResult:
    """Check out an immediately-available digital item.

    Use this when an ebook or e-audiobook is "Available Now" rather
    than queued. For unavailable digital items (Libby waitlist),
    direct the user to the Libby app — joining waitlists is not
    supported here yet.

    Args:
        bib_id: The bib id of the digital item.
    """
    client = _ensure_client()
    data = client.borrow_digital(bib_id)
    checkouts = data.get("entities", {}).get("checkouts", {})
    if not checkouts:
        return BorrowDigitalResult(success=False)
    cid = next(iter(checkouts))
    co = checkouts[cid]
    return BorrowDigitalResult(
        success=True,
        checkout_id=cid,
        title=co.get("bibTitle") or co.get("title"),
        material_type=co.get("materialType"),
        due=co.get("dueDate"),
        call_number=co.get("callNumber"),
        volume=co.get("volume"),
    )


def _holds_from_response(data: dict) -> list[Hold]:
    """Build a list of Hold models from a raw gateway holds response.

    Joins `entities.holds` with `entities.bibs[metadataId]` to populate
    jacket cover-art alongside each hold.
    """
    holds_ents = data.get("entities", {}).get("holds", {})
    return [
        Hold(
            hold_id=hid,
            metadata_id=h.get("metadataId"),
            title=h.get("bibTitle"),
            material_type=h.get("materialType"),
            status=h.get("status"),
            position=h.get("holdsPosition"),
            pickup_branch=(h.get("pickupLocation") or {}).get("code"),
            placed=h.get("holdPlacedDate"),
            expiry=h.get("expiryDate"),
            jacket=_jacket_for(data, h.get("metadataId")),
        )
        for hid, h in holds_ents.items()
    ]


@mcp.tool(
    title="List your holds",
    annotations=READ_ONLY,
    meta=ui_tool_meta(UI_RESOURCES["holds"]),
)
@_safe
def list_holds() -> HoldList:
    """Show current holds (physical + digital) with queue positions."""
    client = _ensure_client()
    data = client.list_holds()
    out = _holds_from_response(data)
    return HoldList(count=len(out), holds=out)


@mcp.tool(
    title="Show holds ready for pickup",
    annotations=READ_ONLY,
    meta=ui_tool_meta(UI_RESOURCES["holds"]),
)
@_safe
def ready_for_pickup() -> HoldList:
    """Show only the holds that have arrived at the user's pickup branch.

    Filters `list_holds` to `status == "READY_FOR_PICKUP"`. The same
    fields as `list_holds`; use this when the user asks "what's waiting
    for me at the library" so the model doesn't have to filter
    client-side.
    """
    client = _ensure_client()
    data = client.list_holds()
    all_holds = _holds_from_response(data)
    ready = [h for h in all_holds if h.status == "READY_FOR_PICKUP"]
    return HoldList(count=len(ready), holds=ready)


@mcp.tool(title="Cancel a hold", annotations=DESTRUCTIVE)
@_safe
def cancel_hold(hold_id: str, bib_id: str, dry_run: bool = False) -> CancelHoldResult:
    """Cancel a hold by id.

    **Irreversible** — cancelling loses your queue position. Confirm
    with the user first.

    For multiple holds, prefer `cancel_holds` — it's one round-trip
    instead of N.

    Args:
        hold_id: From `list_holds().holds[i].hold_id`.
        bib_id: From the same row's `metadata_id`. Both are required by
            the gateway.
        dry_run: If true, look up the hold and describe what would be
            cancelled without actually cancelling it. Useful as an
            agent self-check before calling with `dry_run=False`.
    """
    client = _ensure_client()
    if dry_run:
        data = client.list_holds()
        hold = data.get("entities", {}).get("holds", {}).get(hold_id)
        if not hold:
            return CancelHoldResult(
                success=False,
                dry_run=True,
                failures={hold_id: "hold not found on this account"},
            )
        title = hold.get("bibTitle") or "(unknown title)"
        position = hold.get("holdsPosition")
        pos_str = f" at queue position {position}" if position else ""
        return CancelHoldResult(
            success=True,
            dry_run=True,
            would_cancel=f"{title!r}{pos_str}",
        )
    data = client.cancel_holds([(hold_id, bib_id)])
    failures = data.get("failures") or {}
    return CancelHoldResult(success=not failures, failures=failures)


@mcp.tool(title="Cancel multiple holds in one call", annotations=DESTRUCTIVE)
@_safe
def cancel_holds(holds: list[HoldRef], dry_run: bool = False) -> BulkCancelHoldsResult:
    """Cancel one or more holds in a single gateway call.

    **Irreversible** for each cancelled hold (lost queue position).
    Confirm with the user before calling with `dry_run=False`.

    Prefer this over multiple `cancel_hold` calls when the user has a
    list — it's one HTTP round-trip and one server-side transaction.

    Args:
        holds: List of `{hold_id, bib_id}` pairs. Construct each entry
            from a row in `list_holds().holds` — `hold_id` and
            `metadata_id` map directly.
        dry_run: If true, look up each hold and report what would be
            cancelled without doing it. Use as a self-check before
            committing.
    """
    if not holds:
        raise ToolError("holds list is empty — nothing to cancel")

    client = _ensure_client()

    if dry_run:
        existing = client.list_holds().get("entities", {}).get("holds", {})
        would: list[str] = []
        failures: dict[str, str] = {}
        for ref in holds:
            hold = existing.get(ref.hold_id)
            if not hold:
                failures[ref.hold_id] = "hold not found on this account"
                continue
            title = hold.get("bibTitle") or "(unknown title)"
            position = hold.get("holdsPosition")
            pos_str = f" at queue position {position}" if position else ""
            would.append(f"{title!r}{pos_str}")
        return BulkCancelHoldsResult(
            cancelled=[],
            failures=failures,
            dry_run=True,
            would_cancel=would,
        )

    pairs = [(ref.hold_id, ref.bib_id) for ref in holds]
    data = client.cancel_holds(pairs)
    failures = data.get("failures") or {}
    requested = [ref.hold_id for ref in holds]
    cancelled = [hid for hid in requested if hid not in failures]
    return BulkCancelHoldsResult(cancelled=cancelled, failures=failures)


@mcp.tool(
    title="List checkouts with due dates",
    annotations=READ_ONLY,
    meta=ui_tool_meta(UI_RESOURCES["loans"]),
)
@_safe
def list_loans() -> LoanList:
    """Show current checkouts (physical + digital) with due dates.

    Each `Loan` carries an `actions` list copied from the gateway —
    items with `"renew"` are renewable via `renew_loan`; items with
    `"checkIn"` are digital loans returnable early. `times_renewed`
    shows how many times each has already been renewed.
    """
    client = _ensure_client()
    data = client.list_loans()
    checkouts = data.get("entities", {}).get("checkouts", {})
    out = [_loan_from_entity(cid, c, data) for cid, c in checkouts.items()]
    return LoanList(count=len(out), loans=out)


def _lookup_checkout(client: Client, checkout_id: str) -> dict | None:
    """Find one checkout entity by id; None if absent on this account."""
    data = client.list_loans()
    return data.get("entities", {}).get("checkouts", {}).get(checkout_id)


@mcp.tool(title="Renew a checkout", annotations=MUTATION)
@_safe
def renew_loan(checkout_id: str, dry_run: bool = False) -> RenewLoanResult:
    """Renew one physical checkout by id.

    Reversible in spirit — renewal just pushes the due date out. But
    not all loans renew: digital items, items with holds queued behind
    them, and items at the renewal cap are rejected by the gateway.
    Use `dry_run=True` to pre-check via the `actions` list before
    spending an API call.

    For multiple checkouts, prefer `renew_loans` — it's one PATCH
    instead of N.

    Args:
        checkout_id: From `list_loans().loans[i].checkout_id`.
        dry_run: If true, look up the checkout and describe whether it
            *appears* renewable (based on the gateway's `actions`
            array) without making a call. Useful as an agent self-check.
    """
    client = _ensure_client()
    if dry_run:
        c = _lookup_checkout(client, checkout_id)
        if not c:
            return RenewLoanResult(
                success=False,
                dry_run=True,
                failures={checkout_id: "checkout not found on this account"},
            )
        actions = c.get("actions") or []
        if "renew" not in actions:
            return RenewLoanResult(
                success=False,
                dry_run=True,
                failures={
                    checkout_id: (
                        f"gateway does not list 'renew' as an available "
                        f"action (actions={actions})"
                    )
                },
            )
        title = c.get("bibTitle") or "(unknown title)"
        due = c.get("dueDate")
        due_str = f", currently due {due}" if due else ""
        return RenewLoanResult(
            success=True,
            dry_run=True,
            would_renew=f"{title!r}{due_str}",
        )
    data = client.renew_checkouts([checkout_id])
    failures = _renewal_failures(data)
    if checkout_id in failures:
        return RenewLoanResult(success=False, failures=failures)
    renewed = data.get("entities", {}).get("checkouts", {}).get(checkout_id) or {}
    return RenewLoanResult(
        success=True,
        new_due=renewed.get("dueDate"),
        times_renewed=renewed.get("timesRenewed"),
    )


@mcp.tool(title="Renew multiple checkouts in one call", annotations=MUTATION)
@_safe
def renew_loans(checkout_ids: list[str], dry_run: bool = False) -> BulkRenewLoansResult:
    """Renew one or more checkouts in a single gateway call.

    Prefer this over multiple `renew_loan` calls when the user has a
    list — it's one PATCH and one server-side transaction.

    Args:
        checkout_ids: From `list_loans().loans[i].checkout_id`.
        dry_run: If true, look up each checkout and report whether each
            *appears* renewable (based on the gateway's `actions`
            array) without making a call.
    """
    if not checkout_ids:
        raise ToolError("checkout_ids list is empty — nothing to renew")

    client = _ensure_client()

    if dry_run:
        existing = client.list_loans().get("entities", {}).get("checkouts", {})
        would: list[str] = []
        failures: dict[str, str] = {}
        for cid in checkout_ids:
            c = existing.get(cid)
            if not c:
                failures[cid] = "checkout not found on this account"
                continue
            actions = c.get("actions") or []
            if "renew" not in actions:
                failures[cid] = (
                    f"gateway does not list 'renew' as an available "
                    f"action (actions={actions})"
                )
                continue
            title = c.get("bibTitle") or "(unknown title)"
            due = c.get("dueDate")
            due_str = f", currently due {due}" if due else ""
            would.append(f"{title!r}{due_str}")
        return BulkRenewLoansResult(
            renewed={},
            failures=failures,
            dry_run=True,
            would_renew=would,
        )

    data = client.renew_checkouts(checkout_ids)
    failures = _renewal_failures(data)
    renewed_entities = data.get("entities", {}).get("checkouts", {}) or {}
    renewed: dict[str, str] = {}
    for cid in checkout_ids:
        if cid in failures:
            continue
        entity = renewed_entities.get(cid) or {}
        # Gateway always echoes the renewed checkout entity back with
        # the new due date. If we requested it and it's not in failures,
        # we expect it here — but fall back gracefully if BC's envelope
        # ever omits the entity for some reason.
        renewed[cid] = entity.get("dueDate") or ""
    return BulkRenewLoansResult(renewed=renewed, failures=failures)


def _renewal_failures(data: dict) -> dict[str, str]:
    """Normalize the gateway's `failures` array to {checkout_id: reason}.

    The successful capture showed `failures: []` — an empty list. The
    failure shape isn't directly observed yet; the gateway likely emits
    either a list of objects (with checkoutId + message) or a dict keyed
    by id. Handle both defensively; first real failure surface will tell
    us which it is and we can simplify.
    """
    fails = data.get("failures")
    if not fails:
        return {}
    if isinstance(fails, dict):
        return {str(k): str(v) for k, v in fails.items()}
    out: dict[str, str] = {}
    for item in fails:
        if not isinstance(item, dict):
            continue
        cid = item.get("checkoutId") or item.get("id") or item.get("itemId") or ""
        msg = (
            item.get("message") or item.get("error") or item.get("reason") or str(item)
        )
        if cid:
            out[str(cid)] = str(msg)
    return out


@mcp.tool(title="List branches at your library", annotations=READ_ONLY)
@_safe
def list_branches() -> BranchList:
    """List every branch with its 3-letter pickup code."""
    client = _ensure_client()
    return BranchList(
        library=client.library,
        branches=[BranchModel(code=b.code, name=b.name) for b in client.branches.all()],
    )


@mcp.tool(title="Check login and hold quotas", annotations=READ_ONLY)
@_safe
def library_health() -> LibraryHealth:
    """Verify login + report hold counts vs. caps.

    Run this first if something seems off — it confirms the configured
    library, the account id the gateway recognises, and the user's
    current hold quotas.
    """
    client = _ensure_client()
    q = client.hold_quotas()
    holds_data = client.list_holds()
    holds = holds_data.get("entities", {}).get("holds", {}).values()
    physical = sum(1 for h in holds if h.get("materialType") == "PHYSICAL")
    digital = sum(1 for h in holds if h.get("materialType") == "DIGITAL")

    # SPL (and some libraries) don't expose an ILS quota — report "unlimited"
    physical_cap = (
        f"{physical}/{q.ils_total}" if q.ils_total > 0 else f"{physical}/unlimited"
    )
    return LibraryHealth(
        library=client.library,
        account_id=client.account_id,
        logged_in=True,
        default_pickup_branch=_cfg.default_pickup_branch if _cfg else None,
        physical_holds=physical_cap,
        digital_holds=f"{digital}/{q.overdrive_total}"
        if q.overdrive_total > 0
        else f"{digital}/unlimited",
        digital_remaining=q.overdrive_remaining if q.overdrive_total > 0 else None,
    )


# ─────────────────────────────── entry point ───────────────────────────────


def _setup_logging() -> None:
    """Stderr only — stdout is reserved for the MCP wire protocol."""
    level_name = os.environ.get("BIBLIOCOMMONS_MCP_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)
    logging.basicConfig(
        level=level,
        format="[bibliocommons-mcp] %(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
        force=True,
    )


def main() -> None:
    """Console-script entry point.

    Subcommands:
      (no args)   start the MCP server over stdio (default)
      init        run the interactive setup wizard
      --version   print the package version
      --help      print this message
    """
    argv = sys.argv[1:]
    if argv and argv[0] in {"-h", "--help"}:
        print(main.__doc__.strip() if main.__doc__ else "bibliocommons-mcp")
        return
    if argv and argv[0] in {"-V", "--version"}:
        from . import __version__

        print(__version__)
        return
    if argv and argv[0] == "init":
        from .init import run as init_run

        sys.exit(init_run())

    _setup_logging()
    try:
        Config.load()  # fail-fast at startup
    except ConfigError as e:
        print(f"bibliocommons-mcp config error: {e}", file=sys.stderr)
        print(
            "Run 'bibliocommons-mcp init' to set up your config.",
            file=sys.stderr,
        )
        sys.exit(2)
    logger.info("Starting bibliocommons-mcp (stdio)")
    try:
        mcp.run(transport="stdio")
    except (BCError, BranchNotFound) as exc:
        logger.error("Server error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
