# bibliocommons-mcp

[![PyPI](https://img.shields.io/pypi/v/bibliocommons-mcp?logo=pypi&logoColor=white)](https://pypi.org/project/bibliocommons-mcp/)
[![CI](https://github.com/pdugan20/bibliocommons-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/pdugan20/bibliocommons-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-%3E%3D3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?logo=opensourceinitiative&logoColor=white)](https://opensource.org/licenses/MIT)

MCP server for placing holds, searching, and managing your account at [BiblioCommons](https://bibliocommons.com/)-powered public libraries.

## Install

```bash
pipx install bibliocommons-mcp
```

Or with `pip`:

```bash
pip install bibliocommons-mcp
```

## Quick Start

```bash
pipx install bibliocommons-mcp
bibliocommons-mcp init                                    # interactive setup
claude mcp add bibliocommons bibliocommons-mcp --scope user
```

`init` walks you through the four prompts it needs (library subdomain, card, PIN, default pickup branch), validates each step against the live gateway, and writes `~/.config/bibliocommons-mcp/config.toml` with mode 0600. If you'd rather skip the wizard and hand-write the file (or use env vars), see [`docs/configuration.md`](docs/configuration.md).

After `claude mcp add`, restart your client. That's it.

## What this feels like

> Any Mark Lanegan available at Lake City this week?
>
> Find me a Sub Pop CD from the last five years I haven't held yet — closest branch to Lake City wins.
>
> What's on hold for me and how far up the queue am I?
>
> Cancel the hold on the Cobain biography — I bought it.

Each prompt becomes a chain of MCP tool calls — typically `search` → `availability` → `place_hold`, or `list_holds` → `cancel_hold` for cleanup.

## Tools

| Tool             | Description                                                        |
| ---------------- | ------------------------------------------------------------------ |
| `search`         | Catalog search with format facet (`MUSIC_CD`, `BK`, `EBOOK`, etc.) |
| `availability`   | Per-branch availability + status for a bib                         |
| `place_hold`     | Physical hold with pickup branch (defaults to your config)         |
| `borrow_digital` | Check out an immediately-available ebook / e-audiobook             |
| `list_holds`     | Your current holds (physical + digital)                            |
| `cancel_hold`    | Cancel a hold by ID                                                |
| `list_loans`     | Current checkouts with due dates                                   |
| `list_branches`  | All branches at your configured library                            |
| `library_health` | Login probe + hold counts/quotas                                   |

Placing a hold on an _unavailable_ digital item (joining a Libby waitlist) isn't supported in v1 — use the Libby app for that. `borrow_digital` covers available digital items.

## Configuration

The example above is enough for most users. The full schema, environment-variable overrides, and tips for finding your library's subdomain are in [`docs/configuration.md`](docs/configuration.md).

## MCP clients

The Quick Start uses Claude Code. For Claude Desktop, Cursor, Continue, Cline, Zed, and other MCP clients, see [`docs/mcp-clients.md`](docs/mcp-clients.md).

## Library compatibility

Tested against `seattle` and `sfpl`. NYPL is no longer on BiblioCommons (`410 SiteDisabledError`). If you try it against your library, [open a compatibility report](https://github.com/pdugan20/bibliocommons-mcp/issues/new?template=library_compatibility.yml) — the running list lives in [`docs/known-libraries.md`](docs/known-libraries.md).

## Requirements

- Python 3.11+
- A BiblioCommons library account in good standing (card + PIN)
- The library must run on BiblioCommons (visit `{name}.bibliocommons.com` and confirm)

## Further reading

- [`docs/architecture.md`](docs/architecture.md) — how the gateway client works and what we had to discover to make holds POST cleanly
- [`docs/format-codes.md`](docs/format-codes.md) — known format facet codes
- [`docs/troubleshooting.md`](docs/troubleshooting.md) — common errors and fixes
- [`docs/roadmap.md`](docs/roadmap.md) — what's planned for v1.1+
- [`docs/releasing.md`](docs/releasing.md) — automated release flow

## Contributing / Security / License

- Setup, tests, commit conventions: [CONTRIBUTING.md](CONTRIBUTING.md)
- Vulnerability disclosure: [SECURITY.md](SECURITY.md)
- MIT
