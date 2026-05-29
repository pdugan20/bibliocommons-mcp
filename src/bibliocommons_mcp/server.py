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

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import JSONResponse

from .auth import workos_auth_from_env
from .branches import BranchNotFound
from .cache import TTLCache
from .client import BCError, Client, NotAuthenticatedError
from .config import Config, ConfigError
from .credentials import CredentialStore, InMemoryCredentialStore, UserCredentials
from .models import (
    Availability,
    AvailabilityCopy,
    BibSummary,
    BorrowDigitalResult,
    BranchList,
    BulkBorrowDigitalResult,
    BulkCancelHoldsResult,
    BulkCheckInLoansResult,
    BulkPlaceDigitalHoldResult,
    BulkPlaceHoldResult,
    BulkRenewLoansResult,
    CheckoutRef,
    DigitalFormat,
    Hold,
    HoldList,
    HoldRef,
    Jacket,
    LibraryHealth,
    Loan,
    LoanList,
    PlaceHoldResult,
    SearchResult,
)
from .models import Branch as BranchModel
from .web_settings import (
    WebSettingsConfigError,
    register_account_routes,
    web_settings_from_env,
)

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


# ─────────────────────────────── server instructions ───────────────────────────────

INSTRUCTIONS = """
bibliocommons-mcp connects to one BiblioCommons-powered public library
(Seattle, SFPL, etc.) and exposes catalog search, holds, and account
management as MCP tools.

All mutation tools accept a list of IDs/refs — pass `[id]` for the
common single-item case. Result envelopes carry per-item `placed`/
`borrowed`/`renewed`/etc. dicts plus a `failures` dict so partial
success is always representable.

Common workflows:

- "find a CD and place a hold" — `search` (with `format="MUSIC_CD"`),
  pick a result, optionally `availability` to confirm a copy at the
  user's branch, then `place_hold(bib_ids=[id])`. The user's default
  pickup branch comes from config; respect their choice unless they
  specify another.
- "what am I waiting on" — `list_holds`. Position 1 means front of the
  queue; higher numbers mean farther back.
- "what's due back" — `list_loans`.
- "cancel a hold" — `list_holds` first to get the hold id, then
  `cancel_hold(holds=[{hold_id, bib_id}])`. **Irreversible** — losing
  queue position can't be recovered. Confirm before calling.
- "is the catalog working" — `library_health` is the right first call
  when something seems off.

Important constraints:

- One library per server instance; the configured subdomain is fixed
  at startup.
- `place_hold` requires physical bibs (CD, book, DVD, ...). For
  available digital items, use `borrow_digital` (immediate borrow).
  For unavailable digital items, use `place_digital_hold` (joins the
  Libby waitlist).
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


def _build_mcp() -> FastMCP:
    """Construct the FastMCP server, enabling OAuth Resource-Server auth iff
    WorkOS is configured in the environment.

    Auth is opt-in (see auth.workos_auth_from_env): with `WORKOS_*` env set,
    the HTTP transport validates WorkOS bearer tokens and advertises
    protected-resource metadata; without it, the server is authless
    (Milestone-1 read-only catalog mode). stdio never enforces auth.
    """
    kwargs: dict = {"instructions": INSTRUCTIONS.strip()}
    auth = workos_auth_from_env()
    if auth is not None:
        verifier, settings = auth
        kwargs["token_verifier"] = verifier
        kwargs["auth"] = settings
        logger.info(
            "WorkOS Resource-Server auth enabled (resource=%s)",
            settings.resource_server_url,
        )
    return FastMCP("bibliocommons-mcp", **kwargs)


mcp = _build_mcp()

# Register the prebuilt React bundles as MCP Apps UI resources. The
# mapping is used below by tools that want to render a card; passing
# `meta=ui_tool_meta(UI_RESOURCES[name])` to `@mcp.tool` tells a
# UI-capable host (Claude Desktop, Inspector) which bundle to mount.
from . import ui_resources  # noqa: E402  (import after FastMCP init)
from .ui import ui_tool_meta  # noqa: E402

UI_RESOURCES = ui_resources.register_all(mcp)

_cfg: Config | None = None
_client: Client | None = None

# Multi-user (WorkOS auth on): per-subject credentials + an authenticated-client
# cache keyed on the token `subject`. In single-tenant / stdio mode these stay
# empty and the globals above are used. The cache holds each user's cookie jar
# in memory only (per-session model, brief §2), bounded by idle-TTL + LRU size
# so a long-lived process doesn't grow without limit and sessions refresh
# periodically. Evicting a client just re-authenticates from the stored creds
# on next use — the user isn't re-prompted. Tunable via env:
#   BIBLIOCOMMONS_MCP_SESSION_TTL    idle seconds before a cached client drops
#                                    (default 86400 = 24h)
#   BIBLIOCOMMONS_MCP_MAX_SESSIONS   LRU cap on cached clients (default 1000)
_cred_store: CredentialStore = InMemoryCredentialStore()
_user_clients: TTLCache[Client] = TTLCache(
    ttl=float(os.environ.get("BIBLIOCOMMONS_MCP_SESSION_TTL") or 86400),
    maxsize=int(os.environ.get("BIBLIOCOMMONS_MCP_MAX_SESSIONS") or 1000),
)

# Account settings page (/account): browser flow for capturing each user's
# library credentials into _cred_store. Enabled only when WorkOS is configured
# with an API key (the browser code exchange needs the confidential secret).
try:
    _web_settings_cfg = web_settings_from_env()
except WebSettingsConfigError as _exc:
    logger.warning("account settings page disabled: %s", _exc)
    _web_settings_cfg = None
if _web_settings_cfg is not None:
    register_account_routes(mcp, _web_settings_cfg, _cred_store)
    logger.info("account settings page enabled at /account")


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(_request: Request) -> JSONResponse:
    """Liveness probe for the HTTP transport (Cloud Run / Fly health checks).

    Deliberately credential-free and side-effect-free: it reports the
    configured library and whether the server has credentials (i.e. whether
    account tools are live vs read-only catalog mode), without logging in or
    touching the gateway. Served at the root regardless of the MCP path.
    """
    library = None
    has_creds = False
    try:
        cfg = Config.load(require_credentials=False)
        library = cfg.library
        has_creds = cfg.has_credentials
    except ConfigError:
        return JSONResponse({"status": "misconfigured"}, status_code=503)
    return JSONResponse(
        {
            "status": "ok",
            "library": library,
            "mode": "authenticated" if has_creds else "read-only",
        }
    )


def _current_subject() -> str | None:
    """The authenticated user id (JWT `sub`) for this request, or None.

    None means no auth context — stdio, or the authless M1 HTTP deployment —
    in which case the single-server Config path is used.
    """
    try:
        token = get_access_token()
    except Exception:
        return None
    return getattr(token, "subject", None) if token else None


def _ensure_single_client() -> Client:
    """Single-tenant path: one Config-driven client for the whole server.

    Used by stdio and the authless read-only M1 deployment. Loads config
    without forcing credentials so catalog mode works; authenticates only when
    card/PIN are present.
    """
    global _cfg, _client
    if _client is None:
        _cfg = Config.load(require_credentials=False)
        _client = Client(_cfg.library)
        if _cfg.has_credentials:
            _client.authenticate(_cfg.card, _cfg.pin)
    return _client


def _setup_required_message() -> str:
    base = (
        "No library account is configured for your connector yet. Add your "
        "library, card number, and PIN"
    )
    url = os.environ.get("BIBLIOCOMMONS_MCP_SETTINGS_URL")
    return f"{base} at {url} to use this tool." if url else f"{base} to use this tool."


def _ensure_user_client(subject: str) -> Client:
    """Multi-tenant path: resolve (and cache) this user's authenticated client.

    Looks up the subject's UserCredentials, mints a Client for their library,
    and authenticates if card/PIN are present. No record → a clean
    NotAuthenticatedError pointing at the setup page (PR-B). The cookie jar is
    cached in memory per the per-session model.
    """
    client = _user_clients.get(subject)
    if client is not None:
        return client
    creds = _cred_store.get(subject)
    if creds is None:
        raise NotAuthenticatedError(_setup_required_message())
    client = Client(creds.library)
    if creds.has_credentials:
        client.authenticate(creds.card, creds.pin)
    _user_clients.put(subject, client)
    return client


def _ensure_client() -> Client:
    """Resolve the gateway Client for this request.

    Identity-aware: with an authenticated subject (multi-user / WorkOS mode)
    each user gets their own client; otherwise the single-server config client.
    Account tools that need credentials surface NotAuthenticatedError (→ a
    clean ToolError) when they reach `client.account_id`.
    """
    subject = _current_subject()
    if subject is None:
        return _ensure_single_client()
    return _ensure_user_client(subject)


def _effective_cfg() -> Config | UserCredentials | None:
    """Config-ish record for this request: the per-user record in multi-user
    mode, else the single-server Config. Both expose library/card/pin/
    default_pickup_branch/default_format/digital_notification_email/
    has_credentials, so tools read defaults uniformly. Call after
    `_ensure_client()` so the single-server `_cfg` is populated.
    """
    subject = _current_subject()
    if subject is None:
        return _cfg
    return _cred_store.get(subject)


def _resolve_branch(name_or_code: str | None) -> str:
    """Resolve a branch name/code to a code, falling back to the user's default."""
    client = _ensure_client()
    cfg = _effective_cfg()
    target = name_or_code or (cfg.default_pickup_branch if cfg else None)
    if not target:
        raise ToolError(
            "pickup_branch is required (or set a default pickup branch in config)"
        )
    return client.branches.resolve(target).code


