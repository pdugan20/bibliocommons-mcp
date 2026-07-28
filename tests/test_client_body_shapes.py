"""Verify the body shapes the client builds for state-changing endpoints.

These don't hit the network. We assert the exact JSON shape that gets
POSTed to the gateway, since the shape was painstakingly discovered
during the spike (`errorMessageLocale` is required, etc.).
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from bibliocommons_mcp.client import BCError, Client


@pytest.fixture
def client():
    """A Client with a mocked HTTPX client and forced account_id."""
    c = Client("seattle")
    c._authed = True
    # account_id is a property reading from c._bc.account_id; patch it
    c._bc = MagicMock()
    c._bc.account_id = 1142365318
    c._bc.httpx_client = MagicMock()
    return c


def _last_post(client) -> tuple[str, dict, dict]:
    """Extract (url, body, headers) from the most recent http.post call."""
    call = client.http.post.call_args
    url = call.args[0]
    body = call.kwargs.get("json")
    headers = call.kwargs.get("headers") or {}
    return url, body, headers


def _last_request(client, method: str) -> tuple[str, dict, dict]:
    """Extract the most recent http.request call (used for DELETE)."""
    call = client.http.request.call_args
    # request(method, url, json=..., headers=...)
    assert call.args[0] == method
    url = call.args[1]
    body = call.kwargs.get("json")
    headers = call.kwargs.get("headers") or {}
    return url, body, headers


def _mock_response(client, *, status: int = 200, body: dict | None = None):
    """Set the next response from http.post / http.request / http.get."""
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = body or {}
    resp.text = json.dumps(body or {})
    client.http.post.return_value = resp
    client.http.request.return_value = resp
    client.http.get.return_value = resp
    return resp


def test_place_physical_hold_body_shape(client):
    _mock_response(
        client,
        body={"id": "S30C123", "entities": {"holds": {"H1": {}}}, "successCount": 1},
    )
    client.place_physical_hold("S30C123", "LCY")
    url, body, headers = _last_post(client)

    assert (
        url
        == "https://gateway.bibliocommons.com/v2/libraries/seattle/holds?locale=en-US"
    )
    # The shape that was painstakingly discovered:
    assert body == {
        "metadataId": "S30C123",
        "materialType": "PHYSICAL",
        "accountId": 1142365318,
        "enableSingleClickHolds": False,
        "materialParams": {
            "branchId": "LCY",
            "expiryDate": None,
            "errorMessageLocale": "en-US",
        },
    }
    # Origin + Referer required for CORS at the gateway
    assert headers["Origin"] == "https://seattle.bibliocommons.com"
    assert headers["Referer"] == "https://seattle.bibliocommons.com/"


def test_borrow_digital_uses_checkouts_endpoint(client):
    _mock_response(
        client, body={"id": "S30C999", "entities": {"checkouts": {"C1": {}}}}
    )
    client.borrow_digital("S30C999")
    url, body, _ = _last_post(client)

    assert (
        url
        == "https://gateway.bibliocommons.com/v2/libraries/seattle/checkouts?locale=en-US"
    )
    assert body == {
        "metadataId": "S30C999",
        "materialType": "DIGITAL",
        "accountId": 1142365318,
    }


def test_cancel_holds_uses_plural_array_body(client):
    _mock_response(client, body={"failures": {}})
    client.cancel_holds([("H1", "S30C111"), ("H2", "S30C222")])
    url, body, _ = _last_request(client, "DELETE")

    assert (
        url
        == "https://gateway.bibliocommons.com/v2/libraries/seattle/holds?locale=en-US"
    )
    # Note plural field names + arrays for both, even when canceling one
    assert body == {
        "accountId": 1142365318,
        "metadataIds": ["S30C111", "S30C222"],
        "holdIds": ["H1", "H2"],
        "errorMessageLocale": "en-US",
    }


def test_cancel_empty_raises(client):
    with pytest.raises(ValueError):
        client.cancel_holds([])


def test_renew_checkouts_uses_patch_with_action_flag(client):
    # Body shape captured verbatim from the seattle.bibliocommons.com
    # web UI on 2026-05-27. Notable: no `errorMessageLocale` field —
    # unlike `_post`/`_delete`, PATCH on the checkouts collection does
    # not require it, and adding it would be guessing.
    _mock_response(
        client,
        body={
            "failures": [],
            "entities": {
                "checkouts": {
                    "-3399081509618396918": {
                        "checkoutId": "-3399081509618396918",
                        "dueDate": "2026-06-17",
                        "timesRenewed": 1,
                    }
                }
            },
        },
    )
    client.renew_checkouts(["-3399081509618396918"])
    url, body, headers = _last_request(client, "PATCH")

    assert (
        url
        == "https://gateway.bibliocommons.com/v2/libraries/seattle/checkouts?locale=en-US"
    )
    assert body == {
        "accountId": 1142365318,
        "checkoutIds": ["-3399081509618396918"],
        "renew": True,
    }
    # No errorMessageLocale in body — match wire exactly.
    assert "errorMessageLocale" not in body
    assert headers["Origin"] == "https://seattle.bibliocommons.com"


def test_renew_checkouts_bulk_grows_array(client):
    _mock_response(client, body={"failures": [], "entities": {"checkouts": {}}})
    client.renew_checkouts(["A1", "B2", "C3"])
    _url, body, _h = _last_request(client, "PATCH")
    assert body == {
        "accountId": 1142365318,
        "checkoutIds": ["A1", "B2", "C3"],
        "renew": True,
    }


def test_renew_empty_raises(client):
    with pytest.raises(ValueError):
        client.renew_checkouts([])


def test_place_digital_hold_body_shape(client):
    # Body shape captured verbatim from the seattle.bibliocommons.com
    # web UI on 2026-05-27. Same /holds POST as physical holds but
    # with materialType=DIGITAL and materialParams.email instead of
    # branchId. The gateway requires errorMessageLocale inside
    # materialParams (the /holds family quirk).
    _mock_response(
        client,
        body={
            "id": "S30C3007805",
            "entities": {"holds": {"H_DIGITAL": {"holdsPosition": 1}}},
            "successCount": 1,
        },
    )
    client.place_digital_hold("S30C3007805", "patron@example.com")
    url, body, headers = _last_post(client)

    assert (
        url
        == "https://gateway.bibliocommons.com/v2/libraries/seattle/holds?locale=en-US"
    )
    assert body == {
        "metadataId": "S30C3007805",
        "materialType": "DIGITAL",
        "accountId": 1142365318,
        "enableSingleClickHolds": False,
        "materialParams": {
            "email": "patron@example.com",
            "errorMessageLocale": "en-US",
        },
    }
    # No `format` enum — bibs with `requiresFormatDuringHold: false`
    # (the common case) don't need it. If we hit a bib that requires
    # format we'll add it then.
    assert "format" not in body
    assert headers["Origin"] == "https://seattle.bibliocommons.com"


def test_check_in_loan_per_resource_delete(client):
    # Body shape captured verbatim from the seattle.bibliocommons.com
    # web UI on 2026-05-27. Per-resource DELETE — NOT the bulk PATCH
    # that renew uses. Body is `{metadataId, accountId}`; no
    # errorMessageLocale (unlike /holds endpoints).
    _mock_response(client, body={"id": "S30C2636037"})
    client.check_in_loan("1477017860", "S30C2636037")
    url, body, headers = _last_request(client, "DELETE")

    assert (
        url
        == "https://gateway.bibliocommons.com/v2/libraries/seattle/checkouts/1477017860?locale=en-US"
    )
    assert body == {
        "metadataId": "S30C2636037",
        "accountId": 1142365318,
    }
    # No errorMessageLocale — match wire exactly. The /holds endpoints
    # enforce it via `_post`/`_delete`; `/checkouts` endpoints don't.
    assert "errorMessageLocale" not in body
    assert headers["Origin"] == "https://seattle.bibliocommons.com"


def test_gateway_5xx_raises_bcerror(client):
    _mock_response(
        client, status=500, body={"error": {"message": "Internal Server Error"}}
    )
    with pytest.raises(BCError) as exc:
        client.place_physical_hold("S30C123", "LCY")
    assert exc.value.status == 500
    assert "Internal Server Error" in exc.value.message


def test_gateway_422_surfaces_message(client):
    _mock_response(
        client,
        status=422,
        body={
            "error": {
                "message": "Required parameters: metadataIds, holdIds",
                "classification": "ValidationError",
            }
        },
    )
    with pytest.raises(BCError) as exc:
        client.cancel_holds([("H1", "S30C111")])
    assert exc.value.status == 422
    assert "Required parameters" in exc.value.message
    assert exc.value.classification == "ValidationError"


def test_search_delegates_to_base_library_when_supported(client, monkeypatch):
    """When python-bibliocommons >= 2026.1, search() delegates to search_gateway."""
    monkeypatch.setattr(
        "bibliocommons_mcp.client._base_supports_gateway", lambda: True
    )
    _mock_response(
        client, body={"entities": {"bibs": {}}, "catalogSearch": {"pagination": {}}}
    )
    client._bc.search_gateway = MagicMock(
        return_value={"entities": {"bibs": {}}, "catalogSearch": {"pagination": {}}}
    )
    client.search("weezer", format="MUSIC_CD", page=2, sort_by="newly_acquired")
    call = client._bc.search_gateway.call_args
    assert call.args[0] == "weezer"
    assert call.kwargs["format"] == "MUSIC_CD"
    assert call.kwargs["page"] == 2
    assert call.kwargs["sort_by"] == "newly_acquired"


def test_search_falls_back_when_base_library_too_old(client, monkeypatch):
    """Older python-bibliocommons uses the inline gateway call."""
    monkeypatch.setattr(
        "bibliocommons_mcp.client._base_supports_gateway", lambda: False
    )
    _mock_response(
        client, body={"entities": {"bibs": {}}, "catalogSearch": {"pagination": {}}}
    )
    client.search("weezer", format="MUSIC_CD", page=2, sort_by="newly_acquired")
    call = client.http.get.call_args
    assert (
        call.args[0]
        == "https://gateway.bibliocommons.com/v2/libraries/seattle/bibs/search"
    )
    params = call.kwargs["params"]
    assert params["query"] == "weezer"
    assert params["searchType"] == "keyword"
    assert params["f_FORMAT"] == "MUSIC_CD"
    assert params["page"] == 2
    assert params["sortBy"] == "newly_acquired"


def test_search_available_only_always_uses_inline(client, monkeypatch):
    """available_only is not supported by search_gateway; always use inline."""
    monkeypatch.setattr(
        "bibliocommons_mcp.client._base_supports_gateway", lambda: True
    )
    _mock_response(
        client, body={"entities": {"bibs": {}}, "catalogSearch": {"pagination": {}}}
    )
    client._bc.search_gateway = MagicMock()
    client.search("weezer", available_only=True)
    # Must NOT have called search_gateway
    assert not client._bc.search_gateway.called
    call = client.http.get.call_args
    assert "f_NEWLY_ACQUIRED" in call.kwargs["params"]


def test_availability_delegates_to_base_library_when_supported(client, monkeypatch):
    """When python-bibliocommons >= 2026.1, availability() delegates."""
    monkeypatch.setattr(
        "bibliocommons_mcp.client._base_supports_gateway", lambda: True
    )
    client._bc.get_availability_raw = MagicMock(
        return_value={"entities": {"bibs": {}}}
    )
    client.availability("S126C1872927")
    client._bc.get_availability_raw.assert_called_once_with("S126C1872927")


def test_availability_falls_back_when_base_library_too_old(client, monkeypatch):
    """Older python-bibliocommons uses the inline gateway call."""
    monkeypatch.setattr(
        "bibliocommons_mcp.client._base_supports_gateway", lambda: False
    )
    _mock_response(client, body={"entities": {"bibs": {}}})
    client.availability("S126C1872927")
    call = client.http.get.call_args
    assert call.args[0] == (
        "https://gateway.bibliocommons.com/v2/libraries/seattle"
        "/bibs/S126C1872927/availability"
    )
