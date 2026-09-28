# Cloudflare Access as the auth backend

An alternative to [WorkOS](deploy-fly.md#4-turn-on-auth--single-user-the-owner)
for gating the remote/HTTP connector: Cloudflare Access sits in front of the
Fly origin, handles the OAuth dance with your agent itself (Managed OAuth), and
this server only has to validate the resulting assertion. No `/account` page,
no WorkOS API key, no second identity provider to run.

**This requires running a separate cloudflare worker or reverse proxy!**

**Prerequisites:**

- A Fly deployment of this server already running (see
  [`docs/deploy-fly.md`](deploy-fly.md)), **without** `WORKOS_*` secrets set —
  Cloudflare Access and WorkOS auth are mutually exclusive
- A Cloudflare account with **Zero Trust / Access** enabled, on the same
  account as the domain in front of the Fly app.
- A small Cloudflare Worker deployed in front of the origin — see step 3.
  This is a hard prerequisite since CF sets a header that the MCP server
  will not read (the worker moves it to the authorization header for us).

## 1. Create the Access application

In the Cloudflare Zero Trust dashboard → **Access → Applications → Add an
application** (Self-hosted):

- **Application domain:** the hostname claude.ai will hit, e.g.
  `getbiblio.app`.
- **Identity providers:** whatever you sign in with (Google, GitHub, one-time
  PIN, ...).
- **Policies:** an Allow policy scoped to your own identity (typically
  allowing your email to sign in).

After creating it, open the application's **Overview** tab and copy the
**Application Audience (AUD) Tag** — you'll need it for `CF_ACCESS_AUD`
below. It is *not* the same as your team domain, and conflating the two is
the most common way to end up with every request 401ing.

## 2. Turn on Managed OAuth for the Access application

Access application → **Configuration → Managed OAuth clients** (naming may
vary by dashboard version) → add claude.ai as a client. This is what lets the
Claude connector complete an OAuth login against Access directly.

You should validate this step prior to setting the `CF_ACCESS_*` env vars.  You
can do this by adding the custom connector in claud.ai and verifying the oauth
flow completes. If this doesn't work later steps won't either.

## 3. The Worker: moving the header

Access authenticates the browser/connector and, once past its edge, forwards
the request to the origin with the assertion in a
`Cf-Access-Jwt-Assertion` header. This server (like most OAuth Resource
Servers) expects a standard `Authorization: Bearer <token>` header instead.
The Worker's job is to move this header to the right place:

```js
export default {
  async fetch(request, env) {
    const assertion = request.headers.get("Cf-Access-Jwt-Assertion");

    // Setup probe — see step 4 below. Set ENABLE_WHOAMI="0" (or drop the var)
    // once you've recorded sub/aud/iss, then redeploy. Never leave this on:
    // it prints identity claims to anyone Access lets through.
    if (env.ENABLE_WHOAMI === "1" && new URL(request.url).pathname === "/__whoami") {
      if (!assertion) {
        return new Response("No Cf-Access-Jwt-Assertion header.\n", { status: 401 });
      }
      const payload = assertion.split(".")[1];
      const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
      return new Response(json, { headers: { "content-type": "application/json" } });
    }

    const headers = new Headers(request.headers);
    if (assertion) {
      headers.set("Authorization", `Bearer ${assertion}`);
    }
    return fetch(new Request(request, { headers }));
  },
};
```

Deploy it and route it in front of your fly origin (Worker route matching your
Access application's hostname.  

You can also look at [`luscoma/mcp-cf-access-shim`](https://github.com/luscoma/mcp-cf-access-shim)
for a full worker that's deployable as is.

## 4. Gather the values from `/__whoami`

With the Worker deployed and `ENABLE_WHOAMI` on, hit the debug endpoint
through Access (i.e. log in) and record:

| Value | Becomes |
|---|---|
| `iss` | `CF_ACCESS_TEAM_DOMAIN` (`https://<team>.cloudflareaccess.com`) |
| `aud` | `CF_ACCESS_AUD` — same as the AUD tag from step 1 |
| `sub` | `BIBLIOCOMMONS_MCP_OWNER_SUBJECTS` — this should be stable across logins |

## 5. Env vars on Fly

```bash
fly secrets unset WORKOS_CLIENT_ID WORKOS_API_KEY   # mutually exclusive with CF Access
fly secrets set \
  CF_ACCESS_TEAM_DOMAIN=<team>.cloudflareaccess.com \
  CF_ACCESS_AUD=<aud-tag-from-step-1> \
  BIBLIOCOMMONS_MCP_SINGLE_USER=1 \
  BIBLIOCOMMONS_MCP_OWNER_SUBJECTS=<sub-from-whoami>
fly deploy
```

`CF_ACCESS_TEAM_DOMAIN` accepts either `<team>.cloudflareaccess.com` or the
full `https://...` form — both normalize to the same JWKS URL
(`{team_domain}/cdn-cgi/access/certs`).

## 6. Acceptance test — do this before setting card/PIN

Verify in order. **Do not set `BIBLIOCOMMONS_CARD`/`BIBLIOCOMMONS_PIN` until
all of these pass** — until then the deployed server should not be able to
reach the live library gateway on anyone's behalf.

1. `curl -si https://<host>/healthz` → `200`.
2. The connector still works end-to-end from claude.ai — `list_branches`
   returns data.
3. **The acceptance test:**
   `curl -si https://<app>.fly.dev/mcp -X POST -d '{}'` → **`401`**.
   This hits the Fly origin directly, bypassing Cloudflare entirely. If it
   succeeds instead of 401ing, the verifier is not installed — most likely
   `AuthSettings` was omitted alongside the token verifier (passing a
   verifier without `AuthSettings` installs no auth middleware at all, so the
   server is silently wide open). Do not proceed to step 4 until this
   returns 401.
4. Turn off the debug endpoint: set `ENABLE_WHOAMI="0"` in the Worker and
   redeploy it.

Then set the library credentials:

```bash
fly secrets set BIBLIOCOMMONS_CARD=... BIBLIOCOMMONS_PIN=...
```

and confirm `list_holds` returns real data.

## Notes

- `BIBLIOCOMMONS_MCP_RESOURCE` (the WorkOS path's audience/resource-URL env
  var) is not used by this backend — Cloudflare Access binds to
  `CF_ACCESS_AUD` instead, and the server does not publish its own protected-
  resource metadata document (`resource_server_url` is deliberately `None`;
  Access already serves that discovery surface).
- Only one of WorkOS or Cloudflare Access may be configured at a time. Having
  both sets of env vars present is treated as a misconfiguration and the
  server refuses to start, rather than silently picking one.
