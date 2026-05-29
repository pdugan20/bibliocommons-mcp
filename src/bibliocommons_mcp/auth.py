"""OAuth 2.1 Resource Server auth for the remote/HTTP transport.

bibliocommons-mcp acts as a **Resource Server** (MCP auth spec 2025-06-18):
it validates bearer tokens issued by an external Authorization Server
(WorkOS AuthKit) and never runs its own OAuth endpoints. Validation is
JWKS/JWT only — the server holds *no* WorkOS secret, just WorkOS's public
keys. See docs/projects/remote-mcp-mobile.md §3.

Auth is **opt-in via env**: if `WORKOS_JWKS_URL` (or `WORKOS_CLIENT_ID`) is
present, the HTTP server requires a valid WorkOS token; otherwise it runs
authless (Milestone-1 read-only catalog mode). stdio is always authless.
"""

from __future__ import annotations

import logging
import os

import anyio
import jwt
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings

logger = logging.getLogger(__name__)

# WorkOS serves AuthKit signing keys here, keyed by client id. Issuer is
# api.workos.com (recent AuthKit), with a known trailing-slash inconsistency
# across versions — so we accept both forms (see _issuer_ok).
WORKOS_DEFAULT_ISSUER = "https://api.workos.com"
WORKOS_JWKS_TEMPLATE = "https://api.workos.com/sso/jwks/{client_id}"


class WorkOSAccessToken(AccessToken):
    """`AccessToken` plus the user identity we key per-user state on.

    The base SDK model only carries token/client_id/scopes/expires_at/resource,
    so we extend it with the JWT `sub` (the stable user id) and the raw claims.
    The auth middleware stores the verifier's returned object as-is, so tools
    read `get_access_token().subject`.
    """

    subject: str
    claims: dict = {}


class WorkOSTokenVerifier(TokenVerifier):
    """Validate a WorkOS-issued JWT: signature (JWKS) + iss + aud + expiry."""

    def __init__(
        self,
        *,
        issuer: str,
        jwks_url: str,
        audience: str | None = None,
        algorithms: tuple[str, ...] = ("RS256",),
        leeway: int = 60,
    ) -> None:
        # Normalize for the trailing-slash-tolerant issuer check.
        self._issuer = issuer.rstrip("/")
        self._audience = audience
        self._algorithms = list(algorithms)
        self._leeway = leeway
        # PyJWKClient fetches + caches the key set; first use does one network
        # round-trip, then keys are cached in-process.
        self._jwk_client = jwt.PyJWKClient(jwks_url)

    def _issuer_ok(self, iss: str | None) -> bool:
        return iss in (self._issuer, self._issuer + "/")

    def _verify_sync(self, token: str) -> WorkOSAccessToken | None:
        signing_key = self._jwk_client.get_signing_key_from_jwt(token)
        options = {"require": ["exp", "sub"], "verify_aud": bool(self._audience)}
        kwargs: dict = {
            "algorithms": self._algorithms,
            "leeway": self._leeway,
            "options": options,
        }
        if self._audience:
            kwargs["audience"] = self._audience
        # Don't pass `issuer=` — PyJWT does exact-string matching and WorkOS's
        # trailing slash varies. Decode (verifying sig/exp/aud), then check iss
        # ourselves against both forms.
        claims = jwt.decode(token, signing_key.key, **kwargs)
        if not self._issuer_ok(claims.get("iss")):
            logger.debug("token rejected: issuer mismatch (%s)", claims.get("iss"))
            return None
        raw_scopes = claims.get("scope") or claims.get("scopes") or ""
        scopes = raw_scopes.split() if isinstance(raw_scopes, str) else list(raw_scopes)
        return WorkOSAccessToken(
            token=token,
            client_id=claims.get("client_id") or claims.get("azp") or "unknown",
            scopes=scopes,
            expires_at=claims.get("exp"),
            resource=self._audience,
            subject=str(claims["sub"]),
            claims=claims,
        )

    async def verify_token(self, token: str) -> AccessToken | None:
        # PyJWT's JWKS fetch + decode are blocking; run off the event loop.
        try:
            return await anyio.to_thread.run_sync(self._verify_sync, token)
        except Exception:
            # Any failure (bad signature, expired, wrong aud/iss, malformed,
            # JWKS fetch error) is an auth failure, not a server error.
            logger.debug("token verification failed", exc_info=True)
            return None


def workos_auth_from_env() -> tuple[WorkOSTokenVerifier, AuthSettings] | None:
    """Build (verifier, AuthSettings) from env, or None if auth isn't configured.

    Recognized env:
      WORKOS_JWKS_URL        explicit JWKS URL (else derived from client id)
      WORKOS_CLIENT_ID       used to derive the JWKS URL if WORKOS_JWKS_URL unset
      WORKOS_ISSUER          token `iss` (default https://api.workos.com)
      BIBLIOCOMMONS_MCP_RESOURCE  this server's canonical resource URL, e.g.
                             https://getbiblio.app/mcp — bound as the token
                             audience (RFC 8707) and advertised in the
                             protected-resource metadata.

    Auth is enabled iff a JWKS URL is resolvable. When enabled,
    BIBLIOCOMMONS_MCP_RESOURCE is required (it's the RS identity in the OAuth
    discovery chain) — a clear error beats a silent misconfiguration.
    """
    jwks_url = os.environ.get("WORKOS_JWKS_URL")
    client_id = os.environ.get("WORKOS_CLIENT_ID")
    if not jwks_url and client_id:
        jwks_url = WORKOS_JWKS_TEMPLATE.format(client_id=client_id)
    if not jwks_url:
        return None  # authless (Milestone 1) — no WorkOS configured

    resource = os.environ.get("BIBLIOCOMMONS_MCP_RESOURCE")
    if not resource:
        raise AuthConfigError(
            "WorkOS auth is configured (WORKOS_JWKS_URL/WORKOS_CLIENT_ID) but "
            "BIBLIOCOMMONS_MCP_RESOURCE is unset. Set it to this server's "
            "canonical resource URL (e.g. https://getbiblio.app/mcp) so tokens "
            "are audience-bound and protected-resource metadata is correct."
        )
    issuer = os.environ.get("WORKOS_ISSUER", WORKOS_DEFAULT_ISSUER)

    verifier = WorkOSTokenVerifier(issuer=issuer, jwks_url=jwks_url, audience=resource)
    settings = AuthSettings(
        issuer_url=issuer,
        resource_server_url=resource,
        required_scopes=[],
    )
    return verifier, settings


class AuthConfigError(RuntimeError):
    """Misconfigured auth env (e.g. WorkOS set without a resource URL)."""
