# Architecture

## Overview

bibliocommons-mcp is a thin Python MCP server that authenticates against a BiblioCommons library and forwards a curated set of operations — search, hold, cancel, list, etc. — to the public-facing gateway at `gateway.bibliocommons.com`. The same endpoints work for every BiblioCommons-powered library; the library subdomain is per-instance config.

## Data flow

```text
MCP client (Claude, ChatGPT, Codex, Cursor, ...)
        |
        v  stdio or sessionless Streamable HTTP
   bibliocommons-mcp server
        |
        +-- python-bibliocommons (login flow → session cookies)
        |
        v  HTTPS, cookie auth
   gateway.bibliocommons.com/v2/libraries/{your-library}/...
        |
        v
   The library's underlying ILS (SirsiDynix, Polaris, etc.) + OverDrive
```

## Module layout

- `src/bibliocommons_mcp/config.py` — TOML config loader, env-var overrides
- `src/bibliocommons_mcp/branches.py` — branch name ↔ code resolver with in-memory cache
- `src/bibliocommons_mcp/client.py` — the gateway client. Wraps `python-bibliocommons` for the login flow, layers everything else.
- `src/bibliocommons_mcp/server.py` — official MCP SDK v2 server, tool
  registrations, OAuth resource-server wiring, and Streamable HTTP transport
- `src/bibliocommons_mcp/ui.py` / `ui_resources.py` — official MCP Apps
  extension metadata and bundled HTML resources

## MCP protocol profile

- The runtime pins the official Python SDK to `mcp>=2,<3`. Modern clients
  negotiate MCP 2026-07-28; SDK v2's compatibility path continues to serve
  MCP 2025-11-25 clients.
- Streamable HTTP is sessionless under the modern request/response protocol.
  Legacy HTTP also runs in stateless mode, so neither path relies on sticky
  load-balancer sessions.
- MCP Apps is advertised through the official versioned extension and serves
  the holds, loans, and search cards as `text/html;profile=mcp-app` resources.
- Tool and resource discovery carry public cache hints because their schemas
  and bundled HTML are release-static and identical across users.
- The Tasks extension is intentionally not advertised: current catalog and
  account operations are bounded request/response calls. Revisit Tasks if a
  future bulk or reporting operation can outlive a normal client timeout.
- In remote mode the server remains an OAuth Resource Server. SDK v2 emits the
  protected-resource metadata and bearer challenge; WorkOS JWTs are still
  verified for signature, issuer, audience, expiry, and subject before a
  per-user BiblioCommons session is selected.

## Authentication

We use [`python-bibliocommons`](https://github.com/williamjacksn/python-bibliocommons) for the modern login flow. It scrapes the catalog login form's CSRF token, POSTs barcode + PIN, captures the resulting `bc_access_token` and `session_id` cookies, and sets `X-Access-Token` / `X-Session-Id` headers for subsequent API calls. We extend it with everything else.

The `accountId` used for borrowing operations is derived as `int(session_id.split("-")[-1]) + 1`. The `+1` is correct: the dashboard exposes a separate `currentUserId` (one less, used for social/UGC features); borrowing endpoints want the `+1` value.

## The hold POST that took most of a day to figure out

Placing a physical hold turned out to require a body shape we couldn't derive from the JS bundle alone:

```http
POST https://gateway.bibliocommons.com/v2/libraries/{library}/holds?locale=en-US
Content-Type: application/json

{
  "metadataId": "S30C3857930",
  "materialType": "PHYSICAL",
  "accountId": 1234567890,
  "enableSingleClickHolds": false,
  "materialParams": {
    "branchId": "LCY",
    "expiryDate": null,
    "errorMessageLocale": "en-US"
  }
}
```

The trick is **`errorMessageLocale` inside `materialParams`**. Without it, the gateway's request validator passes happily — `errorMessageLocale` is not a "required" field per the 422 contract — but the downstream ILS adapter NPEs when trying to format a localized response and returns a generic `500 Internal Server Error`. Same shape, same body, no useful hint. The fix only surfaced after capturing a real successful POST from a browser DevTools network panel.

`?locale=en-US` on the URL is _also_ required (separate code path from `errorMessageLocale`).

## Other quirks

| Quirk                                             | Notes                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Digital vs. physical have separate endpoints.** | Available digital items → `POST /v2/libraries/{library}/checkouts` (immediate borrow). Physical → `POST /holds`. Unavailable digital (Libby waitlist) → `POST /holds` with `materialType: "DIGITAL"`, but this needs a `format` enum field we haven't fully exercised yet (deferred to v1.1 — see [`format-codes.md`](format-codes.md) for the leaked enum). The Libby app handles digital waitlists fine in the meantime. |
| **DELETE /holds is bulk.**                        | Body is `{accountId, metadataIds: [...], holdIds: [...], errorMessageLocale}` — plural and arrays even when canceling one.                                                                                                                                                                                                                                                                                                 |
| **Search pagination is fixed at 25 per page.**    | The `size` param is silently ignored. Use `page=N` (1-indexed).                                                                                                                                                                                                                                                                                                                                                            |
| **Branch codes vary by library.**                 | Seattle uses alphabetic codes such as `LCY`; Chicago uses numeric codes such as `56`. Branches can have locker variants; the resolver prefers the regular branch when a name is ambiguous.                                                                                                                                                                                                                                 |
| **Locale matters.**                               | All POSTs need `?locale=en-US` on the URL _and_ `errorMessageLocale: "en-US"` in the body. The MCP server hardcodes both.                                                                                                                                                                                                                                                                                                  |

## Testing strategy

- **Unit tests** for config loading, branch resolution, hold/cancel body shape construction, and error parsing. No network, no credentials needed.
- **VCR cassettes** under `tests/cassettes/` for read-only HTTP flows (login → branches, search, availability). Recorded once against a real library account, then sanitized and replayed in CI. The conftest.py scrubber replaces card/PIN/access-token/session-id with fixed fakes; verifies-clean before commit.
- **No state-changing tests against the live gateway in CI.** `place_hold`, `cancel_hold`, and `borrow_digital` are validated via body-shape unit tests only.
- **Protocol compatibility tests** exercise the MCP 2026-07-28 discovery flow,
  official Apps negotiation, cache hints, sessionless HTTP, OAuth subject
  propagation, and the legacy initialize path supported by SDK v2.
- **Concurrency tests** cover the per-user client cache and mutable in-memory
  stores. Gateway calls are serialized per authenticated BiblioCommons session
  while different users can still make progress concurrently.

To re-record cassettes (after, say, an upstream API change), run:

```bash
BIBLIOCOMMONS_RECORD_CASSETTES=1 make test
```

You need a working `~/.config/bibliocommons-mcp/config.toml` (or env vars). Diff cassettes before committing — they're large and the scrubber is the only thing standing between you and a credential leak.

## Acknowledgments

- [`python-bibliocommons`](https://github.com/williamjacksn/python-bibliocommons) by William Jackson — handles the modern login flow we build on.
- [`SFPL` by kaijchang](https://github.com/kaijchang/SFPL) — first community sighting of the BiblioCommons place-hold endpoint pattern, even if the body shape has since evolved.
- [`bibliophile-backend` by DavidCain](https://github.com/DavidCain/bibliophile-backend) — proof that this approach generalizes across the BiblioCommons platform.
