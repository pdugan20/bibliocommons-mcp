# Threat model

Codex Security reads this file as the repository's threat model. It describes how
bibliocommons-mcp works, where untrusted input enters, and the controls the code must keep.

## Scope and protected assets

bibliocommons-mcp is a Python MCP server that searches library catalogs and manages holds
and loans on a BiblioCommons account. It runs locally over stdio or remotely over
Streamable HTTP, with React MCP Apps for the UI. The hosted container runs as a non-root
user behind HTTPS (`README.md`, `Dockerfile`, `fly.toml`, `src/bibliocommons_mcp/server.py`).

Protected assets are library card numbers, PINs, session cookies, OAuth tokens and WorkOS
secrets, reading activity, pickup locations and notification addresses, the integrity of
each library account, and service availability (`src/bibliocommons_mcp/models.py`).

## Entry points

- **MCP clients** send search queries, record IDs, branches, batch sizes, delays, and
  mutation requests (`src/bibliocommons_mcp/server.py`).
- **Browsers** reach the account settings pages with callback parameters, cookies, and
  form posts; anyone on the network can reach the health, landing, and static routes
  (`src/bibliocommons_mcp/web_settings.py`).
- **Operators** supply TOML configuration, environment variables, and secrets
  (`src/bibliocommons_mcp/config.py`, `src/bibliocommons_mcp/init.py`,
  `src/bibliocommons_mcp/auth.py`).
- **BiblioCommons** returns cookies, JSON, HTML, errors, and cover URLs, and WorkOS supplies
  keys and identity (`src/bibliocommons_mcp/client.py`).
- **Contributors and CI** supply code, dependencies, and release artifacts
  (`web/package.json`, `.github/workflows/publish.yml`).

## Trust boundaries and assumptions

- Over stdio, whoever controls the local MCP client is trusted.
- Over HTTP, OAuth tokens are checked for signature, issuer, audience, expiry, and
  subject. The subject selects that user's credentials, and only subjects on the owner
  allowlist may use the server's own account (`src/bibliocommons_mcp/auth.py`).
- A BiblioCommons gateway session authorizes library actions, so whoever holds one acts
  as that patron.
- Catalog data and upstream responses are untrusted. MCP Host and Origin restrictions do
  not protect the custom account routes.

## Sensitive data and privileged actions

Local configuration stores credentials in plain text and must stay readable only by its
owner. Remote mode holds user credentials in memory. Placing holds, borrowing, cancelling,
renewing, and returning digital loans early all change a real library account
(`src/bibliocommons_mcp/credentials.py`).

## Required controls

1. **Account isolation.** Every remote request acts only for its authenticated subject.
   The server never falls back to the owner's account for an unauthenticated or unlisted
   subject, and HTTP mode is never exposed without OAuth when credentials are configured
   (`tests/test_multiuser.py`).
2. **Credential handling.** Stored credentials are bounded, expire, and are deleted on
   logout or revocation. Library identifiers are validated before they become part of a
   login URL, and redirects and cookies stay scoped to BiblioCommons hosts.
3. **Mutations.** Tool annotations and dry runs are hints to the client, not consent.
   Mutations name their exact targets, verify that the hold or loan belongs to the
   caller, and treat catalog text as data (`AGENTS.md`).
4. **Browser routes.** Session and state cookies stay signed, expiring, Secure, HttpOnly,
   and SameSite. State-changing posts verify their origin. Batches, delays, login attempts,
   and the credential store are bounded.
5. **Output and supply chain.** Upstream error bodies, tracebacks, and test cassettes are
   scrubbed of credentials (`tests/conftest.py`). The MCP App keeps its CSP and validates
   links (`src/bibliocommons_mcp/ui.py`, `web/lib/open-link.tsx`). Publishing uses OIDC with
   least-privilege release tokens, and deploys come from reviewed refs
   (`.github/workflows/release-please.yml`, `.github/workflows/fly-deploy.yml`).

## Review priorities

Review HTTP authentication and per-user isolation first, then credential storage and
outbound URLs, then mutation ownership and consent. Keep adversarial tests in
`tests/test_auth.py`, `tests/test_multiuser.py`, and `tests/test_web_settings.py`.

## Uncertain assumptions

- The live OAuth configuration, edge controls, and release-environment protections can't
  be confirmed from the deployment files (`fly.toml`, `docs/releasing.md`).
- Whether BiblioCommons enforces ownership on hold and loan IDs, and how the login client
  handles redirects and TLS, isn't established by this wrapper.
- Whether a host enforces client consent and the MCP App's sandbox and CSP depends on the
  host.

## When to update this model

Update it when transports, identity mapping, credential storage, tools, upstream
endpoints, MCP App permissions, dependencies, or the release and deploy workflows change.
