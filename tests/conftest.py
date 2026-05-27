"""Shared test fixtures.

VCR is used for HTTP integration tests. Cassettes live in
`tests/cassettes/` and replay deterministically in CI with no network.

To re-record cassettes, run:
    BIBLIOCOMMONS_RECORD_CASSETTES=1 pytest tests/

Sensitive headers/cookies/body fields are sanitized before write — see
the `_scrub_*` helpers below. Always diff the cassettes after recording
to ensure nothing sensitive leaked through.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
import vcr

CASSETTE_DIR = Path(__file__).parent / "cassettes"
RECORD_MODE = "all" if os.environ.get("BIBLIOCOMMONS_RECORD_CASSETTES") else "none"


# ---- VCR sanitization ----

_FAKE_CARD = "1000000000000"
_FAKE_PIN = "0000"

# Headers whose values authenticate the requestor.
# Request side: we replace whole-header values with "REDACTED".
# Response Set-Cookie: we keep cookie structure but replace each value,
# because python-bibliocommons reads bc_access_token / session_id back out
# of the cookie jar after login — wiping them breaks replay.
_REQ_AUTH_HEADERS = ("cookie", "x-access-token", "x-session-id", "authorization")
_FAKE_ACCESS_TOKEN = "00000000-0000-0000-0000-000000000000"
_FAKE_SESSION_ID = "00000000-0000-0000-0000-000000000000-1142365317"


def _scrub_set_cookie_value(raw: str) -> str:
    """Replace cookie *values* but keep names so the jar still parses them."""
    raw = re.sub(r"bc_access_token=[^;]*", f"bc_access_token={_FAKE_ACCESS_TOKEN}", raw)
    raw = re.sub(
        r"(?<![A-Za-z_])session_id=[^;]*", f"session_id={_FAKE_SESSION_ID}", raw
    )
    raw = re.sub(r"_live_bcui_session_id=[^;]*", "_live_bcui_session_id=REDACTED", raw)
    raw = re.sub(r"remember_me=[^;]*", "remember_me=REDACTED", raw)
    return raw


def _scrub_request(request):
    """Strip auth headers + login credentials from recorded requests."""
    for key in list(request.headers.keys()):
        if key.lower() in _REQ_AUTH_HEADERS:
            request.headers[key] = "REDACTED"
    if request.body:
        body = (
            request.body.decode("utf-8", errors="ignore")
            if isinstance(request.body, bytes)
            else request.body
        )
        body = re.sub(r"name=[^&]+", f"name={_FAKE_CARD}", body)
        body = re.sub(r"user_pin=[^&]+", f"user_pin={_FAKE_PIN}", body)
        request.body = body.encode() if isinstance(request.body, bytes) else body
    return request


def _scrub_response(response):
    """Replace auth-cookie values in Set-Cookie response headers, preserving
    the cookie names so playback still populates the jar."""
    headers = response.get("headers", {})
    for key in list(headers.keys()):
        if key.lower() == "set-cookie":
            values = headers[key]
            if isinstance(values, list):
                headers[key] = [_scrub_set_cookie_value(v) for v in values]
            elif isinstance(values, str):
                headers[key] = _scrub_set_cookie_value(values)
    return response


@pytest.fixture
def cassette(request):
    """Use a per-test cassette under tests/cassettes/{test_name}.yaml."""
    name = request.node.name
    path = CASSETTE_DIR / f"{name}.yaml"
    my_vcr = vcr.VCR(
        cassette_library_dir=str(CASSETTE_DIR),
        record_mode=RECORD_MODE,
        match_on=("method", "scheme", "host", "port", "path", "query"),
        before_record_request=_scrub_request,
        before_record_response=_scrub_response,
        decode_compressed_response=True,
    )
    with my_vcr.use_cassette(str(path)):
        yield path


@pytest.fixture
def sample_config(tmp_path, monkeypatch):
    """Write a sample config to a tmp dir + point the loader at it."""
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        f"""
library = "seattle"
default_pickup_branch = "Lake City"
default_format = "MUSIC_CD"

[credentials]
card = "{_FAKE_CARD}"
pin = "{_FAKE_PIN}"
""".strip()
    )
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_CONFIG", str(cfg))
    return cfg
