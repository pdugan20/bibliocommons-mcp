# Deploying the remote connector to Fly.io

The remote/HTTP transport runs as a single always-on Fly machine (see
[`fly.toml`](../fly.toml)). Always-on matters: the per-session cookie-jar cache
lives in memory, so a scale-to-zero host would force PIN re-entry on every cold
start. Full project context:
[`docs/projects/remote-mcp-mobile.md`](projects/remote-mcp-mobile.md).

**Prerequisites:** a Fly account; `flyctl` installed (`brew install flyctl`);
`fly auth login`.

## 1. Launch (first time only)

From the repo root — reuses the committed `fly.toml` + `Dockerfile`:

```bash
fly launch --no-deploy --copy-config --name getbiblio-mcp --region sea
```

Pick your own app name/region if `getbiblio-mcp`/`sea` aren't right.

## 2. First deploy — authless, read-only (Milestone 1)

Deploy **without** WorkOS secrets first. The server comes up in read-only
catalog mode (search / availability / list_branches), which de-risks the whole
transport + hosting + domain story before any auth:

```bash
fly deploy
fly open /healthz        # expect {"status":"ok","library":"seattle","mode":"read-only"}
```

## 3. Custom domain `getbiblio.app` behind Cloudflare

```bash
fly certs add getbiblio.app
```

`fly certs add` prints the exact DNS records to create. In Cloudflare:

- Add those records. For the apex, Cloudflare's CNAME flattening lets you
  CNAME `getbiblio.app` → `getbiblio-mcp.fly.dev`, or use the A/AAAA IPs from
  `fly ips list`.
- **Start DNS-only (grey cloud)** so Fly's ACME challenge validates and issues
  the cert. Confirm `https://getbiblio.app/healthz` works.
- Then optionally enable the Cloudflare **proxy (orange cloud)** with
  **SSL/TLS → Full (strict)**. Proxying lets you add the Anthropic egress
  allowlist (`160.79.104.0/21`) as an edge WAF rule (defense-in-depth; OAuth is
  the real gate).

## 4. Turn on auth — multi-user (Milestone 2)

Once read-only works end-to-end, enable WorkOS:

```bash
fly secrets set WORKOS_CLIENT_ID=client_01... WORKOS_API_KEY=sk_live_...
fly deploy
```

In the WorkOS dashboard (Staging or Production to match the keys):

- **Resource Indicator** = `https://getbiblio.app/mcp`
- **Redirect URI** (web app, for the settings page) = `https://getbiblio.app/account/callback`
- Enable **DCR + CIMD** so Claude's connector auto-registers.

Now `/mcp` requires a WorkOS login, and each user sets their library card at
`https://getbiblio.app/account`.

## 5. Add the connector in Claude

On **claude.ai web** (not the phone): Settings → Connectors → Add custom
connector → `https://getbiblio.app/mcp`. It then syncs to the iOS app. Complete
the WorkOS login, set your card at `/account`, and confirm `list_holds` returns
your holds.

## Operations

- Logs: `fly logs`
- Status: `fly status` (confirm 1 machine, started)
- Secrets: `fly secrets list` (names only)
- Tuning (optional env): `BIBLIOCOMMONS_MCP_SESSION_TTL` (idle seconds before a
  cached client drops, default 86400), `BIBLIOCOMMONS_MCP_MAX_SESSIONS`
  (default 1000), `WEB_SESSION_SECRET` (defaults to a value derived from the
  API key).

## Config validation & linting

- `fly config validate --strict` — semantic check of `fly.toml` (needs Fly
  auth; run before deploying). CI runs it too when an `FLY_API_TOKEN` repo
  secret is set (the `Infra Lint` job); without the secret that step is
  skipped, not failed.
- `taplo fmt fly.toml` — TOML formatter (also a pre-commit hook, scoped to
  `fly.toml`).
- `hadolint Dockerfile` — Dockerfile linter (CI `Infra Lint` job).

## Hardening baked into `fly.toml`

- **Zero-downtime deploys:** `[deploy] strategy = "bluegreen"` boots+health-checks
  a new machine before cutting over (verified). A deploy still empties the
  in-memory session cache; bluegreen just avoids 503s during the swap.
- **Graceful shutdown:** `kill_signal = "SIGTERM"` + `kill_timeout = "30s"` so
  uvicorn drains SSE/streaming connections cleanly on stop.
- **OOM insurance:** `swap_size_mb = 512` on the 512MB machine.
- **Crash recovery:** `[[restart]] policy = "on-failure"` (max 10).
- **Concurrency:** `connections` type, soft 200 / hard 250 (long-lived SSE).
