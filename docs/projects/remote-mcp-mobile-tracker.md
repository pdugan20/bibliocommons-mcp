# Tracker: Remote MCP — mobile custom connector

> Execution tracker for [`remote-mcp-mobile.md`](remote-mcp-mobile.md). The
> brief is the *why/architecture*; this is the *what/checklist*. Keep them in
> sync — if a decision here contradicts the brief, fix the brief too.
>
> **Legend:** `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked.
> **Owner column:** `repo` = an in-repo agent can do it · `owner` = needs the
> human (accounts, payments, phone, ToS, secrets).
>
> **Deferrals** (owner-blocked items) are tracked in
> [`remote-mcp-mobile-followups.md`](remote-mcp-mobile-followups.md) so they're
> not lost. Working rule: don't defer unless necessary.

---

## Phase 0 — Decisions & prerequisites (gates everything)

Acceptance: every open question in the brief is answered and written down;
accounts exist; DNS resolves.

| # | Task | Owner | Status |
|---|------|-------|--------|
| 0.1 | Confirm `getbiblio.app` registered and nameservers pointed at Cloudflare | owner | [ ] |
| 0.2 | Decide **credential-storage model**: per-session (default) vs custodian-persist. Record rationale in brief §2 | owner | [ ] |
| 0.3 | Decide **IdP**: WorkOS / Auth0 / Clerk / Stytch / Descope / other. Create the account, note the issuer URL | owner | [ ] |
| 0.4 | Decide **SDK track**: stay on official `mcp` (hand-wired Resource Server) vs adopt standalone `fastmcp` v2 (first-class IdP providers). Record in brief open questions | owner+repo | [ ] |
| 0.5 | Decide **hosting**: Cloud Run vs Fly vs Railway. Create the account/project | owner | [ ] |
| 0.6 | Choose **credential/grant store backend** (Firestore / Cloud SQL / Redis-with-encryption) supporting TTL + encryption-at-rest | owner+repo | [ ] |
| 0.7 | **ToS check** — SPL / BiblioCommons terms on hosting a multi-user proxy that stores card+PIN and acts on patrons' behalf. Hard gate before any non-owner user | owner | [!] |
| 0.8 | Confirm whether Anthropic requires an inbound-IP allowlist for connectors; capture the live CIDR list if so | repo | [ ] |

---

## Phase 1 — HTTP transport + authless read-only catalog (Milestone 1)

Goal: prove the connector attaches on mobile and read-only tools work, with
**no auth at all**. De-risks transport + hosting + domain before touching auth.

Acceptance: connector added on claude.ai web shows up on the iOS app;
`search` / `availability` / `list_branches` return real results end-to-end;
`/healthz` is green on the deployed container.

### 1a. Transport switch (code)

| # | Task | Owner | Status |
|---|------|-------|--------|
| 1.1 | Add transport switch in `server.py:main()`: no-arg → stdio (unchanged); `serve --http` / `BIBLIOCOMMONS_MCP_TRANSPORT=http` → streamable-http | repo | [ ] |
| 1.2 | Configure `FastMCP` for HTTP: `stateless_http=True`, bind `0.0.0.0:$PORT`, set `streamable_http_path` deliberately (default `/mcp`) | repo | [ ] |
| 1.3 | For M1, hardcode a single `library` (e.g. `seattle`) so no per-user resolution is needed yet; read-only tools take no `account_id` | repo | [ ] |
| 1.4 | Add a public `GET /healthz` route (mount `streamable_http_app()` under a Starlette parent, or use SDK route hooks) | repo | [ ] |
| 1.5 | Unit test: HTTP app boots, `/healthz` 200s, tools list includes read-only tools (no live gateway per CLAUDE.md rule #10) | repo | [ ] |
| 1.6 | Local verify: `npx @modelcontextprotocol/inspector` against `http://localhost:$PORT/mcp` — tools list + a `search` call succeed | repo | [ ] |

### 1b. Containerize & deploy

