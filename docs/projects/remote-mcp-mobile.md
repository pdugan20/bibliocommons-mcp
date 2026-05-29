# Project: Remote MCP — run as a mobile custom connector (multi-user)

> **Status: Milestone 1 code landed** (Track A — HTTP transport, read-only
> catalog mode, `/healthz`, Dockerfile, build CI). Remaining M1 work is
> owner-side (deploy, domain, connector attach); Milestones 2–3 not started.
> This brief is the handoff for an in-repo agent. It is intentionally
> self-contained — the reference servers it draws on (`rewind`,
> `nextup-backend-mcp`) live in _other repos_ you can't see, so their
> relevant patterns are extracted inline below.
>
> **Validated 2026-05-28** against the live Claude connector docs, the MCP
> authorization spec (2025-06-18 + 2025-11-25 revisions), and the installed
> `mcp` 1.27.1 SDK source. The validation changed the architecture materially
> — see **"What changed in this revision"** at the bottom if you read an
> earlier draft.
>
> **Execution checklist:** [`remote-mcp-mobile-tracker.md`](remote-mcp-mobile-tracker.md)
> — phased tasks with owners + acceptance criteria. This doc is the
> _why/architecture_; the tracker is the _what/checklist_.

## Goal

Make bibliocommons-mcp reachable as a **remote custom connector** in the
Claude mobile (iOS) app and claude.ai — **multi-user**, so anyone can connect
with their own library + card + PIN, not just the machine owner. Domain:
**`getbiblio.app`**.

## Why

Today the only transport is stdio (`server.py:main()`, `mcp.run(transport="stdio")`),
so the server can only run as a local subprocess of a desktop MCP client
(Claude Code / Claude Desktop). The mobile app cannot launch local processes
— it can only attach to a **remote MCP server reachable over the public
internet** speaking Streamable HTTP. bibliocommons is the _ideal_ candidate to
port because it has **zero local-machine dependencies**: every tool hits the
public `https://gateway.bibliocommons.com/v2/...` REST API, the only persisted
state is the in-memory branch cache, and credentials are already env-injectable
(`config.py`, `BIBLIOCOMMONS_LIBRARY/CARD/PIN`). It's a stateless API proxy —
the textbook remote-MCP case.

This intersects two items already on [`../roadmap.md`](../roadmap.md):
**"Multi-library mode"** (v2.x) and **"Search-only / no-credentials mode"**
(v2.x). This project subsumes both — multi-user _requires_ per-request library
selection, and the no-credentials catalog mode is the natural low-risk first
milestone.

## The core constraint (why nextup/rewind work on mobile and we don't)

The difference is purely the **transport + hosting + auth shell**, not the
language. The two sibling servers that already work on mobile both:

- expose **Streamable HTTP** (not stdio) via the MCP SDK's web transport;
- are **hosted on the public internet** with a stable custom domain
  (`mcp.rewind.rest` on Cloudflare Workers; `mcp.next-up.app` on Cloud Run);
- gate access with **OAuth 2.1** (PKCE/S256), tokens validated server-side.

We replicate that shell around the existing FastMCP tool definitions. The
tools themselves barely change. **Note:** rewind ran its own OAuth provider
(`@cloudflare/workers-oauth-provider`) because it predates the spec change
below — we should _not_ copy that; see the auth section.

## Approach

### 1. Add a Streamable HTTP entry point (keep stdio)

`mcp` here is the official `modelcontextprotocol/python-sdk` FastMCP
(`pyproject.toml` pins `mcp>=1.27`; installed 1.27.1), which supports
`mcp.run(transport="streamable-http")` and exposes an ASGI app via
`mcp.streamable_http_app()` (returns a Starlette app) for when you need
custom middleware or extra routes (`/healthz`, favicon, root-level
well-known).

In `server.py:main()` (currently stdio-only), add a transport switch — do
**not** remove stdio; local Claude Code still uses it:

