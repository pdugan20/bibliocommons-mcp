"""Pydantic response models for MCP tools.

Returning typed models (rather than raw dicts) gives MCP clients an
``outputSchema`` and ``structuredContent`` in addition to the text
representation. Clients that support structured output (Claude Desktop,
Claude Code, recent Cursor/VS Code) consume the JSON directly; older
clients fall back to the text rendering.

Keep values raw (status as strings, dates as ISO strings the gateway
already returns) — formatting belongs in the client, not here.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ─────────────────────────────── shared ───────────────────────────────


class Branch(BaseModel):
    """One branch at the configured library."""

    code: str = Field(description="Three-letter branch code, e.g. 'LCY'.")
    name: str = Field(description="Display name, e.g. 'Lake City Branch'.")


class Jacket(BaseModel):
    """Cover-art URLs from BiblioCommons (typically Syndetics-hosted).

    Three sizes plus an optional library-uploaded override. Clients that
    support image rendering can use any of these — small for list views,
    medium for cards, large for detail pages.
    """

    small: str | None = Field(default=None)
    medium: str | None = Field(default=None)
    large: str | None = Field(default=None)
    local_url: str | None = Field(
        default=None,
        description="Library-uploaded override, when present. Prefer over Syndetics.",
    )


class BibSummary(BaseModel):
    """Compact view of a catalog bib (book, CD, etc.)."""

    bib_id: str = Field(description="BiblioCommons bib id, e.g. 'S30C3857930'.")
    title: str | None = Field(default=None)
    subtitle: str | None = Field(default=None)
    authors: list[str] = Field(default_factory=list)
    format: str | None = Field(
        default=None, description="Format facet, e.g. 'MUSIC_CD', 'BK', 'EBOOK'."
    )
    year: str | None = Field(default=None, description="Publication date as printed.")
    call_number: str | None = Field(default=None)
    jacket: Jacket | None = Field(default=None)
    availability_status: str | None = Field(
        default=None, description="Aggregate copy status, 'AVAILABLE' / 'UNAVAILABLE'."
    )
    available_copies: int | None = Field(default=None)
    held_copies: int | None = Field(default=None)
    total_copies: int | None = Field(default=None)


class HoldRef(BaseModel):
    """Reference to a hold + its bib. Both are required to cancel."""

    hold_id: str = Field(description="From `Hold.hold_id`.")
    bib_id: str = Field(description="From `Hold.metadata_id`.")


# ─────────────────────────────── tool results ───────────────────────────────


class SearchResult(BaseModel):
    """Paginated search results. Page size is fixed at 25 by the gateway."""

    page: int | None = Field(default=None, description="1-indexed current page.")
    pages: int | None = Field(default=None, description="Total page count.")
    total: int | None = Field(default=None, description="Total matching bibs.")
    library: str | None = Field(
        default=None, description="Library display name, e.g. 'Seattle Public Library'."
    )
    more_url: str | None = Field(
        default=None, description="Catalog search page URL for a 'see all' link."
    )
    results: list[BibSummary] = Field(default_factory=list)


class AvailabilityCopy(BaseModel):
    """One physical copy of a bib."""

    branch_code: str | None = Field(default=None)
    branch_name: str | None = Field(default=None)
    status: str | None = Field(
        default=None,
        description="Copy status, e.g. 'AVAILABLE', 'CHECKED_OUT', 'ON_HOLDSHELF'.",
    )
    library_status: str | None = Field(
        default=None, description="Human-readable status from the ILS."
    )
    call_number: str | None = Field(default=None)
    collection: str | None = Field(default=None)


class DigitalFormat(BaseModel):
    """One downloadable format for a digital bib (Kindle, OverDrive Read, ...)."""

    name: str
    has_download_link: bool | None = Field(default=None)
    must_be_read_online: bool | None = Field(default=None)


class Availability(BaseModel):
    """Per-branch availability + status for a bib."""

    bib_id: str
    total_copies: int | None = Field(default=None)
    available_copies: int | None = Field(default=None)
    held_copies: int | None = Field(default=None)
    status: str | None = Field(default=None, description="Aggregate status.")
    digital_formats: list[DigitalFormat] = Field(default_factory=list)
    copies: list[AvailabilityCopy] = Field(default_factory=list)


class Hold(BaseModel):
    """One hold on the user's account."""

    hold_id: str
    metadata_id: str | None = Field(default=None, description="Bib id.")
    title: str | None = Field(default=None)
    author: str | None = Field(
        default=None, description="Primary creator, from the joined bib record."
    )
    material_type: str | None = Field(
        default=None, description="'PHYSICAL' or 'DIGITAL'."
    )
    format: str | None = Field(
        default=None, description="Format facet, e.g. 'BK', 'MUSIC_CD', 'EBOOK'."
    )
    year: str | None = Field(default=None, description="Publication date as printed.")
    status: str | None = Field(
        default=None, description="'NOT_YET_AVAILABLE', 'READY_FOR_PICKUP', etc."
    )
    position: int | None = Field(
        default=None, description="Position in the holds queue (1 = front)."
    )
    pickup_branch: str | None = Field(
        default=None, description="Three-letter branch code; null for digital holds."
    )
    placed: str | None = Field(
        default=None, description="ISO date the hold was placed."
    )
    expiry: str | None = Field(default=None)
    jacket: Jacket | None = Field(default=None)


