# Chicago Public Library Compatibility Design

## Goal

Make the published `bibliocommons-mcp` package authenticate reliably against
Chicago Public Library's multi-domain BiblioCommons SSO flow, and describe
branch codes accurately for libraries that use numeric rather than alphabetic
identifiers.

## Context and root cause

Chicago's SSO redirects set `bc_access_token` and `session_id` cookies on more
than one domain. `httpx` raises `CookieConflict` when the upstream
`bibliocommons` client retrieves either cookie with name-only mapping access.
The HTTP authentication exchange has completed at that point, and the required
cookie values are present in the cookie jar; only the ambiguous lookup fails.

The branch resolver has no equivalent runtime defect. It stores gateway branch
keys as strings and therefore already accepts numeric codes such as `"56"`.
Several docstrings, Pydantic descriptions, server instructions, and user docs
incorrectly narrow the contract to three-letter codes.

## Considered approaches

### 1. Narrow compatibility fallback in `Client.authenticate` (selected)

Call the upstream authentication method normally. Catch only
`httpx.CookieConflict`, recover the first non-empty access-token and session-id
values by iterating the existing cookie jar, then apply the same headers and
account-id derivation as the upstream client. Missing cookies remain an
authentication failure rather than being masked.

This keeps the standard path delegated to the dependency, fixes installed
releases immediately, and becomes dormant once the upstream package stops
raising the conflict.

### 2. Pin the open upstream pull request

Depending on an unreleased Git commit would incorporate the upstream fix but
would make package installation depend on GitHub and an unversioned revision.
That is unsuitable for the PyPI package.

### 3. Wait for an upstream release

This avoids local code, but the relevant pull request remains open and leaves a
verified library unable to authenticate with the currently published package.

## Detailed behavior

- Authentication without duplicate cookie names is unchanged.
- A `CookieConflict` triggers recovery from the cookie jar only after the
  upstream request flow has populated it.
- Recovery requires non-empty `bc_access_token` and `session_id` values.
- Recovered values populate `X-Access-Token` and `X-Session-Id` on the upstream
  HTTP client.
- `account_id` continues to be derived as the integer suffix of `session_id`
  plus one, matching the existing borrowing API contract.
- Card numbers, PINs, access tokens, and session IDs are never logged or placed
  in exception messages.
- Any exception other than `httpx.CookieConflict` propagates unchanged.

## Documentation contract

User-facing and schema-facing copy will call these values "branch codes" and
use both alphabetic and numeric examples. Seattle's locker preference remains
documented as a resolver behavior, not as a universal branch-code format.

## Testing

The regression test constructs an upstream client double whose authentication
method populates duplicate-domain cookies and reproduces `CookieConflict` via
name-only lookup. The test calls the real MCP wrapper and verifies successful
authentication, recovered headers, and account-id derivation without asserting
or printing secret values.

Existing branch tests will gain a numeric-code case. Schema snapshots will be
updated only for intentional description changes. The final gate is the full
`make check-all` suite.

## Issue resolution

The pull request will reference `pdugan20/bibliocommons-mcp#46`. The issue can
be closed after the fix reaches the default branch; opening a draft pull request
alone is not sufficient to claim the installed package is resolved.
