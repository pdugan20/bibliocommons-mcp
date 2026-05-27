"""Tests for the MCP tool wrappers in server.py.

These mock the Client to isolate the response-shaping logic in each
tool. Network is never touched. Tools now return Pydantic models —
assertions use attribute access.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from mcp.server.fastmcp.exceptions import ToolError

import bibliocommons_mcp.server as srv
from bibliocommons_mcp.branches import Branch


@pytest.fixture
def mock_client(monkeypatch):
    """Replace the module's lazy client + config with mocks."""
    client = MagicMock()
    client.library = "seattle"
    client.account_id = 1142365318

    cfg = MagicMock()
    cfg.library = "seattle"
    cfg.default_pickup_branch = "Lake City"
    cfg.default_format = None

    monkeypatch.setattr(srv, "_client", client)
    monkeypatch.setattr(srv, "_cfg", cfg)
    return client


def test_search_compresses_response(mock_client):
    mock_client.search.return_value = {
        "entities": {
            "bibs": {
                "S30C1": {
                    "id": "S30C1",
                    "briefInfo": {
                        "title": "Plastic Eternity",
                        "authors": ["Mudhoney"],
                        "format": "MUSIC_CD",
                        "publicationDate": "2023",
                        "callNumber": "CD ABC",
                    },
                }
            }
        },
        "catalogSearch": {"pagination": {"page": 1, "pages": 1, "count": 1}},
    }
    out = srv.search("mudhoney", format="MUSIC_CD")
    assert out.page == 1
    assert out.total == 1
    assert out.results[0].title == "Plastic Eternity"
    assert out.results[0].format == "MUSIC_CD"
    mock_client.search.assert_called_once_with(
        "mudhoney", format="MUSIC_CD", page=1, sort_by=None
    )


def test_search_uses_default_format(mock_client, monkeypatch):
    cfg = MagicMock()
    cfg.default_format = "BK"
    monkeypatch.setattr(srv, "_cfg", cfg)
    mock_client.search.return_value = {
        "entities": {"bibs": {}},
        "catalogSearch": {"pagination": {}},
    }
    srv.search("anything")
    assert mock_client.search.call_args.kwargs["format"] == "BK"


def test_availability_flattens_per_copy(mock_client):
    mock_client.availability.return_value = {
        "availability": {"digitalFormats": []},
        "entities": {
            "availabilities": {
                "S30C9": {
                    "totalCopies": 3,
                    "availableCopies": 2,
                    "heldCopies": 1,
                    "status": "AVAILABLE",
                }
            },
            "bibItems": {
                "i1": {
                    "branch": {"code": "LCY", "name": "Lake City Branch"},
                    "availability": {
                        "status": "AVAILABLE",
                        "libraryStatus": "Checked In",
                    },
                    "callNumber": "CD ABC",
                    "collection": "Music CDs",
                },
                "i2": {
                    "branch": {"code": "CEN", "name": "Central Library"},
                    "availability": {"status": "CHECKED_OUT", "libraryStatus": "Out"},
                    "callNumber": "CD ABC",
                    "collection": "Music CDs",
                },
            },
        },
    }
    out = srv.availability("S30C9")
    assert out.total_copies == 3
    assert out.available_copies == 2
    assert len(out.copies) == 2
    assert out.copies[0].branch_code in {"LCY", "CEN"}


def test_place_hold_default_branch(mock_client):
    mock_client.branches.resolve.return_value = Branch(
        code="LCY", name="Lake City Branch"
    )
    mock_client.place_physical_hold.return_value = {
        "id": "S30C1",
        "entities": {
            "holds": {
                "H1": {
                    "bibTitle": "Plastic Eternity",
                    "materialType": "PHYSICAL",
                    "pickupLocation": {"code": "LCY"},
                    "holdsPosition": 1,
                    "status": "NOT_YET_AVAILABLE",
                    "expiryDate": "2027-03-03",
                }
            }
        },
    }
    out = srv.place_hold("S30C1")
    assert out.success is True
    assert out.hold_id == "H1"
    assert out.pickup_branch == "LCY"
    mock_client.branches.resolve.assert_called_once_with("Lake City")
    mock_client.place_physical_hold.assert_called_once_with("S30C1", "LCY")


def test_place_hold_explicit_branch(mock_client):
    mock_client.branches.resolve.return_value = Branch(
        code="CEN", name="Central Library"
    )
    mock_client.place_physical_hold.return_value = {
        "entities": {
            "holds": {
                "H2": {
                    "bibTitle": "x",
                    "materialType": "PHYSICAL",
                    "pickupLocation": {"code": "CEN"},
                    "holdsPosition": 1,
                    "status": "NOT_YET_AVAILABLE",
                }
            }
        }
    }
    srv.place_hold("S30C1", pickup_branch="Central")
    mock_client.branches.resolve.assert_called_once_with("Central")


def test_place_hold_with_no_branch_or_default_raises(mock_client, monkeypatch):
    cfg = MagicMock()
    cfg.default_pickup_branch = None
    monkeypatch.setattr(srv, "_cfg", cfg)
    # _resolve_branch now raises ToolError directly (was ValueError before).
    with pytest.raises(ToolError, match="pickup_branch"):
        srv.place_hold("S30C1")


