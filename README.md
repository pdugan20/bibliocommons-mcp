# bibliocommons-mcp

[![PyPI](https://img.shields.io/pypi/v/bibliocommons-mcp?logo=pypi&logoColor=white)](https://pypi.org/project/bibliocommons-mcp/)
[![CI](https://github.com/pdugan20/bibliocommons-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/pdugan20/bibliocommons-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-%3E%3D3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?logo=opensourceinitiative&logoColor=white)](https://opensource.org/licenses/MIT)

Place holds, search the catalog, and manage your account at any [BiblioCommons](https://bibliocommons.com/)-powered public library — Seattle, SFPL, BPL, ~190 others — from any MCP-aware client (Claude Code, Claude Desktop, Cursor). One library per server instance, configured via a small TOML file.

Built because placing a hold on a CD shouldn't take seven clicks.

## Install

```bash
pipx install bibliocommons-mcp
```

Or with `pip`:

```bash
pip install bibliocommons-mcp
```

## Quick Start

Drop your card and pickup branch into a config file:

```bash
mkdir -p ~/.config/bibliocommons-mcp
cat > ~/.config/bibliocommons-mcp/config.toml << 'EOF'
library = "seattle"                  # your bibliocommons subdomain
default_pickup_branch = "Lake City"  # branch name or 3-letter code

[credentials]
card = "YOUR_CARD_NUMBER"
pin  = "YOUR_PIN"
EOF
chmod 600 ~/.config/bibliocommons-mcp/config.toml
```

Wire it into Claude Code:

```bash
claude mcp add bibliocommons bibliocommons-mcp --scope user
```

Restart your client. That's it.

## What this feels like

> Find me an available Mudhoney CD I can pick up at Lake City this week.
>
> Search for "Heavier Than Heaven" by Charles Cross — is the print edition or the audiobook closer to my branch?
>
> What's on hold for me and how far up the queue am I?
>
> Cancel that hold on the Cobain book — I bought it instead.

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
- [`docs/releasing.md`](docs/releasing.md) — automated release flow

## Contributing / Security / License

- Setup, tests, commit conventions: [CONTRIBUTING.md](CONTRIBUTING.md)
- Vulnerability disclosure: [SECURITY.md](SECURITY.md)
- MIT
