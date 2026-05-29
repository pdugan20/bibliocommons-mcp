# Followups / deferrals: Remote MCP — mobile connector

> Companion to [`remote-mcp-mobile-tracker.md`](remote-mcp-mobile-tracker.md).
> Reconciled 2026-05-29 after the live Fly deploy. Scope is **single-user**
> (the owner, the owner's own card) — multi-user items are parked, not active.

## Status: live

`https://getbiblio.app/mcp` is **deployed and serving** (Fly, always-on,
bluegreen, TLS via Let's Encrypt) in **authless read-only** mode. The remaining
work is: ship the favicon, flip on single-user auth so account tools work, and
do the on-device acceptance test.

## Outstanding (the only things left)

| #   | Item                                                                                                                                                                                                                                  | Owner / repo          | Notes                                                         |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- | ------------------------------------------------------------- |
| F1  | **Favicon** — _done & deployed_ (book icon serving at the apex); awaiting Google's crawl, then verify it renders in Claude (re-check `google.com/s2/favicons?domain=getbiblio.app`)                                                   | repo ✓ / owner verify | currently still Google's globe fallback (~1 day lag)          |
| F2a | **Secrets** — `WORKOS_CLIENT_ID`, `BIBLIOCOMMONS_CARD/PIN`, `BIBLIOCOMMONS_MCP_SINGLE_USER=1` — _done_ (set from config, `/mcp` now 401)                                                                                              | done ✓                | auth live; card protected                                     |
| F2b | **WorkOS dashboard** — Connect → Configuration: enable **DCR + CIMD** and add **Resource Indicator** `https://getbiblio.app/mcp`                                                                                                      | owner                 | 2 toggles; lets Claude register + makes tokens audience-bound |
| F2c | **Owner allow-list** — after first login, set `fly secrets set BIBLIOCOMMONS_MCP_OWNER_SUBJECTS=<your WorkOS user_id>` (the 401 message / WorkOS → Users shows the id). Code-enforced lockdown — only the owner's id reaches the card | owner → repo          | replaces a fuzzy WorkOS sign-up toggle; fail-safe until set   |
| F3  | **Final acceptance** — add `https://getbiblio.app/mcp` as a connector on claude.ai web → confirm on iOS → verify `search` + a checkout work                                                                                           | owner                 | the deliberate last step                                      |

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
