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


def test_place_holds_bulk_success(mock_client):
    """Bulk placement should call place_physical_hold once per bib and
    return a per-bib map of PlaceHoldResults."""
    mock_client.branches.resolve.return_value = Branch(code="LCY", name="Lake City")

    def fake_place(bib_id, branch_code):
        return {
            "entities": {
                "holds": {
                    f"H_{bib_id}": {
                        "bibTitle": f"Title for {bib_id}",
                        "materialType": "PHYSICAL",
                        "pickupLocation": {"code": branch_code},
                        "holdsPosition": 1,
                        "status": "NOT_YET_AVAILABLE",
                    }
                }
            }
        }

    mock_client.place_physical_hold.side_effect = fake_place

    out = srv.place_holds(bib_ids=["S30C1", "S30C2", "S30C3"], delay_seconds=0.0)
    assert out.failures == {}
    assert set(out.placed.keys()) == {"S30C1", "S30C2", "S30C3"}
    assert all(r.success for r in out.placed.values())
    assert mock_client.place_physical_hold.call_count == 3


def test_place_holds_bulk_partial_failure(mock_client):
    """When one bib 409s, the others should still complete and the
    failure should land in `failures`."""
    from bibliocommons_mcp.client import BCError

    mock_client.branches.resolve.return_value = Branch(code="LCY", name="Lake City")

    def fake_place(bib_id, branch_code):
        if bib_id == "S30C_DUP":
            raise BCError(409, "This item is already on your holds list.")
        return {
            "entities": {
                "holds": {
                    "H1": {
                        "bibTitle": "ok",
                        "materialType": "PHYSICAL",
                        "pickupLocation": {"code": branch_code},
                        "holdsPosition": 1,
                        "status": "NOT_YET_AVAILABLE",
                    }
                }
            }
        }

    mock_client.place_physical_hold.side_effect = fake_place

    out = srv.place_holds(
        bib_ids=["S30C_OK", "S30C_DUP", "S30C_ALSO_OK"], delay_seconds=0.0
    )
    assert set(out.placed.keys()) == {"S30C_OK", "S30C_ALSO_OK"}
    assert "S30C_DUP" in out.failures
    assert "already on your holds list" in out.failures["S30C_DUP"]


def test_place_holds_applies_delay_between_calls(mock_client, monkeypatch):
    """The tool should call time.sleep(delay_seconds) between bibs, but
    not before the first one or after the last."""
    sleeps: list[float] = []
    monkeypatch.setattr(srv.time, "sleep", lambda s: sleeps.append(s))

    mock_client.branches.resolve.return_value = Branch(code="LCY", name="Lake City")
    mock_client.place_physical_hold.return_value = {
        "entities": {
            "holds": {
                "H": {
                    "bibTitle": "x",
                    "materialType": "PHYSICAL",
                    "pickupLocation": {"code": "LCY"},
                    "holdsPosition": 1,
                    "status": "NOT_YET_AVAILABLE",
                }
            }
        }
    }

    srv.place_holds(bib_ids=["A", "B", "C"], delay_seconds=0.5)
    # 3 bibs → 2 sleeps (between, not before/after)
    assert sleeps == [0.5, 0.5]


def test_place_holds_empty_raises(mock_client):
    with pytest.raises(ToolError, match="empty"):
        srv.place_holds(bib_ids=[])


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
                    "actions": ["checkIn", "updateFormat"],
                    "timesRenewed": 0,
                },
                "C2": {
                    "metadataId": "S30C2",
                    "bibTitle": "Old Wood Boat",
                    "materialType": "PHYSICAL",
                    "dueDate": "2026-06-16",
                    "actions": ["renew", "updateFormat"],
                    "timesRenewed": 1,
                    "branch": {"code": "LCY", "name": "Lake City Branch"},
                },
            }
        }
    }
    out = srv.list_loans()
    assert out.count == 2
    by_id = {loan.checkout_id: loan for loan in out.loans}
    assert by_id["C1"].due == "2026-06-11"
    # Digital item: no "renew" in actions → model can pre-check before
    # calling renew_loan.
    assert "renew" not in by_id["C1"].actions
    assert by_id["C1"].times_renewed == 0
    # Physical item: renewable, branch code lifted from the nested object.
    assert "renew" in by_id["C2"].actions
    assert by_id["C2"].times_renewed == 1
    assert by_id["C2"].branch == "LCY"