- `bibliocommons-mcp` (no args) → stdio, unchanged.
- `bibliocommons-mcp serve --http` (or `BIBLIOCOMMONS_MCP_TRANSPORT=http`) →
  Streamable HTTP bound to `0.0.0.0:$PORT` (Cloud Run sets `$PORT`).

**SDK specifics verified against 1.27.1 — these bit earlier drafts:**

- The Streamable HTTP endpoint **defaults to `/mcp`, not `/`**
  (`FastMCP.settings.streamable_http_path`). Decide your public path
  deliberately; env override is `FASTMCP_STREAMABLE_HTTP_PATH`, host/port are
  `FASTMCP_HOST` / `FASTMCP_PORT` (defaults `127.0.0.1:8000` — bind `0.0.0.0`
  for a container).
- For a multi-tenant remote service, run **`stateless_http=True`**
  (`FastMCP(..., stateless_http=True)`): a fresh transport per request, no
  sticky-session affinity, which is what you want behind a load balancer.
  Derive the user per-call from the auth context instead of session state
  (see §2). `session_idle_timeout` is incompatible with stateless mode.
- For real auth + custom routes you'll mount `streamable_http_app()` under
  uvicorn — but mounting is **no longer required just to serve the OAuth
  well-known metadata** (the SDK now does that itself; see §3a).

### 2. Multi-tenancy — still the real work, but reshaped

Today the design is **one server instance = one library = one card** (creds
from `config.toml` / env; see CLAUDE.md "Single-library-per-server"). The
concrete chokepoint is `server.py:_ensure_client()` (~`:148`) — a Config-driven
**module-global singleton** `Client`. A multi-user remote service inverts this:
**credentials must be per-user**, supplied via the auth flow, never baked into
server config. `_ensure_client()` becomes "resolve (and cache) the `Client`
for the _authenticated identity_ of this request."

The good news from the code audit: `client.py` is **already fully
instance-per-library**. `Client(library)` → `authenticate(card, pin)` →
instance `account_id` (the `+1` quirk, CLAUDE.md rule #5, is computed
per-instance). So multi-tenancy is "mint one `Client` per user, cache it keyed
by the authenticated subject with a TTL" — not a rewrite of the tool layer.
Re-auth is a network round-trip you don't want on every call, hence the cache.

`search` / `availability` / `list_branches` are **read-only and touch no
`account_id`** (verified — they call `_get` without auth state). They answer
for any `library` with no logged-in session. That's the "no-credentials
catalog mode" and it's milestone 1.

**The identity-vs-library-credentials split (important):** the OAuth flow
below authenticates _who the user is_. It does **not** convey their library
card/PIN. So you still need a step that maps `authenticated subject →
{library, card, pin}`. Two storage models — pick one in the open questions:

