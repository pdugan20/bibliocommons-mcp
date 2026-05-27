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


def test_search_uses_format_facet_and_page(client):
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
