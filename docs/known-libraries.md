# Library compatibility

The BiblioCommons gateway endpoints are uniform across the SaaS, so any library on the platform _should_ work. This page tracks what's actually been tried.

## Confirmed working

| Library                      | Subdomain | Notes                                                                                                                 |
| ---------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------- |
| Seattle Public Library       | `seattle` | All tools tested end-to-end. 34 branches including locker pickup variants.                                            |
| San Francisco Public Library | `sfpl`    | Branches + search verified via read-only probes. State-changing operations not exercised against a live SFPL account. |

## Off the platform

| Library                 | Subdomain | Status                                                               |
| ----------------------- | --------- | -------------------------------------------------------------------- |
| New York Public Library | `nypl`    | Migrated off BiblioCommons. Gateway returns `410 SiteDisabledError`. |

## Tried it? Report back

The same gateway shape serves every BiblioCommons-hosted library, so the odds of your library "just working" are good. If you try it — even just `library_health` and a search — please [file a compatibility report](https://github.com/pdugan20/bibliocommons-mcp/issues/new?template=library_compatibility.yml). It's the only way this list grows. "Works fine" reports are as useful as bug reports.

## What "works" means here

A library is _confirmed working_ once these are exercised against a live account:

- `library_health` returns `logged_in: true`
- `list_branches` returns a non-empty branch list with 3-letter codes
- `search` with a format facet returns matching bibs
- `availability` returns per-copy data
- `place_hold` + `cancel_hold` round-trip successfully on a physical item
- `list_holds` + `list_loans` reflect current account state

Read-only verification (no `place_hold` / `cancel_hold`) gets a library into _branches + search verified_ status. That's enough for most users; placement and cancellation are very likely to work if the read paths do.
