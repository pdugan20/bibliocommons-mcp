# Configuration

bibliocommons-mcp reads from `~/.config/bibliocommons-mcp/config.toml`. Environment variables override file values for any key.

The file should be `chmod 600` — it contains your library PIN.

## Full schema

```toml
# Required: your BiblioCommons subdomain (`{name}.bibliocommons.com`)
library = "seattle"

# Optional: default pickup branch for place_hold. Branch name or 3-letter code.
# When set, you can call place_hold(bib_id) without a pickup_branch arg.
default_pickup_branch = "Lake City"

# Optional: default format for search if not specified.
# Common values: MUSIC_CD, BK, EBOOK, EAUDIOBOOK, DVD. See docs/format-codes.md.
default_format = "MUSIC_CD"

[credentials]
card = "1000000000000"  # library card number / barcode
pin  = "1234"           # your PIN
```

## Environment variables

These override the corresponding config-file value. Useful for CI, MCP clients that prefer env config, or if you'd rather not put credentials on disk at all.

| Variable                      | Overrides                                                                   |
| ----------------------------- | --------------------------------------------------------------------------- |
| `BIBLIOCOMMONS_MCP_CONFIG`    | Path to config TOML                                                         |
| `BIBLIOCOMMONS_LIBRARY`       | `library`                                                                   |
| `BIBLIOCOMMONS_CARD`          | `credentials.card`                                                          |
| `BIBLIOCOMMONS_PIN`           | `credentials.pin`                                                           |
| `BIBLIOCOMMONS_PICKUP_BRANCH` | `default_pickup_branch`                                                     |
| `BIBLIOCOMMONS_MCP_LOG_LEVEL` | stderr log level (`WARNING` default; try `INFO`/`DEBUG` if something's off) |

If env vars supply `library`, `card`, and `pin`, the config file is optional.

## Finding your library's subdomain

If your library uses BiblioCommons, the catalog lives at `{your-library}.bibliocommons.com`. Some common ones:

| Library                       | Subdomain |
| ----------------------------- | --------- |
| Seattle Public Library        | `seattle` |
| San Francisco Public Library  | `sfpl`    |
| Boston Public Library         | `bpl`     |
| Vancouver Public Library (BC) | `vpl`     |
| Edmonton Public Library       | `epl`     |
| Ottawa Public Library         | `ottawa`  |
| Burnaby Public Library        | `burnaby` |

The full list is around ~190 systems. If you visit `{name}.bibliocommons.com` and see the catalog interface, you've got the right subdomain.

If your library isn't on BiblioCommons (e.g. NYPL moved off in 2025), this tool can't help. See [`known-libraries.md`](known-libraries.md) for the compatibility status of libraries people have tried.

## Branches

`default_pickup_branch` accepts either a name or a 3-letter code. The resolver is case-insensitive and matches substrings:

- `"Lake City"` → `LCY`
- `"lake city"` → `LCY`
- `"LCY"` → `LCY`
- `"Ballard"` → `BAL` (prefers the regular branch over `LOCK7`, its locker variant)

Get the full branch list for your library via `list_branches`.

## Where the file goes

Default path is `~/.config/bibliocommons-mcp/config.toml` (XDG-style on Linux/macOS). Override with `BIBLIOCOMMONS_MCP_CONFIG=/path/to/file.toml` if you need to.

Multi-card households / multi-library users: run separate MCP server instances pointed at different config files via the env var.
