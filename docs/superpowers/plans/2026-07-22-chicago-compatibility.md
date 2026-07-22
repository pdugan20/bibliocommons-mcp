# Chicago Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Chicago Public Library authentication survive duplicate-domain SSO cookies and make the public branch-code contract library-agnostic.

**Architecture:** Keep normal authentication delegated to `bibliocommons`. When that dependency raises only `httpx.CookieConflict`, recover the already-issued cookies from its jar and finish the same header and account-id setup locally. Keep numeric branch support in the existing string-based resolver and correct the descriptions around it.

**Tech Stack:** Python 3.11+, httpx, pytest, Pydantic, FastMCP, Syrupy snapshots, Ruff

## Global Constraints

- Never log or include card numbers, PINs, access tokens, or session IDs in errors.
- Catch only `httpx.CookieConflict`; all unrelated authentication failures propagate unchanged.
- Preserve `account_id = int(session_id suffix) + 1` for borrowing operations.
- Do not add a Git dependency or change the `bibliocommons>=2025.3` version floor.
- Do not perform live state-changing gateway tests.

---

### Task 1: Duplicate-cookie authentication fallback

**Files:**
- Create: `tests/test_client_auth.py`
- Modify: `src/bibliocommons_mcp/client.py:96-101`

**Interfaces:**
- Consumes: `Client.authenticate(card: str, pin: str) -> None` and the upstream client's `httpx_client`, `authenticate`, and `account_id` attributes.
- Produces: `Client._finish_auth_from_cookie_jar() -> None`, a private compatibility path used only after `httpx.CookieConflict`.

- [ ] **Step 1: Write the failing duplicate-cookie test**

```python
from __future__ import annotations

import httpx

from bibliocommons_mcp.client import Client


class _DuplicateCookieClient:
    def __init__(self) -> None:
        self.httpx_client = httpx.Client()

    def authenticate(self, username: str, password: str) -> None:
        assert username == "library-card"
        assert password == "library-pin"
        cookies = self.httpx_client.cookies
        for domain in ("chipublib.bibliocommons.com", ".bibliocommons.com"):
            cookies.set("bc_access_token", "test-access-token", domain=domain)
            cookies.set(
                "session_id",
                "00000000-0000-0000-0000-000000000000-41",
                domain=domain,
            )
        cookies["bc_access_token"]


def test_authenticate_recovers_duplicate_domain_cookies() -> None:
    client = Client("chipublib")
    upstream = _DuplicateCookieClient()
    client._bc = upstream

    client.authenticate("library-card", "library-pin")

    assert client.http.headers["X-Access-Token"] == "test-access-token"
    assert client.http.headers["X-Session-Id"].endswith("-41")
    assert client.account_id == 42
```

- [ ] **Step 2: Run the test and verify RED**

Run: `PATH="$PWD/.venv/bin:$PATH" pytest tests/test_client_auth.py -v`

Expected: FAIL because `Client.authenticate` propagates `httpx.CookieConflict`.

- [ ] **Step 3: Implement the minimal fallback**

```python
    def authenticate(self, card: str, pin: str) -> None:
        if self._authed:
            return
        try:
            self._bc.authenticate(username=card, password=pin)
        except httpx.CookieConflict:
            self._finish_auth_from_cookie_jar()
        self._authed = True

    def _finish_auth_from_cookie_jar(self) -> None:
        values: dict[str, str] = {}
        expected = {"bc_access_token", "session_id"}
        for cookie in self.http.cookies.jar:
            if cookie.name in expected and cookie.value:
                values.setdefault(cookie.name, cookie.value)

        access_token = values.get("bc_access_token")
        session_id = values.get("session_id")
        if not access_token:
            raise RuntimeError("Authentication failed: no access-token cookie")
        if not session_id:
            raise RuntimeError("Authentication failed: no session cookie")

        self.http.headers.update(
            {"X-Access-Token": access_token, "X-Session-Id": session_id}
        )
        self._bc.account_id = int(session_id.rsplit("-", 1)[-1]) + 1
```

- [ ] **Step 4: Run the focused test and verify GREEN**

Run: `PATH="$PWD/.venv/bin:$PATH" pytest tests/test_client_auth.py -v`

Expected: 1 passed.

- [ ] **Step 5: Run client and branch tests**

Run: `PATH="$PWD/.venv/bin:$PATH" pytest tests/test_client_auth.py tests/test_client_body_shapes.py tests/test_client_vcr.py tests/test_branches.py -v`

Expected: all selected tests pass with no failures.

- [ ] **Step 6: Commit the behavior change**