| # | Task | Owner | Status |
|---|------|-------|--------|
| 1.7 | Dockerfile (python 3.11+, install package, entrypoint `bibliocommons-mcp serve --http`), honor `$PORT` | repo | [ ] |
| 1.8 | CI: build + push container image | repo | [ ] |
| 1.9 | Deploy to chosen host; confirm `/healthz` green over public HTTPS | owner+repo | [ ] |
| 1.10 | Map `getbiblio.app` → service via Cloudflare proxy; TLS valid; `https://getbiblio.app/mcp` reachable | owner | [ ] |

### 1c. Connector attach (owner-only — can't be done in-repo)

| # | Task | Owner | Status |
|---|------|-------|--------|
| 1.11 | Add `https://getbiblio.app/mcp` as a custom connector on **claude.ai web** (authless) | owner | [ ] |
| 1.12 | Confirm it **syncs to the iOS app** and a `search` returns there | owner | [ ] |

### 1d. Favicon seed (cheap, do it now while the endpoint is fresh)

> Mechanism is **confirmed** (brief §5): Claude renders the icon from
> `https://www.google.com/s2/favicons?domain=getbiblio.app&sz=32`, keyed on the
> registrable apex. Seeding a favicon early just gives Google's crawler the
> ~1-day head start so the icon is already live by the time the connector
> ships. Full asset/polish work is Phase 4.

| # | Task | Owner | Status |
|---|------|-------|--------|
| 1.13 | Serve a favicon (even a placeholder) publicly at the **apex** `getbiblio.app/favicon.ico`; confirm `https://www.google.com/s2/favicons?domain=getbiblio.app&sz=32` returns it (not a blank globe) | repo+owner | [ ] |
| 1.14 | Confirm the icon shows on the connector on both claude.ai web and iOS (allow ~1 day for Google cache) | owner | [ ] |

---

## Phase 2 — OAuth Resource Server + managed IdP + per-user creds (Milestone 2)

Goal: authenticated multi-user. The server is an OAuth 2.1 **Resource Server**
that validates tokens from the chosen IdP (Phase 0.3); it does **not** run its
own authorization server. Per CLAUDE.md rule #1, credentials never hit logs,
stdout, or the wire protocol — that extends to the store.

Acceptance: a second person can connect with *their* library card and see
*their* holds; tokens are audience-validated; the user's IdP token is never
forwarded to the BiblioCommons gateway.

### 2a. Resource Server wiring

