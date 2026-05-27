"""Interactive setup wizard.

Prompts for library subdomain, card, PIN, and default branch. Validates each
step against the live gateway, then writes ``~/.config/bibliocommons-mcp/config.toml``
with mode 0600.

Run via:

    bibliocommons-mcp init
"""

from __future__ import annotations

import getpass
import os
import sys
import tomllib
from pathlib import Path

import httpx

from .branches import Branch, Branches
from .client import Client
from .config import DEFAULT_CONFIG_PATH

GATEWAY = "https://gateway.bibliocommons.com"

# Curated examples shown at the subdomain prompt. The full list is ~190 — we
# don't enumerate it; we just hint at the format.
_EXAMPLE_LIBRARIES = ["seattle", "sfpl", "bpl", "vpl", "epl", "burnaby"]


def _say(msg: str = "") -> None:
    """Friendly stdout. The wizard is for users; stdout is fine here (unlike
    the MCP server, where stdout is reserved for protocol framing)."""
    print(msg)


def _ask(prompt: str, *, default: str | None = None) -> str:
    """Ask for a line of input. `default=None` means the field is required;
    any other value (including `""`) is treated as a default and accepts blank
    input."""
    suffix = f" [{default}]: " if default else ": "
    while True:
        try:
            value = input(prompt + suffix).strip()
        except (EOFError, KeyboardInterrupt):
            _say("\nAborted.")
            sys.exit(130)
        if value:
            return value
        if default is not None:
            return default
        _say("  (required — please enter a value)")


def _ask_secret(prompt: str) -> str:
    """Read a secret without echoing. Used for the PIN."""
    while True:
        try:
            value = getpass.getpass(prompt + ": ").strip()
        except (EOFError, KeyboardInterrupt):
            _say("\nAborted.")
            sys.exit(130)
        if value:
            return value
        _say("  (required — please enter a value)")


def _ask_yes_no(prompt: str, *, default: bool = True) -> bool:
    suffix = " [Y/n]: " if default else " [y/N]: "
    while True:
        try:
            value = input(prompt + suffix).strip().lower()
        except (EOFError, KeyboardInterrupt):
            _say("\nAborted.")
            sys.exit(130)
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        _say("  please answer y or n")


def _validate_library(subdomain: str) -> dict | None:
    """Hit /branches as an unauthenticated GET. Returns parsed entities on
    success, None on failure. Prints a helpful message either way."""
    url = f"{GATEWAY}/v2/libraries/{subdomain}/branches"
    try:
        r = httpx.get(url, timeout=15)
    except httpx.HTTPError as e:
        _say(f"  network error: {e}")
        return None
    if r.status_code == 410:
        meta = r.json().get("error", {}).get("meta", {})
        name = meta.get("fullName") or subdomain
        _say(f"  {name} is no longer on BiblioCommons. Sorry.")
        return None
    if r.status_code == 404:
        _say(f"  no BiblioCommons library found at '{subdomain}'.")
        _say(f"  check {subdomain}.bibliocommons.com in a browser.")
        return None
    if r.status_code != 200:
        _say(f"  unexpected response from gateway ({r.status_code}). Try again.")
        return None
    return r.json()


def _attempt_login(
    library: str, card: str, pin: str
) -> tuple[Client, list[Branch]] | None:
    """Try a real login. Returns (client, branch list) on success."""
    try:
        c = Client(library)
        c.authenticate(card, pin)
    except Exception as e:
        _say(f"  login failed: {type(e).__name__}: {e}")
        return None
    try:
        branches = c.branches.all()
    except Exception as e:
        _say(f"  login worked but couldn't fetch branches: {e}")
        return None
    return c, branches


def _pick_branch(branches: list[Branch]) -> str | None:
    """Print a numbered list and let the user pick by number or name.
    Returns the chosen branch CODE, or None if skipped."""
    if not branches:
        return None
    _say()
    _say("Branches at your library:")
    # Hide locker variants from the picker to reduce noise; users can still
    # type a locker code by hand if they really want one.
    visible = [b for b in branches if not b.code.startswith("LOCK")]
    for i, b in enumerate(visible, start=1):
        _say(f"  {i:>2}. {b.name} ({b.code})")
    _say()
    choice = _ask(
        "Default pickup branch (number, name, or code; leave blank to skip)", default=""
    )
    if not choice:
        return None
    # number?
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(visible):
            return visible[idx].code
        _say(f"  {choice} isn't in range, skipping.")
        return None
    # name/code via the resolver
    name_to_branch = Branches.__new__(Branches)
    name_to_branch._library = ""
    name_to_branch._http = None
    name_to_branch._by_code = {b.code: b for b in branches}
    try:
        return name_to_branch.resolve(choice).code
    except LookupError as e:
        _say(f"  {e}")
        return None