def _safe(fn: Callable) -> Callable:
    """Wrap a tool so known exceptions surface as ToolError with a clean message.

    BCError (gateway errors), BranchNotFound (resolver), ValueError
    (caller mistakes), and NotAuthenticatedError (account op in read-only mode)
    become ToolError. Anything else propagates and FastMCP renders the
    class + message.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (BCError, BranchNotFound, ValueError, NotAuthenticatedError) as e:
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
    cfg = _effective_cfg()
    fmt = format or (cfg.default_format if cfg else None)
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


@mcp.tool(title="Place physical holds", annotations=MUTATION)
@_safe
def place_hold(
    bib_ids: list[str],
    pickup_branch: str | None = None,
    delay_seconds: float = 1.0,
) -> BulkPlaceHoldResult:
    """Place a physical hold on one or more bibs at the same pickup branch.

    Pass `[bib_id]` for the common single-item case. The gateway has no
    batch endpoint for placement, so this is N sequential POSTs with a
    small delay to avoid gateway rate-limiting.

    Per-bib failures don't stop the run — placement continues and the
    result splits successes (`placed`) and failures (`failures`) so the
    agent can report partial completion. Common failure causes: the
    user already has the item on hold (409), the item isn't holdable
    (reference-only), or a transient gateway 5xx.

    Args:
        bib_ids: List of bib IDs. Pass `[id]` for a single hold. Order
            is preserved during placement (first attempted first).
        pickup_branch: Branch name or 3-letter code applied to every
            hold. Defaults to `default_pickup_branch` from config.
            Names are matched case-insensitively; locker variants are
            de-prioritized when the query is ambiguous.
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


