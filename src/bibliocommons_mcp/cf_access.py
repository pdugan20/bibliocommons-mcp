"""Cloudflare Access as a second OAuth 2.1 Resource-Server auth backend.

Cloudflare Access sits in front of the origin and, once Managed OAuth to
claude.ai completes, forwards each request with a `Cf-Access-Jwt-Assertion`
header carrying a short-lived RS256 JWT. A reverse proxy (the Worker
documented in `docs/deploy-cloudflare-access.md`) moves that header's value
into a standard `Authorization: Bearer` header — nothing in this module or in
`server.py` talks to Cloudflare's edge directly, it only validates the
assertion like any other bearer token.

This is deliberately a second backend alongside WorkOS, not a replacement:
see `docs/deploy-cloudflare-access.md` for the full picture. Only one of
WorkOS or Cloudflare Access may be configured at a time — see the dispatch in
`server._auth_from_env`.
"""

from __future__ import annotations

import logging
import os

from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings

from .auth import AuthConfigError, JwksTokenVerifier

logger = logging.getLogger(__name__)

_JWKS_PATH = "/cdn-cgi/access/certs"


class CloudflareAccessAccessToken(AccessToken):
    """Cloudflare Access marker for the SDK's identity-bearing access token.

    Carries `email` (from the assertion's `email` claim, when present) for
    logging/debugging alongside the base `subject`/`claims` fields. Never log
    the assertion itself or its claims (see AGENTS.md critical rule 1) — this
    field exists for callers that want to display "signed in as ..." without
    re-parsing claims.
    """

    email: str | None = None


class CloudflareAccessTokenVerifier(JwksTokenVerifier):
    """Validate a Cloudflare Access JWT assertion: signature (JWKS) + iss/aud/expiry.

    Access issues no OAuth scopes — the assertion carries no `scope` claim —
    so `scopes` is always `[]`. `required_scopes` on the paired `AuthSettings`
    must stay empty too: a non-empty list would make the SDK's
    `RequireAuthMiddleware` reject every request, since Access tokens can
    never satisfy it.
    """

    def _build_token(self, claims: dict, token: str) -> CloudflareAccessAccessToken:
        aud = claims.get("aud")
        if isinstance(aud, list):
            client_id = str(aud[0]) if aud else "cf-access"
        elif aud:
            client_id = str(aud)
        else:
            client_id = "cf-access"
        return CloudflareAccessAccessToken(
            token=token,
            client_id=client_id,
            scopes=[],
            expires_at=claims.get("exp"),
            resource=self._audience,
            subject=str(claims["sub"]),
            claims=claims,
            email=claims.get("email"),
        )


def _normalize_team_domain(raw: str) -> str:
    """Accept both `yourteam.cloudflareaccess.com` and the full URL form."""
    domain = raw.strip()
    if not domain.startswith(("http://", "https://")):
        domain = f"https://{domain}"
    return domain.rstrip("/")


def cf_access_auth_from_env() -> (
    tuple[CloudflareAccessTokenVerifier, AuthSettings] | None
):
    """Build (verifier, AuthSettings) from env, or None if Access auth is unconfigured.

    Recognized env:
      CF_ACCESS_TEAM_DOMAIN  Access team domain, e.g. `yourteam.cloudflareaccess.com`
                             or `https://yourteam.cloudflareaccess.com`. Unset means
                             Cloudflare Access auth is disabled (the module is inert).
      CF_ACCESS_AUD          the Access application's AUD tag. Required when
                             CF_ACCESS_TEAM_DOMAIN is set — this is what binds the
                             verifier to *this* Access application and stops an
                             assertion minted for a different one from validating.

    `resource_server_url` is deliberately `None`: Cloudflare Access already
    serves OAuth discovery, so this server does not publish a second,
    possibly conflicting metadata document. See
    docs/deploy-cloudflare-access.md for the full picture.
    """
    team_domain = os.environ.get("CF_ACCESS_TEAM_DOMAIN")
    if not team_domain:
        return None  # Cloudflare Access not configured — module is inert

    issuer = _normalize_team_domain(team_domain)

    aud = os.environ.get("CF_ACCESS_AUD")
    if not aud:
        raise AuthConfigError(
            "Cloudflare Access auth is configured (CF_ACCESS_TEAM_DOMAIN is set) but "
            "CF_ACCESS_AUD is unset. Set it to the Access application's AUD tag so "
            "tokens are bound to this application specifically."
        )

    jwks_url = f"{issuer}{_JWKS_PATH}"
    verifier = CloudflareAccessTokenVerifier(
        issuer=issuer, jwks_url=jwks_url, audience=aud
    )
    settings = AuthSettings(
        issuer_url=issuer,
        resource_server_url=None,
        required_scopes=[],
    )
    return verifier, settings
