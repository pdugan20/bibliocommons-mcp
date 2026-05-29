# Project briefs

Each file in this folder is a self-contained pitch for a piece of work the project hasn't done yet. They're not specs — they're "if I sat down for an afternoon, here's what I'd do" briefs.

The current set is what we set aside while shipping v0.2.0. See [`../roadmap.md`](../roadmap.md) for the index that links here.

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

| Brief                                                                                           | Tier       | Notes                                                                                                                                                                                         |
| ----------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Renew loans](renew-loans.md)                                                                   | v1.2       | Single endpoint to discover + wire.                                                                                                                                                           |
| [Ready-for-pickup tool](ready-for-pickup.md)                                                    | v1.2       | Filter on existing data; small ergonomics win.                                                                                                                                                |
| [Bulk hold operations](bulk-operations.md)                                                      | v1.2       | Cancel is already bulk on the wire; placement is N×1.                                                                                                                                         |
| [Preview cards (inline UI bundles)](preview-cards.md)                                           | v2.x       | Big one. Standing up a `web/` workbench like clickwheel and rewind.                                                                                                                           |
| [Public-readiness CI](public-readiness-ci.md)                                                   | continuous | Triage of CI/tooling items through "would this help an OSS contributor" lens.                                                                                                                 |
| [Remote MCP — mobile connector](remote-mcp-mobile.md) ([tracker](remote-mcp-mobile-tracker.md)) | v2.x       | Streamable HTTP, multi-user, hosted at `getbiblio.app`. Resource-Server + managed IdP (not own OAuth server); authless read-only M1. Subsumes roadmap's multi-library + no-credentials modes. |
