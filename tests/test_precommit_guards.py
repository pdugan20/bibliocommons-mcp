"""Self-test for the credential-leak pre-commit hook.

``.pre-commit-config.yaml`` ships a pygrep hook that fails any commit
containing strings that look like a card/PIN/access-token leak. The
hook is the first line of defense against accidentally committing
credentials — but it only matters if it actually catches what we
think it catches. This file tests the regex behaves as advertised.

Test strings are built at runtime from harmless components (field
names + clearly-fake hex like ``deadbeef``) rather than being
literal credential-shaped strings in the source — that way the
source file doesn't itself contain anything an outside scanner
would flag.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
PRECOMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"


def _load_guard_regex() -> re.Pattern[str]:
    """Pull the credential-leak regex out of .pre-commit-config.yaml.

    Fails the test loudly if the hook isn't present — that means
    someone removed the guard, and the test should call attention.
    """
    cfg = yaml.safe_load(PRECOMMIT_CONFIG.read_text())
    for repo in cfg.get("repos", []):
        for hook in repo.get("hooks", []):
            if hook.get("id") == "block-credentials":
                return re.compile(hook["entry"])
    raise AssertionError(
        "block-credentials hook not found in .pre-commit-config.yaml — "
        "the credential-leak guard has been removed"
    )


def _shaped(field: str, value: str, sep: str = "=") -> str:
    """Build a string that should look credential-shaped to the regex.

    Caller passes the field name and a harmless hex value (e.g. 'deadbeef').
    Returns ``<field> <sep> "<value>"`` — the shape the hook looks for.
    """
    return f'{field} {sep} "{value}"'


# Fields the hook is meant to catch
SENSITIVE_FIELDS = (
    "card",
    "pin",
    "barcode",
    "password",
    "bc_access_token",
    "x-access-token",
    "session_id",
)


@pytest.fixture(scope="module")
def guard() -> re.Pattern[str]:
    return _load_guard_regex()


@pytest.mark.parametrize("field", SENSITIVE_FIELDS)
def test_guard_matches_each_sensitive_field(field: str, guard: re.Pattern[str]):
    """Every field name we promised to catch should match when given a
    quoted hex value of 4+ chars."""
    sample = _shaped(field, "deadbeef")
    assert guard.search(sample), (
        f"guard failed to match field {field!r} — credential-leak protection "
        "is broken for that field"
    )


def test_guard_matches_when_using_colon_separator(guard: re.Pattern[str]):
    """TOML-style ``card: \"...\"`` should also match (the hook regex
    accepts ``:`` and ``=`` separators interchangeably)."""
    sample = _shaped("card", "feedface", sep=":")
    assert guard.search(sample)


def test_guard_is_case_insensitive(guard: re.Pattern[str]):
    """Field names should match regardless of case."""
    assert guard.search(_shaped("CARD", "cafef00d"))
    assert guard.search(_shaped("Pin", "cafef00d"))
    assert guard.search(_shaped("BC_ACCESS_TOKEN", "cafef00d"))


def test_guard_ignores_too_short_values(guard: re.Pattern[str]):
    """The regex requires 4+ hex chars between the quotes; ``"ab"`` shouldn't
    trip it. Prevents false positives on short config values."""
    short = _shaped("card", "ab")
    assert not guard.search(short)


def test_guard_ignores_unrelated_field_names(guard: re.Pattern[str]):
    """Words we don't promise to catch shouldn't match, even with a
    sensitive-looking value."""
    sample = _shaped("library", "deadbeef")
    assert not guard.search(sample)


def test_guard_ignores_unquoted_values(guard: re.Pattern[str]):
    """The hook only fires on ``field = "value"`` shape, not bare
    assignments — comments and prose mentioning a field name should
    pass through."""
    assert not guard.search("card = deadbeef")
    assert not guard.search("# remember to set the card field")


def test_guard_ignores_non_hex_values(guard: re.Pattern[str]):
    """The regex requires ``[0-9a-f]+`` between the quotes, so a quoted
    word like ``card = \"some-name\"`` shouldn't match."""
    assert not guard.search(_shaped("card", "REDACTED"))
    assert not guard.search(_shaped("card", "xxxxxxxx"))


def test_hook_excludes_tests_and_docs(guard: re.Pattern[str]):
    """The hook's `exclude` block lists paths where credential-shaped
    strings are allowed (cassettes, this very file, etc.). Verify those
    entries exist so a future edit doesn't silently let leaks through
    the tests/ tree."""
    cfg = yaml.safe_load(PRECOMMIT_CONFIG.read_text())
    for repo in cfg.get("repos", []):
        for hook in repo.get("hooks", []):
            if hook.get("id") == "block-credentials":
                exclude = hook.get("exclude", "")
                assert "cassettes" in exclude, "cassettes must be excluded"
                assert "conftest" in exclude, "conftest must be excluded"
                return
