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


# ─────────────────────────────── tool results ───────────────────────────────


class SearchResult(BaseModel):
    """Paginated search results. Page size is fixed at 25 by the gateway."""

    page: int | None = Field(default=None, description="1-indexed current page.")
    pages: int | None = Field(default=None, description="Total page count.")
    total: int | None = Field(default=None, description="Total matching bibs.")
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
    material_type: str | None = Field(
        default=None, description="'PHYSICAL' or 'DIGITAL'."
    )
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


class HoldList(BaseModel):
    count: int
    holds: list[Hold] = Field(default_factory=list)


class Loan(BaseModel):
    """One current checkout on the user's account."""

    checkout_id: str
    metadata_id: str | None = Field(default=None)
    title: str | None = Field(default=None)
    material_type: str | None = Field(default=None)
    due: str | None = Field(default=None, description="ISO date due back.")
    call_number: str | None = Field(default=None)
    branch: str | None = Field(default=None)


class LoanList(BaseModel):
    count: int
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


class CancelHoldResult(BaseModel):
    success: bool
    dry_run: bool = Field(
        default=False,
        description=(
            "If true, nothing was actually cancelled — the tool was called "
            "with dry_run=True and only describes what would happen."
        ),
    )
    would_cancel: str | None = Field(
        default=None,
        description=(
            "On a dry run, a human-readable summary of the hold that would "
            "be cancelled (title + queue position). None when dry_run=False."
        ),
    )
    failures: dict[str, str] = Field(
        default_factory=dict,
        description="Hold-id-keyed map of failure reasons. Empty on full success.",
    )