def test_renew_loan_success(mock_client):
    mock_client.renew_checkouts.return_value = {
        "failures": [],
        "entities": {
            "checkouts": {
                "-3399081509618396918": {
                    "dueDate": "2026-06-17",
                    "timesRenewed": 1,
                }
            }
        },
    }
    out = srv.renew_loan("-3399081509618396918")
    assert out.success is True
    assert out.dry_run is False
    assert out.new_due == "2026-06-17"
    assert out.times_renewed == 1
    mock_client.renew_checkouts.assert_called_once_with(["-3399081509618396918"])


def test_renew_loan_dry_run_pre_checks_actions(mock_client):
    """dry_run uses the gateway's `actions` array to decide whether
    the call would even be allowed — no network call."""
    mock_client.list_loans.return_value = {
        "entities": {
            "checkouts": {
                "C_PHYSICAL": {
                    "bibTitle": "Old Wood Boat",
                    "dueDate": "2026-06-16",
                    "actions": ["renew", "updateFormat"],
                },
                "C_DIGITAL": {
                    "bibTitle": "An eBook",
                    "dueDate": "2026-06-11",
                    "actions": ["checkIn", "updateFormat"],
                },
            }
        }
    }
    ok = srv.renew_loan("C_PHYSICAL", dry_run=True)
    assert ok.success is True and ok.dry_run is True
    assert ok.would_renew is not None
    assert "Old Wood Boat" in ok.would_renew
    assert "2026-06-16" in ok.would_renew

    blocked = srv.renew_loan("C_DIGITAL", dry_run=True)
    assert blocked.success is False and blocked.dry_run is True
    assert "C_DIGITAL" in blocked.failures
    assert "renew" in blocked.failures["C_DIGITAL"]

    missing = srv.renew_loan("NOPE", dry_run=True)
    assert missing.success is False and missing.dry_run is True
    assert "NOPE" in missing.failures

    mock_client.renew_checkouts.assert_not_called()


def test_renew_loans_bulk_partial_failure(mock_client):
    """Bulk renewal where the gateway accepts one and rejects the other."""
    mock_client.renew_checkouts.return_value = {
        "failures": [{"checkoutId": "B2", "message": "Item has holds; cannot renew"}],
        "entities": {
            "checkouts": {
                "A1": {"dueDate": "2026-06-30", "timesRenewed": 2},
            }
        },
    }
    out = srv.renew_loans(["A1", "B2"])
    assert out.renewed == {"A1": "2026-06-30"}
    assert out.failures == {"B2": "Item has holds; cannot renew"}
    mock_client.renew_checkouts.assert_called_once_with(["A1", "B2"])


def test_renew_loans_empty_raises(mock_client):
    from mcp.server.fastmcp.exceptions import ToolError

    with pytest.raises(ToolError):
        srv.renew_loans([])


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


# ─────────────────────────────── jacket extraction ───────────────────────────────


_SAMPLE_JACKET = {
    "type": "SYNDETICS",
    "small": "https://example.com/SC.GIF",
    "medium": "https://example.com/MC.GIF",
    "large": "https://example.com/LC.JPG",
    "local_url": None,
}


def test_search_extracts_jacket(mock_client):
    mock_client.search.return_value = {
        "entities": {
            "bibs": {
                "S30C1": {
                    "id": "S30C1",
                    "briefInfo": {
                        "title": "Plastic Eternity",
                        "format": "MUSIC_CD",
                        "jacket": _SAMPLE_JACKET,
                    },
                }
            }
        },
        "catalogSearch": {"pagination": {}},
    }
    out = srv.search("mudhoney")
    j = out.results[0].jacket
    assert j is not None
    assert j.small == "https://example.com/SC.GIF"
    assert j.medium == "https://example.com/MC.GIF"
    assert j.large == "https://example.com/LC.JPG"


def test_list_holds_joins_jacket_from_entities_bibs(mock_client):
    """list_holds should pull jacket from entities.bibs[metadataId]."""
    mock_client.list_holds.return_value = {
        "entities": {
            "holds": {
                "H1": {
                    "metadataId": "S30C1",
                    "bibTitle": "Plastic Eternity",
                    "materialType": "PHYSICAL",
                    "status": "NOT_YET_AVAILABLE",
                }
            },
            "bibs": {
                "S30C1": {"briefInfo": {"jacket": _SAMPLE_JACKET}},
            },
        }
    }
    out = srv.list_holds()
    assert out.holds[0].jacket is not None
    assert out.holds[0].jacket.medium == "https://example.com/MC.GIF"


