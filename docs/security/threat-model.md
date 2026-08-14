# bibliocommons-mcp threat model

Protected assets are library credentials, patron identity, holds, checkouts, loans, account
quotas, configuration, and MCP protocol integrity. MCP arguments, gateway HTML/JSON,
library configuration, branch names, and recorded cassettes are untrusted.

Required controls:

- Keep credentials and patron data out of stdout, MCP responses, logs, exceptions,
  cassettes, fixtures, and telemetry; stdout is protocol framing only.
- Validate tool arguments and keep state-changing tools distinct from read-only discovery.
- Preserve the verified physical/digital DTO and account-ID distinctions; fail closed on
  an unknown material type, endpoint, response shape, or library identity.
- Do not run state-changing live tests in CI. Automatically sanitize and manually inspect
  every newly recorded cassette.
- Bound gateway requests with timeouts and handle retries without duplicating a hold,
  checkout, or cancellation.

Update this model when a tool, endpoint, credential source, state-changing operation, or
cassette-recording path changes.