def _borrow_digital_one(client: Client, bib_id: str) -> BorrowDigitalResult:
    """Borrow one digital item; shared by the list-accepting tool."""
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


@mcp.tool(title="Borrow available digital items", annotations=MUTATION)
@_safe
def borrow_digital(
    bib_ids: list[str], delay_seconds: float = 1.0
) -> BulkBorrowDigitalResult:
    """Check out one or more immediately-available digital items.

    Pass `[bib_id]` for the common single-item case. Use this when an
    ebook or e-audiobook is "Available Now" rather than queued. For
    unavailable digital items, use `place_digital_hold` to join the
    waitlist.

    No native bulk endpoint exists — this is N sequential POSTs with
    `delay_seconds` between each. Per-bib failures don't stop the run.

    Args:
        bib_ids: List of bib IDs. Pass `[id]` for a single borrow.
        delay_seconds: Pause between each gateway call.
    """
    if not bib_ids:
        raise ToolError("bib_ids list is empty — nothing to borrow")

    client = _ensure_client()
    borrowed: dict[str, BorrowDigitalResult] = {}
    failures: dict[str, str] = {}

    for i, bib_id in enumerate(bib_ids):
        if i > 0 and delay_seconds > 0:
            time.sleep(delay_seconds)
        try:
            borrowed[bib_id] = _borrow_digital_one(client, bib_id)
        except BCError as e:
            failures[bib_id] = e.message

    return BulkBorrowDigitalResult(borrowed=borrowed, failures=failures)


def _place_digital_hold_one(client: Client, bib_id: str, email: str) -> PlaceHoldResult:
    """Place one digital hold; shared by the list-accepting tool."""
    data = client.place_digital_hold(bib_id, email)
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
        # Digital holds don't have a pickup_branch — the email is the
        # notification target.
        pickup_branch=None,
        position=hold.get("holdsPosition"),
        status=hold.get("status"),
        expiry=hold.get("expiryDate"),
    )