```bash
git add src/bibliocommons_mcp/client.py tests/test_client_auth.py
git commit -m "fix(auth): handle duplicate SSO cookies"
```

---

### Task 2: Library-agnostic branch-code contract

**Files:**
- Modify: `tests/test_branches.py`
- Modify: `src/bibliocommons_mcp/branches.py`
- Modify: `src/bibliocommons_mcp/models.py`
- Modify: `src/bibliocommons_mcp/server.py`
- Modify: `docs/architecture.md`
- Modify: `docs/configuration.md`
- Modify: `docs/troubleshooting.md`
- Modify: `docs/projects/docs-site/README.md`
- Modify: `docs-mintlify/guides/branches.mdx`
- Modify: `docs-mintlify/guides/holds.mdx`
- Modify: `docs-mintlify/guides/search.mdx`
- Modify: `docs-mintlify/troubleshooting.mdx`
- Regenerate: `docs-mintlify/reference/configuration.mdx`
- Regenerate: `docs-mintlify/reference/mcp-tools.mdx`
- Modify: `tests/__snapshots__/test_schema_snapshots.ambr`

**Interfaces:**
- Consumes: gateway branch maps whose keys are arbitrary strings.
- Produces: unchanged `Branches.resolve(name_or_code: str) -> Branch` behavior plus accurate public descriptions such as `"Branch code, e.g. 'LCY' or '56'."`.

- [ ] **Step 1: Add a numeric-code characterization case**

Add `"56": {"code": "56", "name": "Northtown Branch"}` to `_FAKE_BRANCHES_JSON`, update the expected branch count from seven to eight, and add:

```python
def test_resolve_by_numeric_code(branches):
    assert branches.resolve("56").name == "Northtown Branch"
```

- [ ] **Step 2: Verify existing numeric behavior**

Run: `PATH="$PWD/.venv/bin:$PATH" pytest tests/test_branches.py -v`

Expected: all branch tests pass; this test records behavior already supplied by string dictionary keys.

- [ ] **Step 3: Correct public descriptions**

Replace universal "three-letter code" claims with "branch code". Use `LCY` and `56` together in schema examples. Keep Seattle-specific locker examples explicitly scoped to Seattle. Do not change resolver logic.

- [ ] **Step 4: Regenerate reference docs and update schema snapshots**

Run: `PATH="$PWD/.venv/bin:$PATH" make docs-reference`

Expected: CLI and MCP reference pages regenerate from the corrected source descriptions.

Run: `PATH="$PWD/.venv/bin:$PATH" pytest tests/test_schema_snapshots.py --snapshot-update -v`

Expected: 1 snapshot updated and the test passes.

- [ ] **Step 5: Verify documentation and code formatting**

Run: `rg -n '3-letter|Three-letter|three-letter' src docs docs-mintlify README.md tests -g '!docs/superpowers/**'`

Expected: no universal three-letter branch-code claims remain.

Run: `git diff --check`

Expected: exit 0 with no whitespace errors.

- [ ] **Step 6: Commit the contract correction**

```bash
git add tests/test_branches.py src/bibliocommons_mcp/branches.py src/bibliocommons_mcp/models.py src/bibliocommons_mcp/server.py docs/architecture.md docs/configuration.md docs/troubleshooting.md docs/projects/docs-site/README.md docs-mintlify/guides/branches.mdx docs-mintlify/guides/holds.mdx docs-mintlify/guides/search.mdx docs-mintlify/troubleshooting.mdx docs-mintlify/reference/configuration.mdx docs-mintlify/reference/mcp-tools.mdx tests/__snapshots__/test_schema_snapshots.ambr
git commit -m "docs(branches): support library-specific codes"
```

---

### Task 3: Full verification and publication

**Files:**
- Verify all files changed by Tasks 1 and 2.

**Interfaces:**
- Consumes: the completed compatibility branch.
- Produces: a verified draft pull request referencing issue #46.

- [ ] **Step 1: Run the complete project gate**

Run: `PATH="$PWD/.venv/bin:$PATH" make check-all`

Expected: Ruff check and format pass; all pytest tests pass; coverage remains at least 80%.

- [ ] **Step 2: Inspect the final scope**

Run: `git status --short --branch && git diff --check && git log --oneline origin/main..HEAD`

Expected: only intentional commits are ahead of `origin/main`, with no uncommitted files.

- [ ] **Step 3: Push and open a draft pull request**

```bash
git push -u origin agent/fix-chicago-compat
```

Create a draft PR titled `fix(auth): support Chicago multi-domain SSO` with the root cause, user impact, and verification results. Reference issue #46 without closing it until the PR reaches `main`.
