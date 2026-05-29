# Followups / deferrals: Remote MCP — mobile connector

> Companion to [`remote-mcp-mobile-tracker.md`](remote-mcp-mobile-tracker.md).
> The working rule is **don't defer unless necessary** — an item lands here
> only when it genuinely can't be completed by an in-repo agent right now.
> Each row says _what blocks it_ and _what unblocks it_, so nothing is lost.
>
> When a deferral clears, do the task, check it off in the tracker, and move
> its row to **Resolved** (or delete it).

## Owner action items (the short list)

These need **you** — an account, a secret, DNS, the phone, or a ToS judgment.
Roughly in order:

1. **WorkOS account** (done). Confirm DCR/CIMD on, plus Resource Indicator
   `https://getbiblio.app/mcp`. Token validation uses the public JWKS (client
   id `WORKOS_CLIENT_ID`, issuer `https://api.workos.com`) — no secret needed.
2. **WorkOS API key for the settings page.** The `/account` browser flow needs
   the confidential **`sk_…` API key** as a server secret (`WORKOS_API_KEY`) —
   the only secret this server holds — plus a **web-app redirect URI**
   registered in WorkOS: `https://getbiblio.app/account/callback`. (Optional
   `WEB_SESSION_SECRET`; defaults to a value derived from the API key.)
3. **Pick a warm host** (Cloud Run `min-instances=1`, or Fly always-on) and
   create the project. Warm is required so the per-session cookie cache
   survives — see tracker 0.2/0.5.
4. **Add registry/CI secrets** so CI can push the image (or push manually).
5. **Point `getbiblio.app`** at the service via Cloudflare; confirm
   `https://getbiblio.app/mcp` + `/healthz` resolve over HTTPS.
6. **ToS check** — read SPL / BiblioCommons terms before onboarding anyone
   but yourself (hard gate for multi-user). Per-session softens it (no PINs
   stored) but doesn't remove it.
7. **On your phone / claude.ai:** add the connector on web, confirm it syncs
   to iOS, complete the WorkOS login, set up your card at `/account`, and
   verify `list_holds` returns _your_ holds.
8. **Seed the apex favicon** (placeholder is fine) so Google's `s2/favicons`
   serves it; confirm the icon renders, distinct from clickwheel.

## Open deferrals (detail)

| Tracker #  | Item                                                                      | Blocked on (owner action)                            | Unblocks               | Gates                       |
| ---------- | ------------------------------------------------------------------------- | ---------------------------------------------------- | ---------------------- | --------------------------- |
| 0.3        | Create the **WorkOS** account; enable AuthKit + DCR; note issuer/JWKS URL | Account signup (free tier)                           | 2.1–2.3 RS wiring      | Milestone 2                 |
| 0.5        | Create a **warm** host project (Cloud Run min-instances=1 / Fly)          | Account signup, billing                              | 1.9 deploy             | Milestone 1 deploy          |
| 0.7        | **BiblioCommons / SPL ToS check** for a multi-user proxy                  | Legal/ToS reading + judgment                         | Any non-owner user     | **Hard gate, Milestone 2+** |
| 1.8 (push) | CI pushes the container image to a registry                               | Registry creds / CI secrets                          | 1.9 deploy             | Milestone 1 deploy          |
| 1.9        | Deploy container to the warm host                                         | Needs 0.5                                            | 1.10, connector attach | Milestone 1                 |
| 1.10       | Point `getbiblio.app` → service via Cloudflare                            | DNS control (owner has domain)                       | 1.11 attach            | Milestone 1                 |
| 1.11       | Add connector on claude.ai web                                            | The deployed URL (1.9/1.10) + owner's Claude account | 1.12                   | Milestone 1                 |
| 1.12       | Confirm sync + `search` on the **iOS app**                                | Physical phone                                       | M1 acceptance          | Milestone 1                 |
| 1.13–1.14  | Seed apex favicon + confirm Google s2 serves it                           | Needs apex live (1.10)                               | Phase 4 polish         | cosmetic                    |
| 2.13       | Owner completes WorkOS login; `list_holds` returns owner's holds          | Phone/web + IdP live                                 | M2 acceptance          | Milestone 2                 |
| 2.14       | Second account connects, sees their own holds (isolation proof)           | A second test account/person                         | M2 acceptance          | Milestone 2                 |

## Resolved

Decisions made 2026-05-28 (rationale in brief Open questions / tracker Phase 0):

- **0.2 credential model → per-session + warm instance** (never persist the
  raw PIN; BC session lasts ~1yr so re-auth is ~per-deploy).
- **0.3 IdP → WorkOS AuthKit** (the _decision_; account creation is still an
  owner item above).
- **0.4 SDK track → stay on official `mcp`**, hand-wire a JWKS TokenVerifier.
- **0.6 creds store → N/A for v1** (per-session is in-memory).
- **0.8 IP allowlist → resolved** (`160.79.104.0/21` at the Cloudflare edge;
  OAuth is the gate).

## Notes

- **Nothing in Phase 0 blocks Milestone 1.** M1 is authless + read-only, so it
  deploys before any auth/IdP work.
- **0.7 (ToS) is the one true blocker for going multi-user beyond the owner** —
  the code can be fully built and deployed for the owner's own use first; no
  third party is onboarded until it's resolved.