class HoldList(BaseModel):
    count: int
    library: str | None = Field(
        default=None, description="Library display name, e.g. 'Seattle Public Library'."
    )
    more_url: str | None = Field(
        default=None, description="Catalog holds page URL for a 'view all' link."
    )
    holds: list[Hold] = Field(default_factory=list)


class Loan(BaseModel):
    """One current checkout on the user's account."""

    checkout_id: str
    metadata_id: str | None = Field(default=None)
    title: str | None = Field(default=None)
    author: str | None = Field(
        default=None, description="Primary creator, from the joined bib record."
    )
    material_type: str | None = Field(default=None)
    format: str | None = Field(
        default=None, description="Format facet, e.g. 'BK', 'MUSIC_CD', 'EBOOK'."
    )
    year: str | None = Field(default=None, description="Publication date as printed.")
    due: str | None = Field(default=None, description="ISO date due back.")
    call_number: str | None = Field(default=None)
    branch: str | None = Field(default=None)
    jacket: Jacket | None = Field(default=None)
    actions: list[str] = Field(
        default_factory=list,
        description=(
            "Actions the gateway says are available on this checkout, "
            "e.g. ['renew', 'updateFormat'] for renewable physical items "
            "or ['checkIn', 'updateFormat'] for digital items that can "
            "be returned early. Use this to pre-check before calling "
            "renew_loan — if 'renew' is absent, the call will fail."
        ),
    )
    times_renewed: int = Field(
        default=0,
        description="How many times this checkout has already been renewed.",
    )


class LoanList(BaseModel):
    count: int
    library: str | None = Field(
        default=None, description="Library display name, e.g. 'Seattle Public Library'."
    )
    more_url: str | None = Field(
        default=None, description="Catalog checkouts page URL for a 'view all' link."
    )
    loans: list[Loan] = Field(default_factory=list)


class BranchList(BaseModel):
    library: str = Field(description="Library subdomain, e.g. 'seattle'.")
    branches: list[Branch] = Field(default_factory=list)


class LibraryHealth(BaseModel):
    """Login probe + hold quotas."""

    library: str
    account_id: int
    logged_in: bool
    default_pickup_branch: str | None = Field(default=None)
    physical_holds: str = Field(
        description="Current count vs. cap, e.g. '2/unlimited' or '0/0'."
    )
    digital_holds: str = Field(description="Current count vs. cap, e.g. '3/10'.")
    digital_remaining: int | None = Field(default=None)


class PlaceHoldResult(BaseModel):
    success: bool
    hold_id: str | None = Field(default=None)
    title: str | None = Field(default=None)
    material_type: str | None = Field(default=None)
    pickup_branch: str | None = Field(default=None)
    position: int | None = Field(default=None)
    status: str | None = Field(default=None)
    expiry: str | None = Field(default=None)


class BorrowDigitalResult(BaseModel):
    success: bool
    checkout_id: str | None = Field(default=None)
    title: str | None = Field(default=None)
    material_type: str | None = Field(default=None)
    due: str | None = Field(default=None)
    call_number: str | None = Field(default=None)
    volume: str | None = Field(default=None)