| # | Task | Owner | Status |
|---|------|-------|--------|
| 2.1 | Configure IdP app: redirect URI `https://claude.ai/api/mcp/auth_callback`, PKCE/S256, public client. Note client_id (+secret if non-DCR) | owner | [ ] |
| 2.2 | Wire `FastMCP(token_verifier=..., auth=AuthSettings(issuer_url=<IdP>, resource_server_url="https://getbiblio.app/mcp", required_scopes=[...]))`; omit `auth_server_provider` | repo | [ ] |
| 2.3 | Implement `verify_token()` (JWT verify or RFC 7662 introspection against the IdP); **validate audience / RFC 8707 `resource`** | repo | [ ] |
| 2.4 | Confirm SDK auto-serves `/.well-known/oauth-protected-resource/mcp` and its `authorization_servers` points at the IdP (issue #1264: full `/mcp` URL in `resource_server_url`) | repo | [ ] |
| 2.5 | Do **not** import `RemoteAuthProvider` if on official `mcp` SDK (fastmcp-only symbol) | repo | [ ] |

### 2b. Per-user credentials + client cache

| # | Task | Owner | Status |
|---|------|-------|--------|
| 2.6 | In tools, read identity via `get_access_token().subject`/`.claims` | repo | [ ] |
| 2.7 | Refactor `server.py:_ensure_client()` (~`:148`) from module-global singleton → per-subject resolution | repo | [ ] |
| 2.8 | Per-user `Client` cache keyed by subject, TTL'd (avoid re-`authenticate()` per call); evict on expiry | repo | [ ] |
| 2.9 | Implement the chosen credential model (0.2): consent/settings page to capture `{library, card, pin}` (custodian, encrypted-at-rest, per-record key + deletion path) **or** per-session capture (never persisted) | repo+owner | [ ] |
| 2.10 | Audit: card/PIN never logged, never in error messages, never in tool output (CLAUDE.md rule #1) | repo | [ ] |

### 2c. Authenticated tools live

| # | Task | Owner | Status |
|---|------|-------|--------|
| 2.11 | Enable authenticated tools end-to-end: `place_hold`, `place_digital_hold`, `borrow_digital`, `list_holds`, `ready_for_pickup`, `cancel_hold`, `list_loans`, `renew_loan`, `check_in_loan`, `library_health` | repo | [ ] |
| 2.12 | Per-user library selection (multi-library): the configured/connected library drives the gateway base URL | repo | [ ] |
| 2.13 | Owner verify: complete OAuth flow from claude.ai web; `list_holds` returns the owner's holds | owner | [ ] |
| 2.14 | Owner verify: a **second** account connects with their own card and sees their own holds (proves per-user isolation, not a shared session) | owner | [ ] |

---

## Phase 3 — Hardening

Acceptance: production-safe for the intended user set (gated by ToS 0.7).

| # | Task | Owner | Status |
|---|------|-------|--------|
| 3.1 | Session-cache TTL + eviction tuning; respect 300s tool timeout | repo | [ ] |
| 3.2 | Per-user rate limiting (protect the BiblioCommons gateway + your store) | repo | [ ] |
| 3.3 | Trim/paginate large tool outputs under the ~150k-char result cap (esp. `search`, `list_holds`) | repo | [ ] |
| 3.4 | Encryption-at-rest review of the credential store; verify deletion path actually deletes | repo+owner | [ ] |
| 3.5 | Structured stderr logging (CLAUDE.md rule #8), `BIBLIOCOMMONS_MCP_LOG_LEVEL` honored; confirm no secrets in logs | repo | [ ] |
| 3.6 | Apply Anthropic IP allowlist if 0.8 found one required | owner | [ ] |
| 3.7 | Error mapping: gateway 4xx/5xx → clean MCP tool errors (don't leak internals) | repo | [ ] |

---

## Phase 4 — Favicon (polish; mechanism confirmed)

> Goal: a polished, distinct connector icon for `getbiblio.app`, the way
> rewind gets one for `rewind.rest` — a publicly-fetchable favicon at the
> registrable apex that Google's `s2/favicons?domain=getbiblio.app&sz=32`
> service serves and Claude renders. Phase 1d seeds a placeholder; this phase
> replaces it with the real asset and the supporting tags. Keep all
> favicon/landing routes public even though MCP + OAuth endpoints are
> auth-gated (Google's crawler has no credentials).

| # | Task | Owner | Status |
|---|------|-------|--------|
| 4.1 | Design / obtain the icon asset (a book/library glyph matching `getbiblio` branding; distinct from clickwheel's) | owner | [ ] |
| 4.2 | Generate the favicon set: multi-res `favicon.ico` (16/32/48), `favicon.png`, `apple-touch-icon.png` | repo | [ ] |
| 4.3 | Serve them publicly at the **apex** `getbiblio.app` — either a Cloudflare static asset/rule or public Starlette routes on the parent app (rewind serves via its Worker; we serve via Cloudflare/our app) | repo+owner | [ ] |
| 4.4 | Minimal public landing page at `/` with `<link rel="icon" ...>` + apple-touch-icon tags | repo | [ ] |
| 4.5 | Confirm favicon + well-known routes are reachable **unauthenticated** while `/mcp` + OAuth stay gated | repo | [ ] |
| 4.6 | Re-prime Google: fetch `https://www.google.com/s2/favicons?domain=getbiblio.app`; allow up to ~1 day cache lag | owner | [ ] |
| 4.7 | Verify the connector icon renders as the `getbiblio.app` favicon on **both** claude.ai web and the iOS app, distinct from clickwheel | owner | [ ] |

---

## Cross-cutting / definition of done

- [ ] Brief (`remote-mcp-mobile.md`) and this tracker agree; both updated as decisions land.
- [ ] stdio transport still works for local Claude Code (no regression).
- [ ] No state-changing tests against the live gateway in CI (CLAUDE.md rule #10) — body-shape unit tests + VCR for read-only only.
- [ ] No credential ever in logs / stdout / tool output / the store in plaintext.
- [ ] ToS sign-off (0.7) before any non-owner user is onboarded.
