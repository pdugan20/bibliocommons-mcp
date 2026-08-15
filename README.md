# bibliocommons-mcp

[![CI](https://github.com/pdugan20/bibliocommons-mcp/actions/workflows/ci.yml/badge.svg?branch=main&event=push)](https://github.com/pdugan20/bibliocommons-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/bibliocommons-mcp)](https://pypi.org/project/bibliocommons-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/bibliocommons-mcp)](https://pypi.org/project/bibliocommons-mcp/)
[![License](https://img.shields.io/github/license/pdugan20/bibliocommons-mcp)](LICENSE)

MCP server for placing holds, searching, and managing your account at [BiblioCommons](https://bibliocommons.com/)-powered public libraries.

## Install

```bash
pipx install bibliocommons-mcp
```

Requires Python 3.11+.

## Quick Start

```bash
bibliocommons-mcp init
claude mcp add bibliocommons bibliocommons-mcp --scope user
```

`init` walks the prompts, validates live against the gateway, and writes the config file for you. Manual setup: [`docs/configuration.md`](docs/configuration.md). For Claude Desktop, Cursor, or other MCP clients: [`docs/mcp-clients.md`](docs/mcp-clients.md).

## Try asking

- “Place a hold on _Project Hail Mary_ at my branch.”
- “Show my current holds and their queue positions.”
- “What’s due back this week?”
- “Cancel my hold on _Zen and the Art of Motorcycle Maintenance_.”

## Tools

All mutation tools accept a list of IDs/refs — pass `[id]` for the common single-item case.

| Tool                 | Description                                                |
| -------------------- | ---------------------------------------------------------- |
| `search`             | Search the catalog, optionally filtered by format          |
| `availability`       | Show per-branch status for a bib                           |
| `place_hold`         | Place physical holds at your pickup branch                 |
| `borrow_digital`     | Borrow one or more available digital items                 |
| `place_digital_hold` | Join the Libby waitlist for unavailable digital items      |
| `list_holds`         | Show current holds and queue positions                     |
| `ready_for_pickup`   | Show only the holds waiting at your branch                 |
| `cancel_hold`        | Cancel holds (native bulk; one DELETE per call)            |
| `list_loans`         | Show checkouts with due dates                              |
| `renew_loan`         | Renew physical checkouts (native bulk; one PATCH per call) |
| `check_in_loan`      | Return digital checkouts early                             |
| `list_branches`      | List all branches at your library                          |
| `library_health`     | Check login and report hold quotas                         |

## Library compatibility

The same gateway serves every BiblioCommons-powered library — see [`docs/known-libraries.md`](docs/known-libraries.md) for what's been verified. If yours isn't listed, [file a compatibility report](https://github.com/pdugan20/bibliocommons-mcp/issues/new?template=library_compatibility.yml) once you try it.

## Requirements

- Python 3.11+
- A BiblioCommons library account in good standing (card + PIN)
- The library must run on BiblioCommons (visit `{name}.bibliocommons.com` and confirm)

## Further reading

- [`docs/architecture.md`](docs/architecture.md) — gateway client design and API quirks
- [`docs/format-codes.md`](docs/format-codes.md) — format facet codes
- [`docs/troubleshooting.md`](docs/troubleshooting.md) — common errors and fixes
- [`docs/roadmap.md`](docs/roadmap.md) — what's planned next
- [`docs/releasing.md`](docs/releasing.md) — automated release flow
