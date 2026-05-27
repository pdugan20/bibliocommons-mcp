"""FastMCP server for bibliocommons-mcp.

Single library per server, configured via
``~/.config/bibliocommons-mcp/config.toml``. Tools:
  search                 search the catalog with optional format/sort/page
  availability           per-branch availability for a bib
  place_hold             place a physical hold with pickup branch
  borrow_digital         check out an available digital item
  list_holds             your current holds (physical + digital)
  cancel_hold            cancel a hold by id
  list_loans             your current checkouts
  list_branches          branches at your configured library
  library_health         login probe + hold quota readout

Place holds on unavailable digital items are not yet supported (v1.1).
"""

from __future__ import annotations

import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

from .branches import BranchNotFound
from .client import BCError, Client
from .config import Config, ConfigError

logger = logging.getLogger(__name__)

mcp = FastMCP("bibliocommons-mcp")

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
        raise ValueError(
            "pickup_branch is required (or set default_pickup_branch in config)"
        )
    return client.branches.resolve(target).code


def _bib_brief(bib: dict) -> dict:
    """Compact view of a search/holds bib for tool responses."""
    bi = bib.get("briefInfo", {})
    return {
        "bib_id": bib.get("id") or bi.get("metadataId"),
        "title": bi.get("title"),
        "subtitle": bi.get("subtitle"),
        "authors": bi.get("authors") or [],
        "format": bi.get("format"),
        "year": bi.get("publicationDate"),
        "call_number": bi.get("callNumber"),
    }


# ─────────────────────────────── tools ───────────────────────────────


@mcp.tool()
def search(
    query: str,
    format: str | None = None,
    page: int = 1,
    sort_by: str | None = None,
) -> dict:
    """Search the catalog. Returns a list of matching bibs.

    Args:
      query: keyword search string.
      format: format facet, e.g. "MUSIC_CD" (CDs), "BK" (book), "EBOOK",
              "EAUDIOBOOK", "AUDIOBOOK_CD", "DVD". Omit for any format.
              Defaults to config.default_format if set.
      page: 1-indexed page (page size is fixed at 25 by the gateway).
      sort_by: optional. One of "relevancy", "newly_acquired", "title",
              "author", "published_date", "ugc_rating".
    """
    client = _ensure_client()
    fmt = format or (_cfg.default_format if _cfg else None)
    data = client.search(query, format=fmt, page=page, sort_by=sort_by)
    bibs = data.get("entities", {}).get("bibs", {})
    pag = data.get("catalogSearch", {}).get("pagination", {})
    return {
        "page": pag.get("page"),
        "pages": pag.get("pages"),
        "total": pag.get("count"),
        "results": [_bib_brief(bibs[bid]) for bid in bibs],
    }


@mcp.tool()
def availability(bib_id: str) -> dict:
    """Show per-branch availability for a bib. Includes branch code, name,
    call number, and current status of each copy."""
    client = _ensure_client()
    data = client.availability(bib_id)
    summary = data.get("entities", {}).get("availabilities", {}).get(bib_id, {})
    items = data.get("entities", {}).get("bibItems", {})
    copies = []
    for it in items.values():
        copies.append(
            {
                "branch_code": it.get("branch", {}).get("code"),
                "branch_name": it.get("branch", {}).get("name"),
                "status": it.get("availability", {}).get("status"),
                "library_status": it.get("availability", {}).get("libraryStatus"),
                "call_number": it.get("callNumber"),
                "collection": it.get("collection"),
            }
        )
    return {
        "bib_id": bib_id,
        "total_copies": summary.get("totalCopies"),
        "available_copies": summary.get("availableCopies"),
        "held_copies": summary.get("heldCopies"),
        "status": summary.get("status"),
        "digital_formats": data.get("availability", {}).get("digitalFormats") or [],
        "copies": copies,
    }


@mcp.tool()
def place_hold(bib_id: str, pickup_branch: str | None = None) -> dict:
    """Place a physical hold on a bib (CD, book, DVD, etc.).

    Args:
      bib_id: the bib id (e.g. "S30C3857930").
      pickup_branch: branch name or 3-letter code (e.g. "Lake City" or "LCY").
                     Defaults to config.default_pickup_branch.
    """
    client = _ensure_client()
    branch_code = _resolve_branch(pickup_branch)
    data = client.place_physical_hold(bib_id, branch_code)
    holds = data.get("entities", {}).get("holds", {})
    if not holds:
        return {"success": False, "raw": data}
    hold_id = next(iter(holds))
    hold = holds[hold_id]
    return {
        "success": True,
        "hold_id": hold_id,
        "title": hold.get("bibTitle"),
        "material_type": hold.get("materialType"),
        "pickup_branch": hold.get("pickupLocation", {}).get("code"),
        "position": hold.get("holdsPosition"),
        "status": hold.get("status"),
        "expiry": hold.get("expiryDate"),
    }


