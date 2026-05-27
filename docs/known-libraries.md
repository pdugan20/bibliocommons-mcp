# Library compatibility

The BiblioCommons gateway endpoints are uniform across the SaaS, so any library on the platform _should_ work. This page tracks what's actually been tried.

If you try a new library, please [file a compatibility report](https://github.com/pdugan20/bibliocommons-mcp/issues/new?template=library_compatibility.yml) — even a "works fine" report is useful.

## Confirmed working

| Library                      | Subdomain | Notes                                                                                                                 |
| ---------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------- |
| Seattle Public Library       | `seattle` | All tools tested end-to-end. 34 branches including locker pickup variants.                                            |
| San Francisco Public Library | `sfpl`    | Branches + search verified via read-only probes. State-changing operations not exercised against a live SFPL account. |

## Off the platform

| Library                 | Subdomain | Status                                                               |
| ----------------------- | --------- | -------------------------------------------------------------------- |
| New York Public Library | `nypl`    | Migrated off BiblioCommons. Gateway returns `410 SiteDisabledError`. |

## Untested but expected to work

The same gateway shape serves every BiblioCommons-hosted library. These are commonly mentioned but haven't been confirmed:

- Boston Public Library (`bpl`)
- Vancouver Public Library, BC (`vpl`)
- Edmonton Public Library (`epl`)
- Burnaby Public Library (`burnaby`)
- Ottawa Public Library (`ottawa`)
- Many others in `bibliophile-backend`'s [list of supported subdomains](https://github.com/DavidCain/bibliophile-backend)

If you've used this against one of these (or a different library entirely), the [compatibility issue template](https://github.com/pdugan20/bibliocommons-mcp/issues/new?template=library_compatibility.yml) is the way to get it on the list.

## What "works" means here

A library is "confirmed working" once these are exercised against a live account:

- `library_health` returns `logged_in: true`
- `list_branches` returns a non-empty branch list with 3-letter codes
- `search` with a format facet returns matching bibs
- `availability` returns per-copy data
- `place_hold` + `cancel_hold` round-trip successfully on a physical item
- `list_holds` + `list_loans` reflect current account state

Read-only verification (no place_hold/cancel_hold) gets a library into "branches + search verified" status. That's enough for most users; placement/cancellation are very likely to work if the read paths do.