@mcp.tool(
    title="Place holds on unavailable digital items",
    annotations=MUTATION,
)
@_safe
def place_digital_hold(
    bib_ids: list[str], delay_seconds: float = 1.0
) -> BulkPlaceDigitalHoldResult:
    """Join the Libby-side waitlist for one or more unavailable digital items
    (`availableCopies: 0` on the bib).

    Pass `[bib_id]` for the common single-item case. Counts against
    your digital hold quota — see `library_health`.

    Requires `digital_notification_email` to be set in config (or
    `BIBLIOCOMMONS_DIGITAL_EMAIL` env var). The gateway emails that
    address when the hold turns into a checkout, same as the Libby
    app would.

    For digital items that are immediately available, use
    `borrow_digital` instead — that checks out the copy directly
    rather than queueing a hold.

    No native bulk endpoint exists — this is N sequential POSTs with
    `delay_seconds` between each.

    Args:
        bib_ids: List of bib IDs. Pass `[id]` for a single hold.
        delay_seconds: Pause between each gateway call.
    """
    if not bib_ids:
        raise ToolError("bib_ids list is empty — nothing to place")

    client = _ensure_client()
    cfg = _effective_cfg()
    if not cfg or not cfg.digital_notification_email:
        raise ToolError(
            "digital_notification_email is required to place digital holds. "
            "Set it in your config (BIBLIOCOMMONS_DIGITAL_EMAIL / config.toml), "
            "or in your connector account settings on a hosted server. Use the "
            "same email your BiblioCommons account has on file for notifications."
        )
    email = cfg.digital_notification_email
    placed: dict[str, PlaceHoldResult] = {}
    failures: dict[str, str] = {}

    for i, bib_id in enumerate(bib_ids):
        if i > 0 and delay_seconds > 0:
            time.sleep(delay_seconds)
        try:
            placed[bib_id] = _place_digital_hold_one(client, bib_id, email)
        except BCError as e:
            failures[bib_id] = e.message

    return BulkPlaceDigitalHoldResult(placed=placed, failures=failures)


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


@mcp.tool(title="Cancel holds", annotations=DESTRUCTIVE)
@_safe
def cancel_hold(holds: list[HoldRef], dry_run: bool = False) -> BulkCancelHoldsResult:
    """Cancel one or more holds in a single gateway call.

    Pass `[{hold_id, bib_id}]` for the common single-item case.
    **Irreversible** for each cancelled hold (lost queue position).
    Confirm with the user before calling with `dry_run=False`.

    The gateway's DELETE /holds endpoint is natively bulk — every call
    is one HTTP round-trip and one server-side transaction regardless
    of array length.

    Args:
        holds: List of `{hold_id, bib_id}` pairs. Pass `[{...}]` for a
            single cancel. Each pair maps to a row from
            `list_holds().holds` — `hold_id` and `metadata_id`.
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


@mcp.tool(title="Renew checkouts", annotations=MUTATION)
@_safe
def renew_loan(checkout_ids: list[str], dry_run: bool = False) -> BulkRenewLoansResult:
    """Renew one or more physical checkouts in a single gateway call.

    Pass `[checkout_id]` for the common single-item case. Reversible
    in spirit — renewal just pushes the due date out. But not all
    loans renew: digital items, items with holds queued behind them,
    and items at the renewal cap are rejected by the gateway. Use
    `dry_run=True` to pre-check via the `actions` list before spending
    an API call.

    The gateway's PATCH /checkouts endpoint is natively bulk — every
    call is one HTTP round-trip regardless of array length.

    Args:
        checkout_ids: From `list_loans().loans[i].checkout_id`. Pass
            `[id]` for a single renewal.
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


