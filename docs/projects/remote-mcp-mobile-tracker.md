# Tracker: Remote MCP — mobile custom connector

> Execution tracker for [`remote-mcp-mobile.md`](remote-mcp-mobile.md). The
> brief is the _why/architecture_; this is the _what/checklist_. Keep them in
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

| #   | Task                                                                                                                                                                                                                                                                                                                                 | Owner      | Status |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- | ------ |
| 0.1 | Confirm `getbiblio.app` registered and nameservers pointed at Cloudflare                                                                                                                                                                                                                                                             | owner      | [ ]    |
| 0.2 | **Decided: per-session + warm instance** — in-memory cookie jar, never persist raw PIN; BC session ~1yr so PIN re-entry is ~per-deploy. Upgrade path = persist encrypted session cookie. Rationale in brief §2/Open questions                                                                                                        | owner      | [x]    |
| 0.3 | **Decided: WorkOS AuthKit** (1M-MAU free, DCR+CIMD on free, RFC 8707, JWKS/JWT). Owner action — create the WorkOS account + note issuer/JWKS URL — tracked in followups                                                                                                                                                              | owner      | [~]    |
| 0.4 | **Decided: stay on official `mcp`** — hand-wire a JWKS `TokenVerifier` (no `fastmcp` v2 swap). Rationale in brief Open questions                                                                                                                                                                                                     | repo       | [x]    |
| 0.5 | **Decided: Fly.io** (always-on machine fits the warm per-session cache; cheapest/simplest). Config in `fly.toml`; steps in `docs/deploy-fly.md`. Owner: create Fly app + deploy                                                                                                                                                      | owner      | [~]    |
| 0.6 | **N/A for v1** — per-session is in-memory, no creds store needed. Required only if the session-cookie-persistence upgrade is taken (small encrypted TTL store)                                                                                                                                                                       | owner+repo | [x]    |
| 0.7 | **ToS check** — SPL / BiblioCommons terms on hosting a multi-user proxy that stores card+PIN and acts on patrons' behalf. Hard gate before any non-owner user                                                                                                                                                                        | owner      | [!]    |
| 0.8 | Anthropic publishes a stable outbound range `160.79.104.0/21` ([ip-addresses doc](https://platform.claude.com/docs/en/api/ip-addresses), "won't change without notice"). Behind Cloudflare the **origin sees CF IPs**, so apply the allowlist at the Cloudflare **edge** as defense-in-depth — OAuth is the real gate (see brief §4) | repo       | [x]    |

---

## Phase 1 — HTTP transport + authless read-only catalog (Milestone 1)

Goal: prove the connector attaches on mobile and read-only tools work, with
**no auth at all**. De-risks transport + hosting + domain before touching auth.

Acceptance: connector added on claude.ai web shows up on the iOS app;
`search` / `availability` / `list_branches` return real results end-to-end;
`/healthz` is green on the deployed container.

### 1a. Transport switch (code)

| #   | Task                                                                                                                                                                                            | Owner | Status |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ------ |
| 1.1 | Add transport switch in `server.py:main()`: no-arg → stdio (unchanged); `serve --http` / `BIBLIOCOMMONS_MCP_TRANSPORT=http` → streamable-http                                                   | repo  | [x]    |
| 1.2 | Configure `FastMCP` for HTTP: `stateless_http=True`, bind `0.0.0.0:$PORT` (`PORT` env honored), path default `/mcp`                                                                             | repo  | [x]    |
| 1.3 | Read-only catalog mode: `config.py` allows library-only (`require_credentials=False`); account tools raise a clean `NotAuthenticatedError`→ToolError. Library comes from config (not hardcoded) | repo  | [x]    |
| 1.4 | Public `GET /healthz` via `@mcp.custom_route` (credential-free; reports library + auth mode)                                                                                                    | repo  | [x]    |
| 1.5 | Unit tests: transport selection, healthz (ok/read-only/misconfigured), authless boot, account-tool clean error — `tests/test_http_transport.py` + `tests/test_config.py` (113 pass)             | repo  | [x]    |
| 1.6 | Local verify: curl smoke passed (`/healthz` 200 + MCP `initialize` over streamable-http in read-only mode). Full `npx @modelcontextprotocol/inspector` visual check still owner-side            | repo  | [~]    |

### 1b. Containerize & deploy

| #    | Task                                                                                                                                                                                                      | Owner      | Status |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------ |
| 1.7  | Dockerfile (python 3.12-slim, installs package, non-root, `HEALTHCHECK` on `/healthz`, entrypoint `serve --http`, honors `$PORT`) + `.dockerignore`. Build + /healthz container smoke green on CI (PR #5) | repo       | [x]    |
| 1.8  | CI **build** + container `/healthz` smoke added (`.github/workflows/docker-build.yml`). **Push** to a registry deferred → followups 1.8 (needs creds)                                                     | repo       | [~]    |
| 1.9  | Deploy to chosen host; confirm `/healthz` green over public HTTPS                                                                                                                                         | owner+repo | [ ]    |
| 1.10 | Map `getbiblio.app` → service via Cloudflare proxy; TLS valid; `https://getbiblio.app/mcp` reachable                                                                                                      | owner      | [ ]    |

### 1c. Connector attach (owner-only — can't be done in-repo)

| #    | Task                                                                                  | Owner | Status |
| ---- | ------------------------------------------------------------------------------------- | ----- | ------ |
| 1.11 | Add `https://getbiblio.app/mcp` as a custom connector on **claude.ai web** (authless) | owner | [ ]    |
| 1.12 | Confirm it **syncs to the iOS app** and a `search` returns there                      | owner | [ ]    |

### 1d. Favicon seed (cheap, do it now while the endpoint is fresh)

> Mechanism is **confirmed** (brief §5): Claude renders the icon from
> `https://www.google.com/s2/favicons?domain=getbiblio.app&sz=32`, keyed on the
> registrable apex. Seeding a favicon early just gives Google's crawler the
> ~1-day head start so the icon is already live by the time the connector
> ships. Full asset/polish work is Phase 4.

| #    | Task                                                                                                                                                                                              | Owner      | Status |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------ |
| 1.13 | Serve a favicon (even a placeholder) publicly at the **apex** `getbiblio.app/favicon.ico`; confirm `https://www.google.com/s2/favicons?domain=getbiblio.app&sz=32` returns it (not a blank globe) | repo+owner | [ ]    |
| 1.14 | Confirm the icon shows on the connector on both claude.ai web and iOS (allow ~1 day for Google cache)                                                                                             | owner      | [ ]    |

---

## Phase 2 — OAuth Resource Server + managed IdP + per-user creds (Milestone 2)

Goal: authenticated multi-user. The server is an OAuth 2.1 **Resource Server**
that validates tokens from the chosen IdP (Phase 0.3); it does **not** run its
own authorization server. Per CLAUDE.md rule #1, credentials never hit logs,
stdout, or the wire protocol — that extends to the store.

Acceptance: a second person can connect with _their_ library card and see
_their_ holds; tokens are audience-validated; the user's IdP token is never
forwarded to the BiblioCommons gateway.

### 2a. Resource Server wiring

| #   | Task                                                                                                                                                       | Owner | Status |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ------ |
| 2.1 | WorkOS app: enable DCR/CIMD (Claude auto-registers, no manual redirect/secret). Resource Indicator = `https://getbiblio.app/mcp`. **Owner — deploy-time**  | owner | [ ]    |
| 2.2 | `_build_mcp()` wires `FastMCP(token_verifier=WorkOSTokenVerifier, auth=AuthSettings(...))` when `WORKOS_*` env present; omits `auth_server_provider`       | repo  | [x]    |
| 2.3 | `WorkOSTokenVerifier.verify_token()` — JWKS/JWT: signature + iss (trailing-slash tolerant) + aud (RFC 8707) + expiry                                       | repo  | [x]    |
| 2.4 | Verified live: SDK serves `/.well-known/oauth-protected-resource/mcp` → `authorization_servers: api.workos.com`; un-authed `/mcp` → 401 + WWW-Authenticate | repo  | [x]    |
| 2.5 | Confirmed: no `RemoteAuthProvider` (fastmcp-only); hand-wired `TokenVerifier` on official `mcp`                                                            | repo  | [x]    |

### 2b. Per-user credentials + client cache

| #    | Task                                                                                                                                                                                         | Owner | Status |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ------ |
| 2.6  | `_current_subject()` reads identity via `get_access_token().subject`                                                                                                                         | repo  | [x]    |
| 2.7  | `_ensure_client()` refactored to identity-aware: single-tenant path (stdio/M1) vs per-subject path                                                                                           | repo  | [x]    |
| 2.8  | Per-subject `Client` cache (`_user_clients`) keyed by subject; authenticates once. TTL/eviction deferred to 3.1                                                                              | repo  | [x]    |
| 2.9  | `/account` settings page (`web_settings.py`): WorkOS browser login → enter library/card/PIN → validated against BC → stored in `_cred_store`. Per-session in-memory; raw PIN never persisted | repo  | [x]    |
| 2.10 | Audit: card/PIN never logged / in errors / in tool output; PIN not echoed in the form; store is in-memory only (no PIN at rest); session/state cookies signed + HttpOnly/Secure              | repo  | [x]    |

### 2c. Authenticated tools live

| #    | Task                                                                                                                                       | Owner | Status |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------ | ----- | ------ |
| 2.11 | Authenticated tools route per-user via `_ensure_client()`; account ops need a provisioned record. (End-to-end live = 2.13)                 | repo  | [x]    |
| 2.12 | Per-user library selection: each subject's `UserCredentials.library` drives the gateway base URL                                           | repo  | [x]    |
| 2.13 | Owner verify: complete OAuth flow from claude.ai web; `list_holds` returns the owner's holds                                               | owner | [ ]    |
| 2.14 | Owner verify: a **second** account connects with their own card and sees their own holds (proves per-user isolation, not a shared session) | owner | [ ]    |

---

## Phase 3 — Hardening

Acceptance: production-safe for the intended user set (gated by ToS 0.7).

| #   | Task                                                                                                                                                                                      | Owner      | Status |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------ |
| 3.1 | Per-user client cache bounded by idle-TTL + LRU (`cache.TTLCache`; `BIBLIOCOMMONS_MCP_SESSION_TTL` / `BIBLIOCOMMONS_MCP_MAX_SESSIONS`). Eviction re-auths from stored creds, no re-prompt | repo       | [x]    |
| 3.2 | Per-user rate limiting — **recommend at the Cloudflare edge** (you already have the zone) rather than in-process; light in-process guard optional. Open                                   | repo+owner | [ ]    |
| 3.3 | Trim/paginate large tool outputs under the ~150k-char result cap (esp. `search`, `list_holds`)                                                                                            | repo       | [ ]    |
| 3.4 | **N/A for v1** — credential store is in-memory (nothing at rest). Deletion = process restart / `_cred_store.delete`. Revisit if the session-cookie-persistence upgrade is taken           | repo       | [x]    |
| 3.5 | Structured stderr logging + `BIBLIOCOMMONS_MCP_LOG_LEVEL` honored; audited — no card/PIN/API-key/token in logs (auth + web_settings log failures without secret content)                  | repo       | [x]    |
| 3.6 | Apply Anthropic IP allowlist if 0.8 found one required                                                                                                                                    | owner      | [ ]    |
| 3.7 | Gateway 4xx/5xx → clean ToolError via `_safe` (BCError/BranchNotFound/ValueError/NotAuthenticatedError); internals not leaked                                                             | repo       | [x]    |

---

## Phase 4 — Favicon (polish; mechanism confirmed)

> Goal: a polished, distinct connector icon for `getbiblio.app`, the way
> rewind gets one for `rewind.rest` — a publicly-fetchable favicon at the
> registrable apex that Google's `s2/favicons?domain=getbiblio.app&sz=32`
> service serves and Claude renders. Phase 1d seeds a placeholder; this phase
> replaces it with the real asset and the supporting tags. Keep all
> favicon/landing routes public even though MCP + OAuth endpoints are
> auth-gated (Google's crawler has no credentials).

| #   | Task                                                                                                                                                                                                     | Owner      | Status |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------ |
| 4.1 | Design / obtain the icon asset (a book/library glyph matching `getbiblio` branding; distinct from clickwheel's)                                                                                          | owner      | [ ]    |
| 4.2 | Generate the favicon set: multi-res `favicon.ico` (16/32/48), `favicon.png`, `apple-touch-icon.png`                                                                                                      | repo       | [ ]    |
| 4.3 | Serve them publicly at the **apex** `getbiblio.app` — either a Cloudflare static asset/rule or public Starlette routes on the parent app (rewind serves via its Worker; we serve via Cloudflare/our app) | repo+owner | [ ]    |
| 4.4 | Minimal public landing page at `/` with `<link rel="icon" ...>` + apple-touch-icon tags                                                                                                                  | repo       | [ ]    |
| 4.5 | Confirm favicon + well-known routes are reachable **unauthenticated** while `/mcp` + OAuth stay gated                                                                                                    | repo       | [ ]    |
| 4.6 | Re-prime Google: fetch `https://www.google.com/s2/favicons?domain=getbiblio.app`; allow up to ~1 day cache lag                                                                                           | owner      | [ ]    |
| 4.7 | Verify the connector icon renders as the `getbiblio.app` favicon on **both** claude.ai web and the iOS app, distinct from clickwheel                                                                     | owner      | [ ]    |

---

## Cross-cutting / definition of done

- [ ] Brief (`remote-mcp-mobile.md`) and this tracker agree; both updated as decisions land.
- [ ] stdio transport still works for local Claude Code (no regression).
- [ ] No state-changing tests against the live gateway in CI (CLAUDE.md rule #10) — body-shape unit tests + VCR for read-only only.
- [ ] No credential ever in logs / stdout / tool output / the store in plaintext.
- [ ] ToS sign-off (0.7) before any non-owner user is onboarded.
