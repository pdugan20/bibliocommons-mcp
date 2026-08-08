# Project: Remote MCP — run as a mobile custom connector (multi-user)

> **Status: LIVE (2026-05-29).** Deployed to Fly at `https://getbiblio.app/mcp`
> (always-on, bluegreen, TLS) in authless read-only mode. M1–M3 code merged;
> single-user mode built. The 3 remaining items (favicon, single-user auth
> activation, on-device acceptance) are tracked in
> [`remote-mcp-mobile-followups.md`](remote-mcp-mobile-followups.md). This brief
> is the architecture record; it is intentionally self-contained — the
> reference servers it draws on (`rewind`, `nextup-backend-mcp`) live in
> _other repos_ you can't see, so their relevant patterns are extracted inline.
>
> **Validated 2026-05-28** against the live Claude connector docs, the MCP
> authorization spec (2025-06-18 + 2025-11-25 revisions), and the installed
> `mcp` 1.27.1 SDK source. The validation changed the architecture materially
> — see **"What changed in this revision"** at the bottom if you read an
> earlier draft.
>
> **SDK update 2026-07-28:** the implementation has moved to official
> `mcp>=2,<3`, `MCPServer`, and the official MCP Apps extension. It negotiates
> MCP 2026-07-28 while retaining earlier-protocol compatibility. The 1.27.1
> details below remain as the historical record for the original deployment;
> current transport settings are passed to `run()` / the ASGI app rather than
> the server constructor.
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

We replicate that shell around the existing MCP tool definitions. The
tools themselves barely change. **Note:** rewind ran its own OAuth provider
(`@cloudflare/workers-oauth-provider`) because it predates the spec change
below — we should _not_ copy that; see the auth section.

## Approach

### 1. Add a Streamable HTTP entry point (keep stdio)

`mcp` here is the official `modelcontextprotocol/python-sdk` v2
(`pyproject.toml` pins `mcp>=2,<3`), which supports
`mcp.run(transport="streamable-http")` and exposes an ASGI app via
`mcp.streamable_http_app()` (returns a Starlette app) for when you need
custom middleware or extra routes (`/healthz`, favicon, root-level
well-known).

In `server.py:main()` (currently stdio-only), add a transport switch — do
**not** remove stdio; local Claude Code still uses it:

- `bibliocommons-mcp` (no args) → stdio, unchanged.
- `bibliocommons-mcp serve --http` (or `BIBLIOCOMMONS_MCP_TRANSPORT=http`) →
  Streamable HTTP bound to `0.0.0.0:$PORT` (Cloud Run sets `$PORT`).

**Current SDK v2 specifics (the original 1.27.1 behavior is preserved where
noted):**

- The Streamable HTTP endpoint **defaults to `/mcp`, not `/`**
  (unchanged from the v1 deployment). Decide your public path deliberately;
  the current server passes host, port, and transport security explicitly to
  `MCPServer.run()`.
- For a multi-tenant remote service, run **`stateless_http=True`**
  (passed to `run()` / `streamable_http_app()` in SDK v2): no
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
{library, card, pin}`. **Decided 2026-05-28: per-session + warm instance** (rationale + the empirical BC-session finding are under Open questions). The two models that were weighed:

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

**What the official `mcp` SDK gives you for RS mode:** construct
`MCPServer(..., token_verifier=<TokenVerifier>,
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
  surfaces (web/desktop/mobile) use `https://claude.ai/api/mcp/auth_callback`
  (docs note this may move to `https://claude.com/...` — register both if your
  IdP allows); OAuth client name is `Claude`. Claude Code uses a loopback
  redirect.

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

**Decided 2026-05-29: Fly.io** — an always-on single machine is the natural
home for the warm in-memory per-session cache (cheapest, simplest deploy);
Cloud Run's scale-to-zero/autoscale model is the opposite of "keep one warm
stateful box." Config committed as [`fly.toml`](../../fly.toml); step-by-step
in [`docs/deploy-fly.md`](../deploy-fly.md). Python rules out Cloudflare Workers
(Node-first), so Cloudflare stays the DNS/edge front, not the host:

- Custom domain: `getbiblio.app` (apex) → the Fly app, via Cloudflare.
- Containerize (Dockerfile), `internal_port` 8000, WorkOS API key via
  `fly secrets set`.
- **Always-on machine** (`auto_stop_machines = "off"`,
  `min_machines_running = 1`). The per-session model keeps each user's
  authenticated BC cookie jar in memory; a scale-to-zero cold start would wipe
  it and force PIN re-entry. Always-on → re-auth is ~per-deploy instead.
  (~$3–5/mo on shared-cpu-1x.)
- **Must be reachable from Anthropic's cloud over the public internet** — no
  VPN/private network (connector traffic comes from Anthropic's cloud, not the
  user's device). Anthropic publishes a stable outbound range to allowlist,
  `160.79.104.0/21` ([ip-addresses doc](https://platform.claude.com/docs/en/api/ip-addresses),
  "won't change without notice"). **Behind a Cloudflare proxy the Cloud Run/Fly
  origin only sees Cloudflare IPs**, so enforce the Anthropic allowlist at the
  Cloudflare **edge** (WAF/IP rule) as defense-in-depth, never on the origin.
  OAuth (§3) is the actual access gate; the allowlist just rejects non-Claude
  MCP clients. (Anthropic also offers outbound-only "MCP tunnels" to avoid
  inbound exposure entirely.)

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

**Resolved 2026-05-28** (rationale kept here; statuses in tracker Phase 0):

- **Credential model → per-session + warm instance.** Hold each user's
  authenticated BC cookie jar in memory only; **never persist the raw PIN**.
  Empirical finding (from the login cassettes): BC issues a ~1-year session
  cookie (`session_id`, `max-age=31536000`) plus a 15-min access token that
  auto-refreshes from it — so on a warm instance the PIN is re-entered only
  ~per deploy. Documented upgrade if that friction bites: persist the
  _encrypted session cookie_ (PIN ~yearly), still never the raw PIN. Full
  PIN-custodian is strictly dominated by that and is not used.
- **IdP → WorkOS AuthKit.** 1M-MAU free tier; DCR + CIMD on free (Claude's
  connector auto-registers, no manual client ID/secret); native RFC 8707
  audience binding; RFC 9728 PRM; standard JWKS/JWT.
- **SDK track → stay on official `mcp`.** Hand-wire a JWKS `TokenVerifier`
  (fetch WorkOS JWKS; validate signature + `aud` + expiry) instead of adopting
  `fastmcp` v2 for its turnkey provider — no dependency swap, IdP-agnostic, no
  migration risk to the tested codebase. The ~80 lines are a one-time cost.
- **Grant/credential store backend → none for v1.** Per-session is in-memory
  (the TTL'd client cache), so no Firestore/Cloud SQL/Redis until/unless the
  session-cookie-persistence upgrade is taken (then: a small encrypted,
  TTL-capable store).
- **Anthropic IP allowlist → resolved (§4):** allowlist `160.79.104.0/21` at
  the Cloudflare edge as defense-in-depth; OAuth is the gate.

Still open:

- **BiblioCommons / library Terms of Service.** Even per-session, you drive
  holds on patrons' behalf — a different posture than a single-user local
  tool. Per-session _not storing PINs_ softens it (you hold only a transient
  session, never the reusable secret), but **check SPL / BiblioCommons ToS
  before going multi-user beyond yourself.** Real blocker, not a footnote.
- **Favicon on iOS** — reconfirm per §5 before doing any icon work.

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