@mcp.tool(title="Return (check in) digital checkouts early", annotations=MUTATION)
@_safe
def check_in_loan(
    checkouts: list[CheckoutRef],
    dry_run: bool = False,
    delay_seconds: float = 0.5,
) -> BulkCheckInLoansResult:
    """Return one or more digital checkouts (ebook / eaudiobook) early.

    Pass `[{checkout_id, metadata_id}]` for the common single-item case.
    Only works on items where `list_loans().loans[i].actions` includes
    `"checkIn"` — physical items are returned at the branch and don't
    have this affordance. The freed slot reflects in the OverDrive
    quota immediately.

    No native bulk endpoint exists — this is N sequential DELETEs with
    `delay_seconds` between each. Each row succeeds or fails
    independently; partial success is normal.

    Args:
        checkouts: List of `{checkout_id, metadata_id}` pairs. Pass
            `[{...}]` for a single check-in. Each pair maps to a row
            from `list_loans().loans` — `checkout_id` and `metadata_id`.
        dry_run: If true, look up each checkout and report whether
            `"checkIn"` is in its `actions` list, without making any
            calls.
        delay_seconds: Sleep between calls. Default 0.5s; raise this
            if you start seeing 429s.
    """
    if not checkouts:
        raise ToolError("checkouts list is empty — nothing to check in")

    client = _ensure_client()

    if dry_run:
        existing = client.list_loans().get("entities", {}).get("checkouts", {})
        would: list[str] = []
        failures: dict[str, str] = {}
        for ref in checkouts:
            c = existing.get(ref.checkout_id)
            if not c:
                failures[ref.checkout_id] = "checkout not found on this account"
                continue
            actions = c.get("actions") or []
            if "checkIn" not in actions:
                failures[ref.checkout_id] = (
                    f"gateway does not list 'checkIn' as an available "
                    f"action (actions={actions})"
                )
                continue
            title = c.get("bibTitle") or "(unknown title)"
            would.append(repr(title))
        return BulkCheckInLoansResult(
            checked_in=[],
            failures=failures,
            dry_run=True,
            would_check_in=would,
        )

    checked_in: list[str] = []
    failures: dict[str, str] = {}
    for i, ref in enumerate(checkouts):
        if i > 0:
            time.sleep(delay_seconds)
        try:
            data = client.check_in_loan(ref.checkout_id, ref.metadata_id)
            if isinstance(data, dict) and data.get("id"):
                checked_in.append(ref.checkout_id)
            else:
                failures[ref.checkout_id] = (
                    "gateway returned no id — check_in may not have landed"
                )
        except BCError as e:
            failures[ref.checkout_id] = str(e)
    return BulkCheckInLoansResult(checked_in=checked_in, failures=failures)


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
    cfg = _effective_cfg()
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
        default_pickup_branch=cfg.default_pickup_branch if cfg else None,
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


def _http_requested(argv: list[str]) -> bool:
    """Whether to serve Streamable HTTP instead of stdio.

    Triggered by `serve --http` or `BIBLIOCOMMONS_MCP_TRANSPORT=http`. stdio
    stays the default so local Claude Code / Claude Desktop are unaffected.
    """
    if os.environ.get("BIBLIOCOMMONS_MCP_TRANSPORT", "").lower() in {
        "http",
        "streamable-http",
    }:
        return True
    return argv[:1] == ["serve"] and "--http" in argv


def _run_http() -> None:
    """Serve over Streamable HTTP (remote/mobile connector transport).

    Credentials are optional here — a missing card/PIN boots read-only
    "catalog mode" (search/availability/list_branches), which is Milestone 1
    of the remote-connector plan. `stateless_http=True` because a multi-tenant
    remote service shouldn't pin sticky sessions; `$PORT` is honored for
    Cloud Run / Fly. See docs/projects/remote-mcp-mobile.md.
    """
    try:
        cfg = Config.load(require_credentials=False)
    except ConfigError as e:
        print(f"bibliocommons-mcp config error: {e}", file=sys.stderr)
        print(
            "Run 'bibliocommons-mcp init' to set up your config "
            "(or set BIBLIOCOMMONS_LIBRARY for read-only catalog mode).",
            file=sys.stderr,
        )
        sys.exit(2)

    mcp.settings.host = os.environ.get("FASTMCP_HOST", "0.0.0.0")
    mcp.settings.port = int(
        os.environ.get("PORT") or os.environ.get("FASTMCP_PORT") or 8000
    )
    mcp.settings.stateless_http = True
    # Two independent axes: WorkOS OAuth (server-level access) and library
    # credentials (account tools). Report both so the operator isn't misled.
    auth_mode = "WorkOS OAuth" if workos_auth_from_env() else "authless"
    creds_mode = "library creds set" if cfg.has_credentials else "read-only catalog"
    logger.info(
        "Starting bibliocommons-mcp (streamable-http) on %s:%s [%s, %s, library=%s]",
        mcp.settings.host,
        mcp.settings.port,
        auth_mode,
        creds_mode,
        cfg.library,
    )
    try:
        mcp.run(transport="streamable-http")
    except (BCError, BranchNotFound) as exc:
        logger.error("Server error: %s", exc)
        sys.exit(1)


def main() -> None:
    """Console-script entry point.

    Subcommands:
      (no args)      start the MCP server over stdio (default)
      serve --http   start the server over Streamable HTTP (remote connector)
      init           run the interactive setup wizard
      --version      print the package version
      --help         print this message

    HTTP can also be selected with BIBLIOCOMMONS_MCP_TRANSPORT=http. In HTTP
    mode, credentials are optional: without them the server runs read-only
    "catalog mode". See docs/projects/remote-mcp-mobile.md.
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

    if _http_requested(argv):
        _run_http()
        return

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
