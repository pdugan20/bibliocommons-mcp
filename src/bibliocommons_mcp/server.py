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
    CancelHoldResult,
    DigitalFormat,
    Hold,
    HoldList,
    LibraryHealth,
    Loan,
    LoanList,
    PlaceHoldResult,
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
    )


# ─────────────────────────────── tools ───────────────────────────────


@mcp.tool(title="Search the catalog", annotations=READ_ONLY)
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


@mcp.tool(title="Place a physical hold", annotations=MUTATION)
@_safe
def place_hold(bib_id: str, pickup_branch: str | None = None) -> PlaceHoldResult:
    """Place a physical hold on a bib (CD, book, DVD, etc.).

    Args:
        bib_id: The bib id (e.g. `S30C3857930`).
        pickup_branch: Branch name or 3-letter code (e.g. `Lake City`
            or `LCY`). Defaults to `default_pickup_branch` from config.
            Names are matched case-insensitively; locker variants are
            de-prioritized when the query is ambiguous.
    """
    client = _ensure_client()
    branch_code = _resolve_branch(pickup_branch)
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


@mcp.tool(title="List your holds", annotations=READ_ONLY)
@_safe
def list_holds() -> HoldList:
    """Show current holds (physical + digital) with queue positions."""
    client = _ensure_client()
    data = client.list_holds()
    holds_ents = data.get("entities", {}).get("holds", {})
    out = [
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
        )
        for hid, h in holds_ents.items()
    ]
    return HoldList(count=len(out), holds=out)


@mcp.tool(title="Cancel a hold", annotations=DESTRUCTIVE)
@_safe
def cancel_hold(hold_id: str, bib_id: str) -> CancelHoldResult:
    """Cancel a hold by id.

    **Irreversible** — cancelling loses your queue position. Confirm
    with the user first.

    Args:
        hold_id: From `list_holds().holds[i].hold_id`.
        bib_id: From the same row's `metadata_id`. Both are required by
            the gateway.
    """
    client = _ensure_client()
    data = client.cancel_holds([(hold_id, bib_id)])
    failures = data.get("failures") or {}
    return CancelHoldResult(success=not failures, failures=failures)


@mcp.tool(title="List checkouts with due dates", annotations=READ_ONLY)
@_safe
def list_loans() -> LoanList:
    """Show current checkouts (physical + digital) with due dates."""
    client = _ensure_client()
    data = client.list_loans()
    checkouts = data.get("entities", {}).get("checkouts", {})
    out = [
        Loan(
            checkout_id=cid,
            metadata_id=c.get("metadataId"),
            title=c.get("bibTitle") or c.get("title"),
            material_type=c.get("materialType"),
            due=c.get("dueDate"),
            call_number=c.get("callNumber"),
            branch=(c.get("branch") or {}).get("code") if c.get("branch") else None,
        )
        for cid, c in checkouts.items()
    ]
    return LoanList(count=len(out), loans=out)


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