def test_list_holds_handles_missing_bibs_entity(mock_client):
    """If entities.bibs isn't present (older response shape), jacket=None."""
    mock_client.list_holds.return_value = {
        "entities": {
            "holds": {
                "H1": {
                    "metadataId": "S30C1",
                    "bibTitle": "x",
                    "materialType": "PHYSICAL",
                }
            }
        }
    }
    out = srv.list_holds()
    assert out.holds[0].jacket is None


# ─────────────────────────────── ready_for_pickup ───────────────────────────────


def test_ready_for_pickup_filters_by_status(mock_client):
    mock_client.list_holds.return_value = {
        "entities": {
            "holds": {
                "H1": {
                    "metadataId": "S30C1",
                    "bibTitle": "Ready One",
                    "materialType": "PHYSICAL",
                    "status": "READY_FOR_PICKUP",
                },
                "H2": {
                    "metadataId": "S30C2",
                    "bibTitle": "Still Waiting",
                    "materialType": "PHYSICAL",
                    "status": "NOT_YET_AVAILABLE",
                },
                "H3": {
                    "metadataId": "S30C3",
                    "bibTitle": "Ready Two",
                    "materialType": "PHYSICAL",
                    "status": "READY_FOR_PICKUP",
                },
            }
        }
    }
    out = srv.ready_for_pickup()
    assert out.count == 2
    titles = {h.title for h in out.holds}
    assert titles == {"Ready One", "Ready Two"}


def test_ready_for_pickup_returns_empty_when_none_ready(mock_client):
    mock_client.list_holds.return_value = {
        "entities": {
            "holds": {
                "H1": {
                    "metadataId": "S30C1",
                    "bibTitle": "x",
                    "materialType": "PHYSICAL",
                    "status": "NOT_YET_AVAILABLE",
                }
            }
        }
    }
    out = srv.ready_for_pickup()
    assert out.count == 0
    assert out.holds == []


# ─────────────────────────────── cancel_holds (bulk) ───────────────────────────────


def test_cancel_holds_bulk_success(mock_client):
    from bibliocommons_mcp.models import HoldRef

    mock_client.cancel_holds.return_value = {"failures": {}}
    out = srv.cancel_holds(
        [HoldRef(hold_id="H1", bib_id="S30C1"), HoldRef(hold_id="H2", bib_id="S30C2")]
    )
    assert sorted(out.cancelled) == ["H1", "H2"]
    assert out.failures == {}
    assert out.dry_run is False
    mock_client.cancel_holds.assert_called_once_with([("H1", "S30C1"), ("H2", "S30C2")])


def test_cancel_holds_bulk_partial_failure(mock_client):
    from bibliocommons_mcp.models import HoldRef

    mock_client.cancel_holds.return_value = {"failures": {"H2": "already gone"}}
    out = srv.cancel_holds(
        [HoldRef(hold_id="H1", bib_id="S30C1"), HoldRef(hold_id="H2", bib_id="S30C2")]
    )
    assert out.cancelled == ["H1"]
    assert out.failures == {"H2": "already gone"}


def test_cancel_holds_bulk_dry_run(mock_client):
    """dry_run=True should look up each hold and describe what would
    happen without calling cancel_holds on the client."""
    from bibliocommons_mcp.models import HoldRef

    mock_client.list_holds.return_value = {
        "entities": {
            "holds": {
                "H1": {"bibTitle": "Plastic Eternity", "holdsPosition": 3},
                "H2": {"bibTitle": "In Utero", "holdsPosition": 1},
            }
        }
    }
    out = srv.cancel_holds(
        [HoldRef(hold_id="H1", bib_id="S30C1"), HoldRef(hold_id="H2", bib_id="S30C2")],
        dry_run=True,
    )
    assert out.dry_run is True
    assert out.cancelled == []
    assert len(out.would_cancel) == 2
    joined = " ".join(out.would_cancel)
    assert "Plastic Eternity" in joined
    assert "In Utero" in joined
    mock_client.cancel_holds.assert_not_called()


def test_cancel_holds_empty_raises(mock_client):
    with pytest.raises(ToolError, match="empty"):
        srv.cancel_holds([])
