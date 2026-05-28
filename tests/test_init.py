"""Tests for the interactive setup wizard. Inputs are monkeypatched, network
is mocked."""

from __future__ import annotations

import tomllib
from unittest.mock import MagicMock

import pytest

from bibliocommons_mcp import init as init_module
from bibliocommons_mcp.branches import Branch

# ---- helpers ----


class _Inputs:
    """Drives input() / getpass() with a queue of canned responses."""

    def __init__(self, lines):
        self._lines = list(lines)
        self.consumed = []

    def __call__(self, _prompt=""):
        if not self._lines:
            raise EOFError("test ran out of canned input")
        v = self._lines.pop(0)
        self.consumed.append(v)
        return v


@pytest.fixture
def fake_inputs(monkeypatch):
    """Returns a callable to set the next inputs. Patches both input + getpass."""
    holder: dict = {}

    def setup(lines):
        inputs = _Inputs(lines)
        monkeypatch.setattr("builtins.input", inputs)
        monkeypatch.setattr("getpass.getpass", inputs)
        holder["inputs"] = inputs
        return inputs

    return setup


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Point the wizard at a fresh tmp path."""
    cfg = tmp_path / "config.toml"
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_CONFIG", str(cfg))
    return cfg


def _mock_branches_resp(branches: dict) -> MagicMock:
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = {"entities": {"branches": branches}}
    return r


def _stub_client(branches: list[Branch]):
    """Return a callable that, when used as Client(...), produces a Client-like
    mock whose .authenticate succeeds and .branches.all returns the given list."""

    def factory(library):
        c = MagicMock()
        c.library = library
        c.authenticate = MagicMock(return_value=None)
        c.branches = MagicMock()
        c.branches.all.return_value = branches
        return c

    return factory


# ---- tests ----


def test_writes_minimum_config(fake_inputs, isolated_config, monkeypatch):
    """Happy path: pick library, card+PIN, no branch, no format."""
    branches = [Branch("LCY", "Lake City Branch"), Branch("CEN", "Central Library")]
    fake_inputs(
        [
            "seattle",  # subdomain
            "1234567890123",  # card
            "1234",  # pin (getpass)
            "",  # default pickup branch — skip
            "",  # default format — skip
            "",  # digital notification email — skip
            "y",  # confirm write
        ]
    )
    monkeypatch.setattr(
        init_module.httpx,
        "get",
        lambda *a, **kw: _mock_branches_resp(
            {b.code: {"code": b.code, "name": b.name} for b in branches}
        ),
    )
    monkeypatch.setattr(init_module, "Client", _stub_client(branches))

    rc = init_module.run()
    assert rc == 0
    assert isolated_config.exists()
    data = tomllib.loads(isolated_config.read_text())
    assert data["library"] == "seattle"
    assert data["credentials"]["card"] == "1234567890123"
    assert data["credentials"]["pin"] == "1234"
    assert "default_pickup_branch" not in data
    assert "default_format" not in data
    # mode 0600
    assert oct(isolated_config.stat().st_mode & 0o777) == "0o600"


def test_writes_full_config(fake_inputs, isolated_config, monkeypatch):
    branches = [Branch("LCY", "Lake City Branch"), Branch("CEN", "Central Library")]
    fake_inputs(
        [
            "seattle",  # subdomain
            "card",  # card
            "pin",  # pin
            "1",  # default pickup branch — pick #1 (LCY)
            "MUSIC_CD",  # default format
            "patron@example.com",  # digital notification email
            "y",  # confirm
        ]
    )
    monkeypatch.setattr(
        init_module.httpx,
        "get",
        lambda *a, **kw: _mock_branches_resp(
            {b.code: {"code": b.code, "name": b.name} for b in branches}
        ),
    )
    monkeypatch.setattr(init_module, "Client", _stub_client(branches))

    init_module.run()
    data = tomllib.loads(isolated_config.read_text())
    assert data["default_pickup_branch"] == "LCY"
    assert data["default_format"] == "MUSIC_CD"
    assert data["digital_notification_email"] == "patron@example.com"


def test_branch_pick_by_name(fake_inputs, isolated_config, monkeypatch):
    """Picking by 'lake city' should resolve to LCY."""
    branches = [Branch("LCY", "Lake City Branch"), Branch("CEN", "Central Library")]
    fake_inputs(
        [
            "seattle",
            "c",
            "p",
            "lake city",  # name-based pick
            "",  # skip format
            "",  # skip digital email
            "y",
        ]
    )
    monkeypatch.setattr(
        init_module.httpx,
        "get",
        lambda *a, **kw: _mock_branches_resp(
            {b.code: {"code": b.code, "name": b.name} for b in branches}
        ),
    )
    monkeypatch.setattr(init_module, "Client", _stub_client(branches))
    init_module.run()
    data = tomllib.loads(isolated_config.read_text())
    assert data["default_pickup_branch"] == "LCY"


def test_invalid_library_then_retry(fake_inputs, isolated_config, monkeypatch):
    """First subdomain returns 410 (e.g., NYPL), user retries with seattle."""
    branches = [Branch("LCY", "Lake City Branch")]
    fake_branches_json = {b.code: {"code": b.code, "name": b.name} for b in branches}

    def fake_get(url, *a, **kw):
        if "/nypl/" in url:
            r = MagicMock()
            r.status_code = 410
            r.json.return_value = {"error": {"meta": {"fullName": "NYPL"}}}
            return r
        return _mock_branches_resp(fake_branches_json)

    fake_inputs(
        [
            "nypl",  # first try — site disabled
            "seattle",  # retry
            "c",
            "p",
            "",  # skip branch
            "",  # skip format
            "",  # skip digital email
            "y",  # confirm
        ]
    )
    monkeypatch.setattr(init_module.httpx, "get", fake_get)
    monkeypatch.setattr(init_module, "Client", _stub_client(branches))
    init_module.run()
    data = tomllib.loads(isolated_config.read_text())
    assert data["library"] == "seattle"


def test_login_failure_then_retry(fake_inputs, isolated_config, monkeypatch):
    branches = [Branch("LCY", "Lake City Branch")]
    monkeypatch.setattr(
        init_module.httpx,
        "get",
        lambda *a, **kw: _mock_branches_resp(
            {b.code: {"code": b.code, "name": b.name} for b in branches}
        ),
    )

    # First Client() succeeds in construction but .authenticate raises;
    # second one succeeds.
    call_count = {"n": 0}

    def factory(library):
        call_count["n"] += 1
        c = MagicMock()
        c.library = library
        if call_count["n"] == 1:
            c.authenticate = MagicMock(side_effect=RuntimeError("bad PIN"))
        else:
            c.authenticate = MagicMock(return_value=None)
        c.branches = MagicMock()
        c.branches.all.return_value = branches
        return c

    monkeypatch.setattr(init_module, "Client", factory)

    fake_inputs(
        [
            "seattle",
            "card1",
            "wrong-pin",  # first attempt — fails
            "y",  # try again
            "card2",
            "right-pin",  # second attempt — succeeds
            "",  # skip branch
            "",  # skip format
            "",  # skip digital email
            "y",  # confirm
        ]
    )
    rc = init_module.run()
    assert rc == 0
    data = tomllib.loads(isolated_config.read_text())
    assert data["credentials"]["card"] == "card2"
    assert data["credentials"]["pin"] == "right-pin"


def test_existing_config_keep(fake_inputs, isolated_config, monkeypatch):
    isolated_config.parent.mkdir(parents=True, exist_ok=True)
    isolated_config.write_text(
        'library = "previous"\n[credentials]\ncard = "old"\npin = "old"\n'
    )
    fake_inputs(["n"])  # don't overwrite
    rc = init_module.run()
    assert rc == 0
    # file untouched
    data = tomllib.loads(isolated_config.read_text())
    assert data["library"] == "previous"


def test_user_aborts_at_final_confirm(fake_inputs, isolated_config, monkeypatch):
    branches = [Branch("LCY", "Lake City Branch")]
    monkeypatch.setattr(
        init_module.httpx,
        "get",
        lambda *a, **kw: _mock_branches_resp(
            {b.code: {"code": b.code, "name": b.name} for b in branches}
        ),
    )
    monkeypatch.setattr(init_module, "Client", _stub_client(branches))
    fake_inputs(
        [
            "seattle",
            "c",
            "p",
            "",  # skip branch
            "",  # skip format
            "",  # skip digital email
            "n",  # don't write
        ]
    )
    rc = init_module.run()
    assert rc == 1
    assert not isolated_config.exists()
