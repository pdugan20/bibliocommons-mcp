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

Requires Python 3.11+.

## Quick Start

```bash
bibliocommons-mcp init
claude mcp add bibliocommons bibliocommons-mcp --scope user
```

`init` walks the prompts, validates live against the gateway, and writes the config file for you. Manual setup: [`docs/configuration.md`](docs/configuration.md). For Claude Desktop, Cursor, or other MCP clients: [`docs/mcp-clients.md`](docs/mcp-clients.md).

## Try asking

> Place a hold on something at my branch.
>
> Show my current holds with queue positions.
>
> What's due back this week?
>
> Cancel a hold.

## Tools

| Tool                 | Description                                             |
| -------------------- | ------------------------------------------------------- |
| `search`             | Search the catalog, optionally filtered by format       |
| `availability`       | Show per-branch status for a bib                        |
| `place_hold`         | Place a physical hold at your pickup branch             |
| `place_holds`        | Place holds on multiple bibs at the same branch         |
| `borrow_digital`     | Borrow an available digital item                        |
| `place_digital_hold` | Join the Libby waitlist for an unavailable digital item |
| `list_holds`         | Show current holds and queue positions                  |
| `ready_for_pickup`   | Show only the holds waiting at your branch              |
| `cancel_hold`        | Cancel one hold by ID                                   |
| `cancel_holds`       | Cancel multiple holds in a single round-trip            |
| `list_loans`         | Show checkouts with due dates                           |
| `renew_loan`         | Renew one checkout by ID                                |
| `renew_loans`        | Renew multiple checkouts in one PATCH                   |
| `check_in_loan`      | Return a digital checkout early                         |
| `check_in_loans`     | Return multiple digital checkouts                       |
| `list_branches`      | List all branches at your library                       |
| `library_health`     | Check login and report hold quotas                      |

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
