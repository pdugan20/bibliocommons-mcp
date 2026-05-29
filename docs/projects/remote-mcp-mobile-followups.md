# Followups / deferrals: Remote MCP — mobile connector

> Companion to [`remote-mcp-mobile-tracker.md`](remote-mcp-mobile-tracker.md).
> The working rule is **don't defer unless necessary** — an item lands here
> only when it genuinely can't be completed by an in-repo agent right now.
> Each row says *what blocks it* and *what unblocks it*, so nothing is lost.
>
> When a deferral clears, do the task, check it off in the tracker, and move
> its row here to **Resolved** (or delete it).

## Why these are deferred (not just un-done)

Track A (the Milestone-1 *code*) is being executed in-repo and does **not**
appear here. Everything below needs the **owner** for a reason an agent can't
satisfy: an account/payment, a secret, DNS control, the physical phone, or a
legal/ToS judgment.

## Open deferrals

| Tracker # | Item | Blocked on (owner action) | Unblocks | Gates |
|-----------|------|---------------------------|----------|-------|
| 0.2 | Credential-storage model (per-session vs custodian) | A design decision only the owner should make (security/UX tradeoff) | Phase 2 cred capture (2.9) | Milestone 2 |
| 0.3 | Choose IdP + create account (WorkOS/Auth0/Clerk/Stytch/Descope) | Account signup, possibly paid | 2.1–2.3 RS wiring | Milestone 2 |
| 0.5 | Hosting account/project (Cloud Run / Fly / Railway) | Account signup, billing | 1.9 deploy | Milestone 1 deploy |
| 0.6 | Credential/grant store backend (Firestore / Cloud SQL / Redis) | Provisioning + billing; depends on 0.2 | 2.9 cred store | Milestone 2 |
| 0.7 | **BiblioCommons / SPL ToS check** for a multi-user proxy storing card+PIN | Legal/ToS reading + judgment | Any non-owner user | **Hard gate, Milestone 2+** |
| 1.8 (push) | CI pushes the container image to a registry | Registry creds / CI secrets | 1.9 deploy | Milestone 1 deploy |
| 1.9 | Deploy container to the host | Needs 0.5 | 1.10, connector attach | Milestone 1 |
| 1.10 | Point `getbiblio.app` → service via Cloudflare | DNS control (owner has domain) | 1.11 attach | Milestone 1 |
| 1.11 | Add connector on claude.ai web | The deployed URL (1.9/1.10) + owner's Claude account | 1.12 | Milestone 1 |
| 1.12 | Confirm sync + `search` on the **iOS app** | Physical phone | M1 acceptance | Milestone 1 |
| 1.13–1.14 | Seed apex favicon + confirm Google s2 serves it | Needs apex live (1.10) | Phase 4 polish | cosmetic |
| 2.13 | Owner completes OAuth flow; `list_holds` returns owner's holds | Phone/web + IdP live | M2 acceptance | Milestone 2 |
| 2.14 | Second account connects, sees their own holds (isolation proof) | A second test account/person | M2 acceptance | Milestone 2 |

## Resolved

_(none yet — move rows here as deferrals clear)_

## Notes

- **Nothing in Phase 0 blocks Milestone 1.** M1 is authless + single hardcoded
  library, so the IdP/cred-model/store decisions can be made on the owner's own
  timeline without stalling the code.
- **0.7 (ToS) is the one true blocker for going multi-user beyond the owner** —
  the code can be fully built and even deployed for the owner's own use before
  it's resolved, but no third party gets onboarded until it is.
