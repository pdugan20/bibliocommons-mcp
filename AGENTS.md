# bibliocommons-mcp

## Work modes

- Default to exploration for prototypes and small changes. Make focused edits directly; do not require a formal spec, separate plan, worktree, or TDD.
- Apply production rigor when the user explicitly asks to ship, harden, prepare a release, or use strict TDD. Match verification to risk and obey any stronger test requirements below.
- Ask before placing or cancelling holds, borrowing items, recording against the live gateway, publishing a release, or making any other live mutation. A user request naming the exact mutation and target counts as approval for that operation.

MCP server for BiblioCommons-powered public libraries. Search the catalog,
place holds, manage checkouts via an MCP client.

## Stack

- **Python 3.11+** with `httpx`, `lxml`, [`python-bibliocommons`](https://github.com/williamjacksn/python-bibliocommons), `mcp` (FastMCP)
- Single-library-per-server (subdomain configured in `~/.config/bibliocommons-mcp/config.toml`)
- No local persistence — branch list cached in-memory only

## Project Layout

- `src/bibliocommons_mcp/config.py` — TOML config loader, env-var overrides
- `src/bibliocommons_mcp/branches.py` — branch name ↔ 3-letter code resolver (in-memory cache)
- `src/bibliocommons_mcp/client.py` — wrapped BC gateway client with the discovered hold POST/DELETE shapes
- `src/bibliocommons_mcp/server.py` — FastMCP server + tool definitions
- `tests/` — pytest with VCR cassettes (no network in CI)
- `docs/releasing.md` — release-please flow

## MCP tools

- `search(query, format?, page?, sort_by?)` — catalog search with format facet
- `availability(bib_id)` — per-branch availability
- `place_hold(bib_id, pickup_branch?)` — physical hold
- `borrow_digital(bib_id)` — checkout an available digital item
- `list_holds()` / `cancel_hold(hold_id, bib_id)` / `list_loans()`
- `list_branches()` — branches at the configured library
- `library_health()` — login probe + hold counts/quotas

## Critical rules

1. **Credentials never go to logs, stdout, memory, or the wire protocol.**
   stdout is reserved for MCP framing; credentials live in
   `~/.config/bibliocommons-mcp/config.toml` (mode 0600) or env vars.

2. **The hold POST body shape is non-obvious.** Required fields for a
   physical hold:

   ```json
   {
     "metadataId": "S30C...",
     "materialType": "PHYSICAL",
     "accountId": <int>,
     "enableSingleClickHolds": false,
     "materialParams": {
       "branchId": "LCY",
       "expiryDate": null,
       "errorMessageLocale": "en-US"
     }
   }
   ```

   `errorMessageLocale` is the killer field — without it, the gateway returns
   a generic 500 ("Internal Server Error"). The validator passes without it,
   but the ILS adapter NPEs.

3. **Digital vs physical have different endpoints + DTOs.** PHYSICAL goes to
   `POST /holds`; DIGITAL available-now items go to `POST /checkouts`;
   DIGITAL unavailable items (queue) go to `POST /holds` with materialType
   DIGITAL — but that requires a `format` enum field we haven't fully
   confirmed yet (deferred to v1.1).

4. **The DELETE /holds endpoint is bulk.** Required body fields are
   `accountId`, `metadataIds: [...]`, `holdIds: [...]`,
   `errorMessageLocale: "en-US"`. Even cancelling one hold uses arrays.

5. **`python-bibliocommons`'s `account_id` (`session_id last segment + 1`) is
   correct for borrowing operations.** The dashboard exposes a different
   `currentUserId` (one less) used for social/UGC, but POSTs to /holds want
   the +1 borrowing-side accountId.

6. **Search pagination is fixed at 25 per page.** The `size` param is
   ignored. Use `page=N` (1-indexed); the response's
   `catalogSearch.pagination.pages` tells you the total page count.

7. **Branch IDs are 3-letter codes** (LCY = Lake City, CEN = Central, etc.).
   Branches can have locker variants — names like "Lake City Branch: SPL
   Lockers" with codes `LOCK*`. The resolver prefers non-locker matches when
   ambiguous.

8. **MCP server logs to stderr only.** stdout is the wire protocol.
   `BIBLIOCOMMONS_MCP_LOG_LEVEL` controls verbosity.

9. **All gateway POSTs need `?locale=en-US` on the URL** AND
   `errorMessageLocale: "en-US"` in the body. The locale query param alone
   isn't enough — `_post()` and `_delete()` enforce both.

10. **No state-changing tests against the live gateway in CI.** State-changing
    code paths (place_hold, cancel_hold, borrow_digital) are unit-tested for
    body shape correctness only. Read-only flows use VCR cassettes.

## Generality

The same endpoints work for any BiblioCommons-powered library. Library is
configured per-server-instance via the `library` key (subdomain) in config.
Tested against `seattle` and `sfpl`.

## Development

```bash
make dev          # install with dev/test deps + pre-commit hooks
make test         # pytest, VCR replays cassettes
make lint         # ruff check + format check
make format       # ruff --fix + format
make check-all    # lint + test
```

## Recording new cassettes

```bash
BIBLIOCOMMONS_RECORD_CASSETTES=1 make test
```

Needs a working `~/.config/bibliocommons-mcp/config.toml`. Cassettes are
auto-sanitized — see `tests/conftest.py` — but always diff and inspect
before committing.

## Releasing

Driven by `release-please`. See `docs/releasing.md`. **Do not** manually
bump `src/bibliocommons_mcp/__init__.py:__version__`; the
`version-guard.yml` workflow blocks any commit on `main` that does so
outside of release-please's release PR.
