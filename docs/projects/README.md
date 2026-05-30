# Project briefs

Each file in this folder is a self-contained pitch for a piece of work — some shipped, some active, some still parked. They're not specs — they're "if I sat down for an afternoon, here's what I'd do" briefs.

See [`../roadmap.md`](../roadmap.md) for the index that links here.

## Where things stand (as of v0.5.0, 2026-05-29)

The remote/mobile connector is **shipped and live** — deployed to Fly, WorkOS single-user auth on, working on iOS, and rendering inline UI cards. With that done, the active focus is three things:

1. **Resume the docs site (Mintlify).** Fully built in-repo (`docs-site/`), hosting is **paused** on Mintlify's one-site-per-account limit — owner-gated, needs contacting Mintlify. See [`docs-site/TRACKER.md`](docs-site/TRACKER.md) (Phase 3 + the once-unblocked setup steps) and [`docs-site/DEFERRED.md`](docs-site/DEFERRED.md).
2. **Iterate on the UI cards.** Cards render in-product now; the polish work (iOS flash/corners, theming, status visuals, digital-cover CDN allow-list) is milestone 4 in [`preview-cards.md`](preview-cards.md) — **active**.
3. **Other followups.** The big catalog/loan feature briefs below (renew, ready-for-pickup, bulk holds, digital queue holds) have all **shipped** — what's left is smaller: capture a real renewal-failure response to tighten error classification, and the genuinely-unbuilt v1.1 items **suspend/unsuspend holds** and **change pickup branch on an existing hold**. The deeper backlog (recommendations, multi-library, multi-user) lives in [`../roadmap.md`](../roadmap.md).

## Format

Every brief follows roughly this template:

- **Goal** — one sentence, user-facing if possible.
- **Why** — what the user (or contributor) gets out of it.
- **Approach** — high-level steps; not a spec, but enough that someone else could pick it up.
- **Effort** — rough time, "if no surprises."
- **Open questions** — known unknowns.
- **Dependencies / blockers** — what has to be in place first.

Briefs graduate to actual issues when someone's ready to work on them.

## Current set

| Brief                                                                                           | Status         | Notes                                                                                                                                                              |
| ----------------------------------------------------------------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [Remote MCP — mobile connector](remote-mcp-mobile.md) ([tracker](remote-mcp-mobile-tracker.md)) | ✅ shipped     | Live on Fly at `getbiblio.app/mcp`, WorkOS single-user auth, working on iOS. Followups doc is closed; see [followups](remote-mcp-mobile-followups.md).             |
| [Preview cards (inline UI bundles)](preview-cards.md)                                           | 🔵 active (m4) | Cards render in-product (v0.5.0). Milestones 1–3 + rendering shipped; **milestone 4 (polish) is the active work** — iOS flash/corners, theming, status, cover CDN. |
| [Docs site (Mintlify)](docs-site/README.md) ([tracker](docs-site/TRACKER.md))                   | ⏸️ paused      | Fully built in-repo; **hosting paused** on Mintlify's 1-site-per-account limit (owner-gated). Resume steps in the tracker.                                         |
| [Renew loans](renew-loans.md)                                                                   | ✅ shipped     | `renew_loan(checkout_ids, dry_run)` — bulk PATCH, v0.3.0 / refactored v0.4.0. Leftover: capture a real failure response to tighten error classification.           |
| [Ready-for-pickup tool](ready-for-pickup.md)                                                    | ✅ shipped     | `ready_for_pickup()` — filters `list_holds` to `READY_FOR_PICKUP`; renders the holds card.                                                                         |
| [Bulk hold operations](bulk-operations.md)                                                      | ✅ shipped     | All three: `cancel_hold(holds, dry_run)`, `place_hold(bib_ids, …)`, `place_digital_hold(bib_ids, …)` — the v0.4 "list-accepting only" mutation refactor.           |
| [Public-readiness CI](public-readiness-ci.md)                                                   | 🔁 continuous  | Triage of CI/tooling items through "would this help an OSS contributor" lens.                                                                                      |

**Genuinely unbuilt** (no brief yet, see [`../roadmap.md`](../roadmap.md) v1.1): **suspend/unsuspend holds** and **change pickup branch on an existing hold** — neither has a tool. ("Digital queue holds" from v1.1 shipped as `place_digital_hold`.)