class BulkCancelHoldsResult(BaseModel):
    """Result of `cancel_holds(...)`. Per-hold success/failure breakdown."""

    cancelled: list[str] = Field(
        default_factory=list, description="Hold IDs successfully cancelled."
    )
    failures: dict[str, str] = Field(
        default_factory=dict,
        description="Hold-id-keyed map of failure reasons.",
    )
    dry_run: bool = Field(default=False)
    would_cancel: list[str] = Field(
        default_factory=list,
        description=(
            "On a dry run, one human-readable summary per hold that would "
            "be cancelled (title + queue position). Empty when dry_run=False."
        ),
    )


class CheckoutRef(BaseModel):
    """Pair of (checkout_id, metadata_id) the gateway needs to act on a checkout.

    Both come from a row in `list_loans().loans`. The gateway requires the
    bib reference even when the checkout id is in the URL — same pattern
    as `HoldRef` for holds.
    """

    checkout_id: str = Field(description="From `list_loans().loans[i].checkout_id`.")
    metadata_id: str = Field(description="From `list_loans().loans[i].metadata_id`.")


class BulkCheckInLoansResult(BaseModel):
    """Result of `check_in_loans(...)`. Per-checkout success/failure breakdown.

    There's no native bulk endpoint — the client loops sequentially with
    a small inter-call delay, same pattern as `place_holds`. Each row
    succeeds or fails independently.
    """

    checked_in: list[str] = Field(
        default_factory=list,
        description="Checkout IDs successfully checked in.",
    )
    failures: dict[str, str] = Field(
        default_factory=dict,
        description="Checkout-id-keyed map of failure reasons.",
    )
    dry_run: bool = Field(default=False)
    would_check_in: list[str] = Field(
        default_factory=list,
        description=(
            "On a dry run, one human-readable summary per checkout that "
            "would be checked in. Empty otherwise."
        ),
    )


class BulkRenewLoansResult(BaseModel):
    """Result of `renew_loans(...)`. Per-checkout success/failure breakdown."""

    renewed: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Map of checkout_id → new ISO due date for items that renewed successfully."
        ),
    )
    failures: dict[str, str] = Field(
        default_factory=dict,
        description="Checkout-id-keyed map of failure reasons.",
    )
    dry_run: bool = Field(default=False)
    would_renew: list[str] = Field(
        default_factory=list,
        description=(
            "On a dry run, one human-readable summary per checkout that "
            "would be renewed (title + current due date). Empty otherwise."
        ),
    )


class BulkBorrowDigitalResult(BaseModel):
    """Result of a multi-item `borrow_digital` call.

    No native bulk endpoint exists — the tool issues N sequential
    `POST /checkouts` calls with a small delay. Each row succeeds or
    fails independently.
    """

    borrowed: dict[str, BorrowDigitalResult] = Field(
        default_factory=dict,
        description="Map of bib_id → per-item borrow result.",
    )
    failures: dict[str, str] = Field(
        default_factory=dict,
        description="Bib-id-keyed map of failure reasons.",
    )


class BulkPlaceDigitalHoldResult(BaseModel):
    """Result of a multi-item `place_digital_hold` call.

    Same shape pattern as `BulkPlaceHoldResult` but for the Libby
    waitlist (`POST /holds` with `materialType: DIGITAL`). Sequential
    calls with inter-call delay; per-bib failures don't stop the run.
    """

    placed: dict[str, PlaceHoldResult] = Field(
        default_factory=dict,
        description="Map of bib_id → per-item hold result.",
    )
    failures: dict[str, str] = Field(
        default_factory=dict,
        description="Bib-id-keyed map of failure reasons.",
    )


class BulkPlaceHoldResult(BaseModel):
    """Result of `place_holds(...)`. Per-bib success/failure breakdown.

    The gateway has no batch endpoint for placement, so this is N
    sequential POSTs with a small delay between each. Some may succeed
    while others fail (e.g. duplicate hold, item not holdable); the
    response is keyed by `bib_id` so the caller can act on each.
    """

    placed: dict[str, PlaceHoldResult] = Field(
        default_factory=dict,
        description="Successful placements, keyed by `bib_id`.",
    )
    failures: dict[str, str] = Field(
        default_factory=dict,
        description="Failed placements, keyed by `bib_id` → reason.",
    )
