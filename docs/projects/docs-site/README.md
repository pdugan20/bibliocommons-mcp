# Project: bibliocommons-mcp docs site

A real documentation site for bibliocommons-mcp at **`docs.getbiblio.app`**,
built docs-as-code with anti-staleness guarantees — mirroring the sibling
**clickwheel** docs site (near-identical shape: Python CLI + FastMCP server).

- **[TRACKER.md](TRACKER.md)** — phased task list (status, owner, blockers).
- **[DEFERRED.md](DEFERRED.md)** — explicitly parked / out-of-scope items.

## Goals

1. A discoverable, structured docs site — not just a README — for a Python CLI
   and MCP server that works against **any BiblioCommons library** (Seattle,
   SFPL, …), usable **locally (stdio)** or as a **remote/mobile connector**.
2. **Docs that can't silently rot.** The tool reference is generated from the
   live FastMCP instance and drift-checked in CI; links are validated in CI.
3. Authoring consistent with `rewind` / `clickwheel` (same Mintlify flow).

## Decisions (settled — don't re-litigate without new info)

- **Tool: Mintlify**, hosted free (OSS), at **`docs.getbiblio.app`** — the apex
  `getbiblio.app` stays the live MCP server + its minimal landing. Matches
  clickwheel; its intro page doubles as the landing, **no separate marketing
  site** (rewind's Astro `www` exists only because rewind.rest is a product
  with legal pages). Rejected: Cloudflare Pages + Astro Starlight (more setup).
- **Structure: Diátaxis** — Tutorial / How-to / Reference / Explanation, in
  separate tabs/groups (better for humans and AI assistants).
- **Audience = the OSS tool, not a hosted signup.** Docs teach _install locally_
  or _self-host your own instance_. `getbiblio.app` is the maintainer's personal
  instance (like `clickwheel.fm`), used only as a reference example — never a
  "sign up here" service.
- **Single-user is the primary remote story; multi-user is "advanced".** What
  ships + what `getbiblio.app` runs is single-user; the code also supports
  multi-user, documented as a clearly-marked advanced section with the
  BiblioCommons/SPL ToS caveat. No rework needed if we ever promote it.
- **Source of truth:** the site becomes canonical for _user-facing_ docs;
  `README.md` shrinks to a blurb + link. In-repo `docs/` (architecture,
  releasing, the project briefs) stays for _contributors_.

## Content plan (Diátaxis + MCP-docs best practices)

### Guides tab

- _Getting started:_ `introduction` (what it is, multi-library, local + remote)
  · `quickstart` (install → `init` → first search)
- _Install_ (**multi-client, copy-paste — high-leverage for MCP**):
  Claude Desktop (`claude_desktop_config.json`), Claude Code (`claude mcp add`),
  the remote connector (claude.ai → Connectors), Cursor / VS Code one-click
  deeplink **badges**.
- _How-to:_ search the catalog (formats, sort, paging) · place & manage holds ·
  borrow/return digital + Libby waitlist · manage loans (renew / check-in) ·
  branches & availability (3-letter + locker codes) · **recipes** ("what to ask
  Claude") · **self-host the remote connector** (Fly + WorkOS, single-user;
  multi-user as an advanced subsection).
- _Concepts:_ architecture (gateway client, single-library-per-server) · local
  vs remote (stdio vs Streamable HTTP; per-session credential model) · security
  & credentials (never logged; single-user owner gate).
- _Help:_ **troubleshooting** (auth/401, missing creds, format/branch codes,
  reading logs) · `changelog`.

### Reference tab

- `cli` (generated from the console-script) · `mcp-tools` (**generated** from the
  FastMCP instance, with **read-only / writes / destructive** badges from each
  tool's annotations) · `configuration` (hand-written: `config.toml` + every
  env var, incl. the remote/WorkOS/single-user vars).

**MCP-docs best practices baked in** (beyond clickwheel/rewind):

- Multi-client **Install** page + Cursor/VS Code install **badges**.
- **Recipes** (example prompts) — MCP's interface is conversational.
- Tool **annotation badges** (read-only/writes/destructive) auto-emitted.
- **Troubleshooting** page.
- Mintlify **`llms.txt`/`llms-full.txt`** (auto) + **contextual menu**
  (`copy`, `claude`, `chatgpt`, `cursor`, `vscode`).
- **MCP registry** `server.json` (`io.github.pdugan20/bibliocommons-mcp`) +
  README install badges (Phase 4).

## Architecture

```text
bibliocommons-mcp repo
├── docs-mintlify/                 # the Mintlify site (docs-as-code)
│   ├── docs.json                  # nav (Diátaxis tabs/groups), theme, contextual menu, domain
│   ├── introduction.mdx           # landing/overview
│   ├── quickstart.mdx             # TUTORIAL
│   ├── install.mdx                # multi-client install + badges
│   ├── guides/*.mdx               # HOW-TO (search, holds, digital, loans, branches, recipes, self-host)
│   ├── concepts/*.mdx             # EXPLANATION (architecture, local-vs-remote, security)
│   ├── reference/
│   │   ├── cli.mdx                # GENERATED from the console-script
│   │   ├── mcp-tools.mdx          # GENERATED from the FastMCP instance (+ annotation badges)
│   │   └── configuration.mdx      # config.toml / env vars
│   ├── troubleshooting.mdx
│   ├── logo/ + favicon.svg
│   └── changelog.mdx
└── scripts/
    ├── gen_cli_reference.py        # console-script -> reference/cli.mdx
    └── gen_mcp_reference.py        # FastMCP        -> reference/mcp-tools.mdx
```

## Anti-staleness strategy

Mirrors clickwheel's "Docs Reference Freshness" + the repo's existing web-bundle
freshness convention:

- The CLI + MCP-tool reference is **generated from source**; CI regenerates and
  `git diff --exit-code` fails the build if the committed output drifted.
- CI runs `mint broken-links` so nav/links can't rot.
- `make docs-reference` / `docs` / `docs-links` for local authoring.

## Out of scope (see DEFERRED.md)

Separate marketing/legal site, custom-domain Mintlify ($), API playground
(no REST API — MCP tools instead), multi-user as the headline.