@mcp.tool()
def borrow_digital(bib_id: str) -> dict:
    """Check out an available digital item (ebook/e-audiobook). Use this
    when an item is "Available Now" rather than queued — it borrows
    immediately instead of placing a hold.
    """
    client = _ensure_client()
    data = client.borrow_digital(bib_id)
    checkouts = data.get("entities", {}).get("checkouts", {})
    if not checkouts:
        return {"success": False, "raw": data}
    cid = next(iter(checkouts))
    co = checkouts[cid]
    return {
        "success": True,
        "checkout_id": cid,
        "title": co.get("bibTitle") or co.get("title"),
        "material_type": co.get("materialType"),
        "due": co.get("dueDate"),
        "call_number": co.get("callNumber"),
        "volume": co.get("volume"),
    }


@mcp.tool()
def list_holds() -> dict:
    """List your current holds (physical and digital)."""
    client = _ensure_client()
    data = client.list_holds()
    holds_ents = data.get("entities", {}).get("holds", {})
    out = []
    for hid, h in holds_ents.items():
        out.append(
            {
                "hold_id": hid,
                "metadata_id": h.get("metadataId"),
                "title": h.get("bibTitle"),
                "material_type": h.get("materialType"),
                "status": h.get("status"),
                "position": h.get("holdsPosition"),
                "pickup_branch": (h.get("pickupLocation") or {}).get("code"),
                "placed": h.get("holdPlacedDate"),
                "expiry": h.get("expiryDate"),
            }
        )
    return {"count": len(out), "holds": out}


@mcp.tool()
def cancel_hold(hold_id: str, bib_id: str) -> dict:
    """Cancel a hold. Both hold_id and bib_id are required (the gateway needs
    both). hold_id comes from list_holds().hold_id, bib_id from .metadata_id."""
    client = _ensure_client()
    data = client.cancel_holds([(hold_id, bib_id)])
    failures = data.get("failures") or {}
    return {
        "success": not failures,
        "failures": failures,
    }


@mcp.tool()
def list_loans() -> dict:
    """List your current checkouts (physical + digital) with due dates."""
    client = _ensure_client()
    data = client.list_loans()
    checkouts = data.get("entities", {}).get("checkouts", {})
    out = []
    for cid, c in checkouts.items():
        out.append(
            {
                "checkout_id": cid,
                "metadata_id": c.get("metadataId"),
                "title": c.get("bibTitle") or c.get("title"),
                "material_type": c.get("materialType"),
                "due": c.get("dueDate"),
                "call_number": c.get("callNumber"),
                "branch": (c.get("branch") or {}).get("code")
                if c.get("branch")
                else None,
            }
        )
    return {"count": len(out), "loans": out}


@mcp.tool()
def list_branches() -> dict:
    """List all branches at your configured library, with codes."""
    client = _ensure_client()
    return {
        "library": client.library,
        "branches": [{"code": b.code, "name": b.name} for b in client.branches.all()],
    }


@mcp.tool()
def library_health() -> dict:
    """Verify login works and report your hold counts + quotas. Run this
    first if something seems off."""
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
    return {
        "library": client.library,
        "account_id": client.account_id,
        "logged_in": True,
        "default_pickup_branch": _cfg.default_pickup_branch if _cfg else None,
        "physical_holds": physical_cap,
        "digital_holds": f"{digital}/{q.overdrive_total}"
        if q.overdrive_total > 0
        else f"{digital}/unlimited",
        "digital_remaining": q.overdrive_remaining if q.overdrive_total > 0 else None,
    }


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
    """Console-script entry point. Runs over stdio."""
    _setup_logging()
    try:
        Config.load()  # fail-fast at startup
    except ConfigError as e:
        print(f"bibliocommons-mcp config error: {e}", file=sys.stderr)
        sys.exit(2)
    logger.info("Starting bibliocommons-mcp (stdio)")
    try:
        mcp.run(transport="stdio")
    except (BCError, BranchNotFound) as exc:
        logger.error("Server error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
