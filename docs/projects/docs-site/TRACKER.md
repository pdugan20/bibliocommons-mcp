# Docs site — tracker

Phased task list. See [README.md](README.md) for the plan/decisions and
[DEFERRED.md](DEFERRED.md) for parked items.

**Legend** — Status: ✅ done · 🚧 in progress · ⬜ not started.
Owner: 🤖 in-repo (code/docs) · 🧑 owner-owned (Mintlify account / DNS).
**Discipline:** every not-started task names its blocker; no silent deferrals.

**Where we are:** Phase 0 done. Executing Phases 1–2 in-repo; Phase 3 (Mintlify
account + `docs.getbiblio.app`) is owner-owned; Phase 4 is cutover + listing.

---

## Phase 0 — Plan ✅

| ✓   | Owner | Task                                                                                                     |
| --- | ----- | -------------------------------------------------------------------------------------------------------- |
| ✅  | 🤖    | Research — clickwheel/rewind pattern, MCP-docs best practices, install deeplinks, llms.txt, MCP registry |
| ✅  | 🤖    | Inventory our CLI + 13 MCP tools (+ annotations) for the generated reference                             |
| ✅  | 🤖    | Plan + tracker + deferred docs in `docs/projects/docs-site`                                              |

---

## Phase 1 — Scaffold + narrative content ⬜

| ✓   | Owner | Task                                                                                      |
| --- | ----- | ----------------------------------------------------------------------------------------- |
| ⬜  | 🤖    | `docs.json` — nav (Guides + Reference tabs, Diátaxis), theme, contextual menu, domain     |
| ⬜  | 🤖    | `favicon.svg` + `logo/` (reuse the getbiblio book mark)                                   |
| ⬜  | 🤖    | `introduction.mdx` — overview / landing                                                   |
| ⬜  | 🤖    | `quickstart.mdx` — TUTORIAL                                                               |
| ⬜  | 🤖    | `install.mdx` — Claude Desktop / Claude Code / remote connector / Cursor + VS Code badges |
| ⬜  | 🤖    | `guides/` — search, holds, digital, loans, branches, recipes, self-host-remote            |
| ⬜  | 🤖    | `concepts/` — architecture, local-vs-remote, security                                     |
| ⬜  | 🤖    | `troubleshooting.mdx`                                                                     |
| ⬜  | 🤖    | `reference/configuration.mdx`                                                             |
| ⬜  | 🤖    | `changelog.mdx`                                                                           |

**Acceptance:** `mint broken-links` passes; nav resolves all pages.

---

## Phase 2 — Generated reference + anti-rot CI ⬜

| ✓   | Owner | Task                                                                                      |
| --- | ----- | ----------------------------------------------------------------------------------------- |
| ⬜  | 🤖    | `scripts/gen_mcp_reference.py` → `reference/mcp-tools.mdx` (13 tools + annotation badges) |
| ⬜  | 🤖    | `scripts/gen_cli_reference.py` → `reference/cli.mdx`                                      |
| ⬜  | 🤖    | CI **"Docs Reference Freshness"** — regenerate + fail on drift                            |
| ⬜  | 🤖    | CI **"Docs Links"** — `mint broken-links`                                                 |
| ⬜  | 🤖    | `make docs-reference` / `docs` / `docs-links` + CONTRIBUTING note                         |

**Acceptance:** generators idempotent; editing a tool without regenerating fails CI; links pass.

---

## Phase 3 — Hosting / deploy 🧑

| ✓   | Owner | Task                                                               |
| --- | ----- | ------------------------------------------------------------------ |
| ⬜  | 🧑    | Create the Mintlify project (free OSS), connect the GitHub repo    |
| ⬜  | 🧑    | Point `docs.getbiblio.app` CNAME per Mintlify; confirm auto-deploy |
| ⬜  | 🤖    | Confirm `llms.txt` + contextual menu live; spot-check nav/search   |

**Blocker:** needs a Mintlify SaaS account + DNS (owner).

---

## Phase 4 — Cutover + listing ⬜

| ✓   | Owner | Task                                                                       |
| --- | ----- | -------------------------------------------------------------------------- |
| ⬜  | 🤖    | Shrink `README.md` to a blurb + link to the docs site; add install badges  |
| ⬜  | 🤖    | `server.json` + list in the official MCP registry (`io.github.pdugan20/…`) |
| ⬜  | 🧑    | Live spot-check on `docs.getbiblio.app` (web + mobile)                     |

**Blocker:** Phase 4 live check needs Phase 3 done.
