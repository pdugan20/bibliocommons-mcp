# Followups / deferrals: Remote MCP — mobile connector

> Companion to [`remote-mcp-mobile-tracker.md`](remote-mcp-mobile-tracker.md).
> **Reconciled 2026-05-29 — SHIPPED.** Scope is **single-user** (the owner, the
> owner's own card) — multi-user items are parked, not active.

## Status: shipped ✅

The connector is **live, authed, and in use**: deployed to Fly (always-on,
bluegreen, TLS), WorkOS single-user auth on with the owner allow-list enforced,
added as a connector in Claude, **working on iOS**, pulling real holds/loans,
and rendering inline UI cards (see [`preview-cards.md`](preview-cards.md)).
There is **nothing outstanding** for this project — remaining UI polish lives in
the preview-cards brief, not here.

## Outstanding

None — all of F1–F3 are done.

## Done (former "outstanding")

| #   | Item                                                                                          | Result                                                                                               |
| --- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| F1  | **Favicon** — book icon at the apex + `/favicon.svg` routes                                   | done ✅ — apple-touch later dropped on purpose: Google's s2 flattens it to an opaque JPEG at 48/64px |
| F2a | **Secrets** — `WORKOS_CLIENT_ID`, `BIBLIOCOMMONS_CARD/PIN`, `BIBLIOCOMMONS_MCP_SINGLE_USER=1` | done ✅ — auth live, `/mcp` 401s without a token                                                     |
| F2b | **WorkOS dashboard** — DCR + CIMD + Resource Indicator                                        | done ✅ — Claude registered + connected, so this is confirmed                                        |
| F2c | **Owner allow-list** — `BIBLIOCOMMONS_MCP_OWNER_SUBJECTS=<owner WorkOS user_id>`              | done ✅ — set to the owner's id; only the owner reaches the card                                     |
| F3  | **Final acceptance** — connector on claude.ai, confirmed on iOS, `search` + holds/loans work  | done ✅ — verified in-product (5 holds pulled, cards render)                                         |

## Closed

**Done:**

- Deploy to Fly (always-on, bluegreen, swap, graceful shutdown) — live.
- Cloudflare DNS + Let's Encrypt cert — `getbiblio.app` resolves over HTTPS.
- M1 (HTTP transport + read-only catalog), M2 (WorkOS RS + per-user routing +
  /account page + single-user mode), M3 (TTL cache + audits), Fly hardening +
  infra linters (hadolint, taplo, `fly config validate`) — all merged.
- Local/Inspector verify — curl smoke + live `initialize` over the domain.

**Closed as not needed for single-user scope:**

- WorkOS API key + `/account` browser page — single-user uses the config card.
- Registry/CI image push — Fly remote-builds on `fly deploy`.
- Second-account isolation test — multi-user only.
- Rate limiting / output trimming / Anthropic IP allowlist — optional polish;
  the IP allowlist is moot while Cloudflare DNS is grey (not proxied).

**Downgraded:**

- **ToS** — the multi-user "custodian of patrons' PINs" concern doesn't apply
  to single-user with the owner's own card (same posture as the local stdio
  tool). Revisit only if going genuinely multi-user.

## If you later go multi-user

Parked, not deleted: set `WORKOS_API_KEY` + the `/account` redirect URI, drop
`BIBLIOCOMMONS_MCP_SINGLE_USER`, do the BiblioCommons/SPL ToS check, and verify
two accounts stay isolated. The code already supports it.
