# Troubleshooting

Common errors and fixes. If your problem isn't here, the next step is `library_health` — it surfaces login state and hold quotas, and 90% of "weird behaviour" turns out to be one of those.

## "missing 'library' (set in ...)" at startup

The config loader couldn't find a `library` value in either the TOML file or the `BIBLIOCOMMONS_LIBRARY` env var.

- Check the file exists at `~/.config/bibliocommons-mcp/config.toml` (or wherever `BIBLIOCOMMONS_MCP_CONFIG` points)
- Check it has `library = "seattle"` (or your subdomain) at the top level — _not_ inside a `[section]`
- If you're using env vars, confirm they're exported in the shell that started the MCP client

## "missing credentials" at startup

Same idea but for the `[credentials]` section. Either set `card` and `pin` in the TOML file under `[credentials]`, or export both `BIBLIOCOMMONS_CARD` and `BIBLIOCOMMONS_PIN` env vars.

## Login times out / "ReadTimeout"

The catalog host (`{your-library}.bibliocommons.com`) is slow or rate-limiting you. Most likely cause: you've hammered it from a test loop. Wait a minute and retry. If it persists, check the library's status page or visit the catalog in a browser.

## `place_hold` returns 500 "Internal Server Error"

Almost always one of these:

- **You're calling against a freshly-upgraded card.** SPL-style "online-only" cards (often 13 digits) can't place physical holds until you verify in person. `library_health` will show `physical_holds: "N/unlimited"` for verified cards; an online-only card's ILS quota is 0/0 and the gateway crashes downstream. Visit a branch with photo ID to upgrade.
- **The bib isn't actually holdable** (reference-only, library use only, on order). `availability(bib_id)` will show this — look for `circulationType: "REQUEST"` and a non-zero `totalCopies`.
- **Bug in the library's ILS bridge.** If `library_health` is fine and the bib is normal, retry once. If it's still failing, the ILS adapter on BiblioCommons' side is having a moment. Place the hold via the library website to confirm, and please [file a bug](https://github.com/pdugan20/bibliocommons-mcp/issues/new?template=bug_report.yml).

## `cancel_hold` returns "Required parameters: metadataIds, holdIds"

You passed only one or the other. The DELETE shape requires both — `hold_id` from `list_holds().holds[i].hold_id` and `bib_id` from the same row's `metadata_id`. The MCP tool signature is `cancel_hold(hold_id, bib_id)` for this reason.

## Search returns 25 results no matter what

That's the gateway's fixed page size. Use `page=2`, `page=3`, etc. to walk further. `catalogSearch.pagination.pages` (visible in the raw client response) tells you the total page count for a query.

## "ambiguous branch 'XYZ'"

The branch resolver matched more than one branch by substring. Be more specific, or pass the 3-letter code (`list_branches` shows them). For SPL: `"Lake City"` resolves to `LCY` (the regular branch) over `LOCK7` (its locker variant) — the resolver prefers non-locker matches automatically when ambiguous.

## Tools work locally but not from my MCP client

- Confirm the client can see the `bibliocommons-mcp` binary: `which bibliocommons-mcp` from the same shell that launches the client
- If the binary isn't on the client's PATH, use the absolute path in your client config
- Set `BIBLIOCOMMONS_MCP_LOG_LEVEL=DEBUG` in the client's env to get stderr logs in the client's UI

## Cassette tests fail in CI but pass locally

You probably re-recorded a cassette locally but didn't commit it. `git status` should show `tests/cassettes/*.yaml` as modified — diff and commit, sanitization check, push.
