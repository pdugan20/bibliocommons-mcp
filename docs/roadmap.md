# Roadmap

What's planned, what's deliberately deferred, and what's a maybe. None of these dates are hard — this is "what I'd build next if I sat down for an afternoon."

This is intentionally exhaustive — easier to delete than to remember. See ["Honest categorization"](#honest-categorization) at the bottom for the "what actually matters" view. Items linked to a brief have a fleshed-out plan in [`projects/`](projects/).

## v1.1 — fill in digital + suspend

- **Digital queue holds.** `place_digital_hold(bib_id)` — currently the gateway 500s on a partial body shape. The blocker is a `format` enum field in `materialParams`. We have the full `DigitalFormatType` enum from a Jackson type-mismatch probe (see [`format-codes.md`](format-codes.md)) but never captured a successful real-browser POST for the join-waitlist path. One DevTools network capture from someone with an unavailable digital item on an SPL account would close this.
- **Suspend / unsuspend holds.** The `suspend` action exists on hold objects but the endpoint shape isn't probed. Should be a sibling of `cancel_hold` (likely PUT or PATCH on `/holds/{id}`).
- **Pickup-branch update on existing holds.** Bundle code references `UPDATE_PICKUP_LOCATION` — useful when you want to change pickup mid-queue.

## v1.2 — loans + status filters

- **[Renew loans](projects/renew-loans.md).** Distinct endpoint, untested. Most-asked-for missing feature once people start using this in earnest.
- **[Ready-for-pickup tool](projects/ready-for-pickup.md).** The holds list exposes status transitions — surface them as a tool that filters to `READY_FOR_PICKUP`.
- **[Bulk hold operations](projects/bulk-operations.md).** `cancel_holds(ids)` and `place_hold(bibs)`. The gateway's DELETE is already bulk-shaped; place is N×1. Mostly an MCP-side ergonomics tweak.

## v2.x — bigger swings

- **Multi-library mode.** Today, one MCP server instance speaks to one library. Multi-card households would benefit from a `library` argument on each tool, with config defining the default. Trade-off: per-library session caching gets more complex.
- **Better recommendations.** The catalog response includes `recommendations` and `userContent` entities we ignore. A `recommend(bib_id)` tool that cross-references your loans/holds with similar items would be a natural fit for AI clients.
- **Search-only / no-credentials mode.** Most read-only catalog endpoints work unauthenticated. A `read_only` config flag would let users explore a library's catalog without giving the server a PIN.

## Other BiblioCommons endpoints we never wired

- **Pay fines.** `/v2/libraries/{lib}/fines` returns the data; the mutation endpoint is untested. Sensitive — touches money, deliberate caution warranted.
- **Item-level holds.** Multi-volume sets use `placeItemHold` with a different POST path. We assume single-volume bibs.
- **Borrowing history.** BC API exposes opt-in history.
- **Saved searches and "for later" lists.** BC's user-content concept.
- **Full bib detail fetch.** We only do `/availability`; full metadata sits at a separate endpoint.
- **Subscription notifications.** "Notify me when available."
- **Cursor-based pagination.** We use 1-indexed `page=N` (fixed page size 25); BC may support cursors for better stable pagination.

## MCP server features deferred

| Feature                                                         | Why skipped                                                                                                                                 |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **`Context` param + `ctx.info()` / `ctx.report_progress()`**    | None of our 9 tools is slow enough to warrant progress reporting; would be ceremony without value.                                          |
| **`Context.elicit()` for mid-execution confirmation**           | `destructiveHint=True` annotation handles client-side confirmation in current clients.                                                      |
| **MCP `prompts`** (slash commands like `/library:plan-pickups`) | No natural workflow demanded one yet.                                                                                                       |
| **MCP `resources`** (server-provided URIs)                      | Tools cover everything; client support for resources is uneven.                                                                             |
| **`resource_template`** (`bibliocommons://bib/{id}`)            | Niche feature; mentioned in best-practices research.                                                                                        |
| **`Context.sample()`**                                          | Catalog servers rarely need server-side LLM sampling.                                                                                       |
| **[MCP Apps / inline UI bundles](projects/preview-cards.md)**   | Clickwheel does this for live sync progress; we don't have anything similar. Brief covers preview cards using `briefInfo.jacket` cover art. |
| **`dry_run` on `borrow_digital`**                               | Only added to `cancel_hold`; borrow is opt-in by definition.                                                                                |
| **Bulk operations**                                             | Single-item only currently. See v1.2 above.                                                                                                 |

## CI / tooling we considered but skipped

See [`projects/public-readiness-ci.md`](projects/public-readiness-ci.md) for the triaged version of this section: which of these to actually adopt if the project goes broader-OSS.

| Tool                                         | Status                                                                                                                                       |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **MCP Inspector CLI in CI**                  | Skipped — `tests/test_mcp_smoke.py` covers the same handshake validation in-process. Documented in `CONTRIBUTING.md` as a manual debug tool. |
| **`mcpdiff` schema snapshots**               | Skipped — adds maintenance burden for a project with no external schema consumers yet.                                                       |
| **`claude-code-lint` in CI**                 | Clickwheel runs `npx claude-code-lint@latest`; we don't. Worth adding.                                                                       |
| **Sentry MCP integration**                   | Skipped — overkill for v0.x personal use.                                                                                                    |
| **TestPyPI staging publish**                 | Clickwheel has `test-publish.yml`; we don't.                                                                                                 |
| **Live state-changing CI test**              | Cassettes cover reads; no CI test actually places/cancels a hold against a real account.                                                     |
| **Coverage threshold tighter than 60%**      | We're at 86% — could raise the floor to lock the gain in.                                                                                    |
| **Repo-level `claudelint`**                  | Your local `claudelint` skill is available; not wired into this repo's CI.                                                                   |
| **Pre-commit hook for credential leak grep** | Already in `.pre-commit-config.yaml`; never tested with a deliberate leak (could add a self-test).                                           |

## Docs / polish

- **Asciicast or screenshot in README.** Manual followup — record a Claude Desktop session with DevTools, host on asciinema.org, embed.
- **More entries in `docs/known-libraries.md`.** Only `seattle` + `sfpl` are listed; the issue template invites community reports.
- **Decide on `releasing.md` in Further reading.** Discussed earlier; still listed. Contributor-internal, arguably belongs only in CONTRIBUTING.
- **Per-error-message troubleshooting examples.** `docs/troubleshooting.md` is general; could expand with each new error users hit.
- **`examples/` directory** with sample MCP client configs (Claude Code, Claude Desktop, Cursor, Continue, Cline, Zed).
- **Architectural diagram.** `docs/architecture.md` has ASCII data flow; no visual.
- **Client-internals reference.** Architecture doc names endpoints but doesn't show the `Client` wrapper API.
- **"Add a new tool" contributing recipe.** Generic CONTRIBUTING; no walkthrough.

## Performance / scaling

- **Session caching across MCP server restarts.** Each restart logs in fresh; no on-disk session jar.
- **Branch list cache survives restart.** In-memory only; refetches on first call after restart.
- **Search result caching.** Live every call.
- **Retry / backoff for transient gateway errors.** Single attempt; gateway 5xx propagates as `ToolError`.
- **Rate limiting on our side.** None — burned login attempts during the spike, but the normal flow is gentle.

## Build / distribution

- **Standalone `fastmcp` 3.x migration.** Deliberately skipped — the official
  `mcp` SDK v2 server covers the current 13 tools, OAuth Resource Server, and
  MCP Apps requirements without a second server framework.
- **Beta / pre-release channel** (`bibliocommons-mcp==0.3.0a1`). None.
- **Docker image.**
- **Homebrew formula.**
- **`uv` / `rye` support docs.** Implicit (works because `pyproject.toml` is standard) but not documented.
- **Python 3.10 backport.** Pin is `>=3.11`; would need `from __future__` annotations + dropping some 3.11+ syntax.

## Multi-library / multi-tenant

- **Multi-library in one server instance.** Listed v2.x.
- **`library` argument on each tool.** Same — needs v2 multi-tenant design.
- **Read-only / no-credentials mode.** Listed v2.x.
- **Multiple credential profiles in one config file.** Today, one `[credentials]` block per file; multi-config needs the `BIBLIOCOMMONS_MCP_CONFIG` env var per server.

## Security / hardening

- **PAT rotation.** The `RELEASE_PLEASE_TOKEN` is still the one pasted in chat. One-time task; not really a roadmap item but tracked here so it doesn't get lost.
- **Cassettes contain `patdugan` username + `1142365317` userId in HTML bodies.** Acceptable for a personal repo but flag-worthy if shared.
- **No credential-rotation hook.** Re-run `init` to overwrite.
- **No backup before `init` overwrites.** Maybe worth a `.bak` copy on overwrite.
- **No explicit credential redaction in log lines.** Logging is sparse, but no filter exists.

## Explicit non-goals (deliberate, won't be in any version)

- **Account creation / sign-up flows.** Out of scope; the server assumes you already have a card.
- **Library staff features.** Catalog editing, item creation, patron management — wrong tool for the wrong audience.
- **Persistent caching layer (SQLite, Redis, ...).** Branch lists cached in-memory per process; everything else is live. If you need persistence, run a cache in front yourself.
- **GUI.** It's MCP. The client is the GUI.

## Honest categorization

| Bucket                            | Items                                                                                       |
| --------------------------------- | ------------------------------------------------------------------------------------------- |
| **Planned, real next work**       | Digital queue holds, suspend, renew, pickup-branch update, item-level holds (v1.1–v1.2).    |
| **Probably useful, low-priority** | Ready-for-pickup tool, recommendations, examples/ dir, asciicast in README.                 |
| **Worth doing soon-ish**          | `claude-code-lint` in CI, raise coverage floor, retry/backoff for transient gateway errors. |
| **Quietly fine to skip forever**  | Sentry, Docker, multi-library, MCP Apps UI bundles, Homebrew formula, Python 3.10 support.  |
| **One-time housekeeping**         | Rotate the `RELEASE_PLEASE_TOKEN` PAT.                                                      |