def _write_config(
    path: Path,
    library: str,
    card: str,
    pin: str,
    default_pickup_branch: str | None,
    default_format: str | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Build TOML manually so we control formatting + comments.
    lines = [
        f'library = "{library}"',
    ]
    if default_pickup_branch:
        lines.append(f'default_pickup_branch = "{default_pickup_branch}"')
    if default_format:
        lines.append(f'default_format = "{default_format}"')
    lines.extend(
        [
            "",
            "[credentials]",
            f'card = "{card}"',
            f'pin  = "{pin}"',
            "",
        ]
    )
    path.write_text("\n".join(lines))
    os.chmod(path, 0o600)


def _existing_config_summary(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        data = tomllib.loads(path.read_text())
    except Exception:
        return "  (existing file is not valid TOML)"
    bits = [f"library={data.get('library')!r}"]
    if data.get("default_pickup_branch"):
        bits.append(f"pickup={data['default_pickup_branch']!r}")
    return "  " + ", ".join(bits)


def run() -> int:
    """Entry point for ``bibliocommons-mcp init``."""
    config_path = Path(os.environ.get("BIBLIOCOMMONS_MCP_CONFIG", DEFAULT_CONFIG_PATH))

    _say("bibliocommons-mcp setup")
    _say("=" * 40)
    _say()

    existing = _existing_config_summary(config_path)
    if existing is not None:
        _say(f"Existing config at {config_path}:")
        _say(existing)
        if not _ask_yes_no("Overwrite?", default=False):
            _say("Keeping existing config. Done.")
            return 0
        _say()

    # 1. Library subdomain
    _say(f"Library subdomain — e.g. {', '.join(_EXAMPLE_LIBRARIES[:5])}.")
    _say("(If your library uses BiblioCommons, the URL is {name}.bibliocommons.com.)")
    while True:
        library = _ask("Subdomain").lower()
        info = _validate_library(library)
        if info is not None:
            branches_data = info.get("entities", {}).get("branches", {})
            _say(f"  ✓ found {len(branches_data)} branches")
            break

    # 2. Card + PIN, with login test
    _say()
    while True:
        card = _ask("Library card number")
        pin = _ask_secret("PIN")
        _say("  testing login...")
        result = _attempt_login(library, card, pin)
        if result is not None:
            client, branches = result
            _say("  ✓ login OK")
            break
        if not _ask_yes_no("Try again?", default=True):
            _say("Aborting without saving.")
            return 1

    # 3. Default pickup branch
    default_branch = _pick_branch(branches)
    if default_branch:
        _say(f"  ✓ default pickup branch: {default_branch}")

    # 4. Default format (optional)
    _say()
    _say("Default search format — common codes:")
    _say("  MUSIC_CD, BK, EBOOK, EAUDIOBOOK, AUDIOBOOK_CD, DVD")
    _say("(Leave blank to search all formats by default.)")
    default_format = _ask("Default format", default="") or None

    # 5. Confirm + write
    _say()
    _say("Saving config:")
    _say(f"  path:    {config_path}")
    _say(f"  library: {library}")
    if default_branch:
        _say(f"  pickup:  {default_branch}")
    if default_format:
        _say(f"  format:  {default_format}")
    _say()
    if not _ask_yes_no("Write it?", default=True):
        _say("Aborted, no changes made.")
        return 1

    _write_config(config_path, library, card, pin, default_branch, default_format)
    _say(f"  ✓ wrote {config_path} (mode 0600)")

    _say()
    _say("Next step — wire it into your MCP client. For Claude Code:")
    _say()
    _say("  claude mcp add bibliocommons bibliocommons-mcp --scope user")
    _say()
    _say("For Claude Desktop / Cursor / others, see docs/mcp-clients.md.")
    return 0