def test_place_hold_unknown_branch_surfaces_as_tool_error(mock_client):
    """BranchNotFound from the resolver gets wrapped in ToolError by _safe."""
    from bibliocommons_mcp.branches import BranchNotFound

    mock_client.branches.resolve.side_effect = BranchNotFound("no match")
    with pytest.raises(ToolError, match="no match"):
        srv.place_hold("S30C1", pickup_branch="Hogwarts")


def test_borrow_digital_shape(mock_client):
    mock_client.borrow_digital.return_value = {
        "id": "S30C5",
        "entities": {
            "checkouts": {
                "C1": {
                    "bibTitle": "Come as You Are",
                    "materialType": "DIGITAL",
                    "dueDate": "2026-06-17",
                    "callNumber": "EAUDIO OVERDRIVE",
                    "volume": "Unabridged",
                }
            }
        },
    }
    out = srv.borrow_digital("S30C5")
    assert out.success is True
    assert out.title == "Come as You Are"
    assert out.due == "2026-06-17"


def test_list_holds_shape(mock_client):
    mock_client.list_holds.return_value = {
        "entities": {
            "holds": {
                "H1": {
                    "metadataId": "S30C1",
                    "bibTitle": "x",
                    "materialType": "PHYSICAL",
                    "status": "NOT_YET_AVAILABLE",
                    "holdsPosition": 1,
                    "pickupLocation": {"code": "LCY"},
                    "holdPlacedDate": "2026-05-27",
                    "expiryDate": "2027-03-03",
                }
            }
        }
    }
    out = srv.list_holds()
    assert out.count == 1
    assert out.holds[0].pickup_branch == "LCY"


def test_cancel_hold_returns_success_when_no_failures(mock_client):
    mock_client.cancel_holds.return_value = {"failures": {}}
    out = srv.cancel_hold("H1", "S30C1")
    assert out.success is True
    assert out.dry_run is False
    mock_client.cancel_holds.assert_called_once_with([("H1", "S30C1")])


def test_cancel_hold_surfaces_failures(mock_client):
    mock_client.cancel_holds.return_value = {"failures": {"H1": "already canceled"}}
    out = srv.cancel_hold("H1", "S30C1")
    assert out.success is False
    assert "H1" in out.failures


def test_cancel_hold_dry_run_does_not_call_cancel(mock_client):
    """dry_run=True should look up the hold via list_holds and return what
    would be cancelled, never calling cancel_holds."""
    mock_client.list_holds.return_value = {
        "entities": {
            "holds": {
                "H1": {
                    "bibTitle": "Plastic Eternity",
                    "holdsPosition": 3,
                    "materialType": "PHYSICAL",
                },
            }
        }
    }
    out = srv.cancel_hold("H1", "S30C1", dry_run=True)
    assert out.success is True
    assert out.dry_run is True
    assert out.would_cancel is not None
    assert "Plastic Eternity" in out.would_cancel
    assert "position 3" in out.would_cancel
    mock_client.cancel_holds.assert_not_called()


def test_cancel_hold_dry_run_reports_missing_hold(mock_client):
    mock_client.list_holds.return_value = {"entities": {"holds": {}}}
    out = srv.cancel_hold("NOPE", "S30C1", dry_run=True)
    assert out.success is False
    assert out.dry_run is True
    assert "NOPE" in out.failures
    mock_client.cancel_holds.assert_not_called()


def test_list_loans_shape(mock_client):
    mock_client.list_loans.return_value = {
        "entities": {
            "checkouts": {
                "C1": {
                    "metadataId": "S30C1",
                    "bibTitle": "Everybody Loves Our Town",
                    "materialType": "DIGITAL",
                    "dueDate": "2026-06-11",
                    "callNumber": "EBOOK OVERDRIVE",
                    "branch": None,
                }
            }
        }
    }
    out = srv.list_loans()
    assert out.count == 1
    assert out.loans[0].due == "2026-06-11"


def test_list_branches(mock_client):
    mock_client.branches.all.return_value = [
        Branch("LCY", "Lake City Branch"),
        Branch("CEN", "Central Library"),
    ]
    out = srv.list_branches()
    assert out.library == "seattle"
    assert len(out.branches) == 2
    assert out.branches[0].code == "LCY"
    assert out.branches[0].name == "Lake City Branch"


def test_library_health_unlimited_ils(mock_client):
    """SPL doesn't surface an ILS quota — we report unlimited."""
    from bibliocommons_mcp.client import HoldQuotas

    mock_client.hold_quotas.return_value = HoldQuotas(0, 0, 3, 10)
    mock_client.list_holds.return_value = {
        "entities": {
            "holds": {
                "H1": {"materialType": "PHYSICAL"},
                "H2": {"materialType": "PHYSICAL"},
                "H3": {"materialType": "DIGITAL"},
                "H4": {"materialType": "DIGITAL"},
                "H5": {"materialType": "DIGITAL"},
            }
        }
    }
    out = srv.library_health()
    assert out.physical_holds == "2/unlimited"
    assert out.digital_holds == "3/10"
    assert out.logged_in is True
    assert out.library == "seattle"


def test_bcerror_from_gateway_surfaces_as_tool_error(mock_client):
    """Gateway errors should turn into ToolError, not propagate raw BCError."""
    from bibliocommons_mcp.client import BCError

    mock_client.list_holds.side_effect = BCError(500, "Internal Server Error")
    with pytest.raises(ToolError, match="Internal Server Error"):
        srv.list_holds()