- **Custodian (persist):** the user enters library subdomain + card + PIN once
  (on a server-hosted consent/settings page), you encrypt and store keyed to
  the subject, later calls look it up. Powerful but you are now **custodian of
  other people's library PINs** — encryption-at-rest with a per-record key,
  never logged (CLAUDE.md rule #1 extends to the store), and a deletion path.
- **Per-session (don't persist):** bring-your-own — creds live only for the
  life of an authenticated session, re-supplied on reconnect. Lower risk, more
  friction.

### 3. Auth: be a Resource Server, delegate to a managed IdP (do NOT run your own OAuth server)

**This is the biggest correction from validation.** An earlier draft said the
connector "must run its own OAuth 2.1 server (like rewind/nextup do)." Under
the **current** MCP spec that is no longer the right call:

- **MCP spec 2025-06-18 split the roles** (PR #284). The MCP server is an
  OAuth 2.1 **Resource Server**; the Authorization Server "may be hosted with
  the resource server **or a separate entity**." The blessed path is: be a
  thin RS that validates audience-bound tokens and **delegates login + token
  issuance to an external/managed IdP** (WorkOS, Auth0, Clerk, Stytch,
  Descope all ship "MCP auth" products for exactly this).
- **DCR is no longer mandatory.** `SHOULD` in 2025-06-18, demoted to `MAY` in
  2025-11-25 (superseded by Client ID Metadata Documents). And Claude
  explicitly supports **non-DCR servers via a manually-entered client
  ID/secret** in the connector's Advanced settings. A managed IdP handles
  registration concerns either way.
- **Claude also supports fully authless remote connectors** — which is what
  makes milestone 1 nearly free.

**What the official `mcp` SDK (1.27.1) gives you for RS mode** (verified in
source): construct `FastMCP(..., token_verifier=<TokenVerifier>,
auth=AuthSettings(issuer_url="<external AS>", resource_server_url="https://getbiblio.app/mcp", required_scopes=[...]))`
and **omit** `auth_server_provider`. That makes the SDK a pure Resource Server
— no authorize/token/register endpoints to implement. The canonical example is
**`examples/servers/simple-auth`** in the python-sdk repo (RS + an
`IntrospectionTokenVerifier` doing RFC 7662 introspection against the external
AS, over streamable-http). You write a `verify_token()`; you do not write
OAuth.

**Inside a tool, get the user** via
`from mcp.server.auth.middleware.auth_context import get_access_token` →
`get_access_token()` returns the `AccessToken` (`.subject`, `.client_id`,
`.scopes`, `.claims`). Key your per-user `Client` cache off `.subject`. (Only
populated when `token_verifier` is configured.)

**Pitfalls to honor:**

- `RemoteAuthProvider` is **only in the standalone `fastmcp` v2 package, NOT
  in the official `mcp` SDK we pin.** Don't import it. (Real fork in the road:
  stay on official `mcp` as a hand-wired RS, _or_ adopt standalone `fastmcp`
  v2 for its first-class IdP-provider integrations — a dependency swap, see
  open questions.)
- **Spec MUSTs to satisfy:** clients send RFC 8707 `resource` on every auth +
  token request; the server **MUST validate the token audience** and **MUST
  NOT** accept or forward tokens minted for anything else (anti
  confused-deputy / no token passthrough). Never forward the user's IdP token
  to the BiblioCommons gateway — the gateway auth is the separate card/PIN
  session.
- **Claude's fixed redirect URI** (if you skip DCR and pre-register): hosted
  surfaces (web/desktop/mobile) use `https://claude.ai/api/mcp/auth_callback`;
  OAuth client name is `Claude`. Claude Code uses a loopback redirect.

### 3a. Discovery metadata — mostly handled by the SDK now

The "well-known mounting gotcha" from earlier drafts is largely solved:

- When `auth.resource_server_url` is set, the SDK **auto-serves** RFC 9728
  Protected Resource Metadata. The subtlety: it lives at the **path-suffixed**
  `/.well-known/oauth-protected-resource/mcp` (not bare root), so set
  `resource_server_url` to the **full URL including the `/mcp` path**
  (`https://getbiblio.app/mcp`) or clients discover the wrong resource
  (python-sdk issue #1264). That metadata's `authorization_servers` field
  points clients at the external IdP.
- `/.well-known/oauth-authorization-server` is the **IdP's** responsibility in
  RS mode — your server does not serve it (it's only auto-served when you pass
  `auth_server_provider`, i.e. when _you_ are the AS, which we're not).
- Only if you target a non-spec-compliant client that probes bare-root
  well-known do you need to add a manual root route on the parent Starlette
  app. Spec-compliant Claude follows the `WWW-Authenticate` /
  protected-resource chain, so the built-ins suffice.

### 4. Hosting

Python rules out Cloudflare Workers (Node-first). Target **Cloud Run** (matches
nextup) or **Fly/Railway**, behind a **Cloudflare-proxied** custom domain so
DNS/TLS/edge sit in one place:

- Custom domain: `getbiblio.app` (apex) → the service.
- Containerize (Dockerfile), `$PORT` from the platform, secrets via the
  platform's secret manager (Cloud Run + Secret Manager, or Fly secrets).
- **Must be reachable from Anthropic's IP ranges over the public internet** —
  no VPN/private network. Verify whether the current connector docs require
  allowlisting specific Anthropic inbound CIDRs and capture the live list.

### 5. Favicon / connector icon — CONFIRMED mechanism

Claude renders each connector's icon via **Google's favicon service, keyed on
the registrable apex domain**:

```
https://www.google.com/s2/favicons?domain=<apex>&sz=32
```

Confirmed from live connectors (2026-05-28): `domain=craft.do`,
`domain=figma.com`, `domain=rewind.rest` — note it strips to the **registrable
apex**, not the subdomain (rewind's MCP server is at `mcp.rewind.rest` but the
icon lookup uses `rewind.rest`). The earlier Anthropic tracker thread
([#152](https://github.com/anthropics/claude-ai-mcp/issues/152)) about a
"generic globe" was about a different path (the MCP `icons` field / a direct
`/favicon.ico` fetch); the **apex-favicon-via-Google-s2 path works**, which is
why rewind/clickwheel show real icons.

**This validates the dedicated-apex decision.** Because the lookup is
apex-keyed, hosting at `getbiblio.app` (apex) — or any `*.getbiblio.app`
subdomain — yields the `getbiblio.app` icon, **distinct from clickwheel's**.
What we must do: ensure `https://www.google.com/s2/favicons?domain=getbiblio.app&sz=32`
returns _our_ icon, which means **the apex `getbiblio.app` must serve a
favicon that Google's crawler can find** (a `/favicon.ico` and/or
`<link rel="icon">` on the apex root, publicly fetchable — Google's crawler is
unauthenticated, so this route stays open even though `/mcp` + OAuth are
gated). Expect up to ~a day of Google cache lag before it appears in Claude.
See tracker Phase 4 for the task breakdown.

### 6. Platform constraints to design within (from current connector docs)

- **Streamable HTTP only** for new servers; legacy HTTP+SSE is deprecated.
- **Tool result cap ~150,000 characters** on claude.ai/Desktop — relevant for
  large `search` / `list_holds` payloads; paginate/trim.
- **300-second (5 min) tool timeout** on claude.ai/Desktop.
- **Adding a connector is web-first:** users add custom connectors on
  **claude.ai web** (Settings → Connectors → Add custom connector); it then
  **syncs to the iOS app**. You cannot add a connector by URL from the phone.
- **Free tier = 1 custom connector**; on Team/Enterprise only **Owners** can
  add connectors (members then enable).

## Milestones

1. **HTTP transport + read-only catalog, single hardcoded library, fully
   authless.** Claude supports authless connectors, so this needs _no auth at
   all_ — not even a connector token. Prove the mobile connector attaches
   (added on web, synced to phone) and `search`/`availability`/`list_branches`
   work end-to-end. De-risks the whole transport+hosting story before any
   auth.
2. **OAuth 2.1 as a Resource Server, delegating to a managed IdP**, per-user
   `{library, card, pin}`, authenticated tools (`place_hold`,
   `place_digital_hold`, `list_holds`, `ready_for_pickup`, `borrow_digital`,
   `cancel_hold`, `list_loans`, `renew_loan`, `check_in_loan`,
   `library_health`). Pick the IdP and the credential-storage model first.
3. **Hardening:** session-cache TTL, per-user rate limiting,
   encryption-at-rest review, credential-deletion path, `/healthz`, apex
   favicon (§5), Anthropic IP-allowlist if required.

## Effort

- Milestone 1: ~1–2 days (transport swap + container + domain + Inspector;
  authless so no auth work).
- Milestone 2: **~2–4 days** (down from the earlier ~4–7 day estimate — RS +
  managed IdP replaces hand-rolled OAuth). Bulk of remaining cost is the
  credential store + per-user `Client` cache + the consent/settings page for
  capturing library creds, not OAuth plumbing.
- Milestone 3: ~2–3 days.

## Open questions

- **Credential-storage model:** custodian (persist encrypted) vs per-session
  (never persist)? Security + UX call for the owner before milestone 2.
  Default recommendation: per-session for v1, custodian only if reconnect
  friction proves unacceptable.
- **Which managed IdP** (WorkOS / Auth0 / Clerk / Stytch / Descope / other),
  and **official `mcp` SDK as hand-wired RS vs standalone `fastmcp` v2** for
  its first-class IdP integrations? The latter is a dependency swap away from
  the pinned official SDK — weigh integration convenience vs staying on the
  pinned stack.
- **Grant/credential store backend:** Firestore? Cloud SQL? Redis w/
  encryption? Must support TTL + encryption-at-rest.
- **BiblioCommons / library Terms of Service.** Hosting a _multi-user_ proxy
  that stores patrons' card numbers + PINs and drives holds on their behalf is
  a materially different posture than a single-user local tool. **Check SPL /
  BiblioCommons ToS before going multi-user beyond yourself.** Real blocker,
  not a footnote.
- **Favicon on iOS** — reconfirm per §5 before doing any icon work.
- **Anthropic inbound IP allowlist** — does the current connector setup
  require it for Cloud Run / Fly? Capture the live CIDR list if so.

## Dependencies / blockers

- `getbiblio.app` registered (done) and pointed at Cloudflare DNS.
- A hosting account (Cloud Run / Fly) + container build in CI.
- A managed IdP account (milestone 2).
- ToS check (above) before any non-owner users.
- No code blockers — the tool layer is already transport-agnostic and
  `client.py` is already instance-per-library.

## Verification (owner-owned — cannot be fully done in-repo)

An in-repo agent can get to "MCP Inspector passes against the local
streamable-http endpoint" and "container deploys + `/healthz` is green." It
**cannot** declare victory — the real test needs the owner:

1. `npx @modelcontextprotocol/inspector` against the local HTTP endpoint —
   tools list + a read-only `search` call succeed.
2. Deploy; for milestone 2 confirm
   `getbiblio.app/.well-known/oauth-protected-resource/mcp` resolves over
   HTTPS and its `authorization_servers` points at the IdP.
3. **Add the connector on claude.ai web** (`https://getbiblio.app/mcp`),
   complete the OAuth flow, then **confirm on the phone** that it synced and
   tools appear + a `search` returns. (You cannot add by URL from the phone.)
4. Confirm an authenticated `list_holds` returns _your_ holds (per-user creds
   wired correctly via `get_access_token().subject` → your store, not a shared
   session).
5. Confirm the connector icon renders as the `getbiblio.app` favicon — i.e.
   `https://www.google.com/s2/favicons?domain=getbiblio.app&sz=32` returns our
   icon (allow ~a day for Google's crawler), distinct from clickwheel's.

## What changed in this revision (2026-05-28 validation)

- **Architecture flip:** Resource-Server-delegating-to-managed-IdP replaces
  "run your own OAuth 2.1 server." MCP spec 2025-06-18 split the AS/RS roles;
  the official SDK supports RS mode directly (`token_verifier` + `AuthSettings`
  without `auth_server_provider`; see `examples/servers/simple-auth`). DCR is
  now optional. Milestone 2 effort estimate dropped accordingly.
- **Milestone 1 is authless** — Claude supports authless connectors.
- **Favicon mechanism confirmed** (corrected again 2026-05-28 after owner
  supplied the live URLs): Claude uses `google.com/s2/favicons?domain=<apex>&sz=32`,
  keyed on the registrable apex. The apex-domain icon rationale holds; serve a
  crawlable favicon at `getbiblio.app`.
- **"Add on phone" corrected** to "add on web, syncs to phone."
- **SDK details corrected:** default path `/mcp`; protected-resource metadata
  auto-served at the path-suffixed well-known (set `resource_server_url` to the
  full `/mcp` URL); `RemoteAuthProvider` is a `fastmcp`-only symbol; prefer
  `stateless_http=True`; per-user identity via `get_access_token()`.
- **Platform constraints added:** 150k-char result cap, 300s timeout, Free=1
  connector, Team/Enterprise owner-only, possible IP allowlist.
- **Code audit confirmed** `client.py` is already instance-per-library and the
  read-only tools need no auth; the one refactor locus is
  `server.py:_ensure_client()`.
