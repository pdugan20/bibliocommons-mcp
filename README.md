# bibliocommons-mcp

MCP server for [BiblioCommons](https://bibliocommons.com/)-powered public libraries — Seattle, San Francisco, ~190 others. Search the catalog, place holds, manage checkouts, all from any MCP-capable client (Claude, Cursor, etc.).

Built because placing a hold on a CD shouldn't take seven clicks.

## What it does

| Tool             | What it does                                                                                               |
| ---------------- | ---------------------------------------------------------------------------------------------------------- |
| `search`         | Search the catalog. Optional format filter (`MUSIC_CD`, `BK`, `EBOOK`, `EAUDIOBOOK`, `DVD`, etc.) and sort |
| `availability`   | Per-branch availability for a specific bib                                                                 |
| `place_hold`     | Place a physical hold (CD/book/DVD/etc.) with pickup branch                                                |
| `borrow_digital` | Check out an immediately-available digital item                                                            |
| `list_holds`     | All your current holds (physical + digital)                                                                |
| `cancel_hold`    | Cancel one of your holds                                                                                   |
| `list_loans`     | Current checkouts with due dates                                                                           |
| `list_branches`  | All branches at your configured library                                                                    |
| `library_health` | Login probe + hold counts/quotas                                                                           |

**Not yet supported (v1.1):** placing a digital hold on an _unavailable_ digital item (joining a waitlist). Available digital items work via `borrow_digital`. Use the Libby app directly for digital waitlists in the meantime.

## Install

```bash
pip install -e .
```

Requires Python 3.11+.

## Configure

Create `~/.config/bibliocommons-mcp/config.toml`:

```toml
library = "seattle"                  # your BiblioCommons subdomain
default_pickup_branch = "Lake City"  # branch name or 3-letter code
default_format = "MUSIC_CD"          # optional default for search

[credentials]
card = "1234567890"
pin = "1234"
```

`chmod 600` it. Or set everything via environment variables:

```
BIBLIOCOMMONS_LIBRARY=seattle
BIBLIOCOMMONS_CARD=1234567890
BIBLIOCOMMONS_PIN=1234
BIBLIOCOMMONS_PICKUP_BRANCH="Lake City"
```

### Finding your library subdomain

If your library uses BiblioCommons, the URL will be `{your-library}.bibliocommons.com`. Common examples:

- Seattle: `seattle`
- San Francisco: `sfpl`
- Vancouver (BC): `vpl`
- Boston: `bpl`

If you visit `{name}.bibliocommons.com` and see a catalog, that's your subdomain.

## Run

Console script:

```bash
bibliocommons-mcp
```

Or via Python:

```bash
python -m bibliocommons_mcp
```

The server speaks MCP over stdio.

## Add to Claude Desktop

In `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or the equivalent on your OS:

```json
{
  "mcpServers": {
    "bibliocommons": {
      "command": "bibliocommons-mcp"
    }
  }
}
```

Restart Claude Desktop. Then ask Claude to "search the library for Mudhoney CDs" or "what holds do I have?"

## Format codes

Common values for the `format` parameter of `search`:

| Code           | Meaning                        |
| -------------- | ------------------------------ |
| `MUSIC_CD`     | Music CD                       |
| `BK`           | Book                           |
| `EBOOK`        | Ebook                          |
| `EAUDIOBOOK`   | E-audiobook                    |
| `AUDIOBOOK_CD` | Audiobook on CD                |
| `DVD`          | DVD                            |
| `BLU_RAY`      | Blu-ray                        |
| `LARGEPRINT`   | Large print book               |
| `MN`           | Music notation / printed music |

The full facet list is available from a search response under `entities.bibs[*].briefInfo.format`.

## How it works

1. Authenticates via the standard SPL/BiblioCommons login form (`POST /user/login`).
2. Talks to the modern gateway at `gateway.bibliocommons.com/v2/libraries/{your-library}/` using your session cookies.
3. Wraps and corrects the [`python-bibliocommons`](https://github.com/williamjacksn/python-bibliocommons) client — same auth, more endpoints (search, place hold, cancel hold, branches, availability).

The hold POST body shape we eventually figured out (see commit history for the saga):

```json
POST /v2/libraries/{library}/holds?locale=en-US
{
  "metadataId": "S30C...",
  "materialType": "PHYSICAL",
  "accountId": 1234567890,
  "enableSingleClickHolds": false,
  "materialParams": {
    "branchId": "LCY",
    "expiryDate": null,
    "errorMessageLocale": "en-US"
  }
}
```

`errorMessageLocale` is the killer field — without it, the gateway 500s with a generic Internal Server Error.

## Limitations

- **Digital queue holds** (joining a waitlist for an unavailable ebook/audiobook) aren't supported yet — only `borrow_digital` for items currently available. Use Libby for waitlists.
- **No suspend/unsuspend holds** in v1. Cancel works.
- **No renewals** in v1. Use the library website to renew.
- **One library per server instance.** Run two servers if you have cards at multiple libraries.

## Acknowledgments

- [`python-bibliocommons`](https://github.com/williamjacksn/python-bibliocommons) by William Jackson — handles the modern login flow.
- [`SFPL` by kaijchang](https://github.com/kaijchang/SFPL) — first sighting of the BiblioCommons place-hold endpoint pattern.
- [`bibliophile-backend` by DavidCain](https://github.com/DavidCain/bibliophile-backend) — proof that this approach generalizes across ~190 libraries.

## License

MIT
