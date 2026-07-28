"""Browser settings page (`/account`) for capturing per-user library credentials.

In multi-user mode the WorkOS bearer token (used by Claude) only proves *who*
the user is — it doesn't carry their library card/PIN. This module serves a
small web page where a user logs in with WorkOS in a browser and enters their
library + card + PIN, which is validated against BiblioCommons and stored in
the per-user store keyed on the same WorkOS subject the token verifier uses.

Why a web page (not MCP elicitation): the PIN goes straight to this server over
TLS, never through Claude's wire. Per the per-session model the store is
in-memory and the raw PIN is never persisted to disk.

Enabled only when WorkOS is configured *with an API key* (browser code exchange
needs the confidential client secret) — see web_settings_from_env(). The token
verifier (auth.py) still needs no secret; only this page does.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
import urllib.parse
from dataclasses import dataclass

import anyio
import httpx
from starlette.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from starlette.routing import Route

from .client import Client
from .credentials import CredentialStore, UserCredentials

logger = logging.getLogger(__name__)

_STATE_MAX_AGE = 600  # seconds a login attempt's state stays valid


class WebSettingsConfigError(RuntimeError):
    """Account settings page is half-configured (e.g. no public URL)."""


@dataclass
class WebSettingsConfig:
    client_id: str
    api_key: str
    public_base: str  # external origin, e.g. https://getbiblio.app
    api_base: str = "https://api.workos.com"
    session_secret: str = ""
    session_max_age: int = 3600
    cookie_secure: bool = True

    @property
    def redirect_uri(self) -> str:
        return f"{self.public_base.rstrip('/')}/account/callback"


def web_settings_from_env() -> WebSettingsConfig | None:
    """Build config from env, or None if the page isn't configured.

    Enabled when WORKOS_CLIENT_ID + WORKOS_API_KEY are both set (the API key is
    the confidential secret needed for the browser code exchange). Requires a
    public origin: BIBLIOCOMMONS_MCP_PUBLIC_URL, or derived from
    BIBLIOCOMMONS_MCP_RESOURCE (stripping a trailing /mcp). The cookie-signing
    secret defaults to a value derived from the API key so sessions are stable
    across restarts without an extra env var.
    """
    client_id = os.environ.get("WORKOS_CLIENT_ID")
    api_key = os.environ.get("WORKOS_API_KEY")
    if not (client_id and api_key):
        return None

    public_base = os.environ.get("BIBLIOCOMMONS_MCP_PUBLIC_URL")
    if not public_base:
        resource = os.environ.get("BIBLIOCOMMONS_MCP_RESOURCE", "")
        if resource.endswith("/mcp"):
            public_base = resource[: -len("/mcp")]
    if not public_base:
        raise WebSettingsConfigError(
            "account settings page needs a public origin: set "
            "BIBLIOCOMMONS_MCP_PUBLIC_URL (e.g. https://getbiblio.app) or a "
            "BIBLIOCOMMONS_MCP_RESOURCE ending in /mcp."
        )
    session_secret = (
        os.environ.get("WEB_SESSION_SECRET")
        or hashlib.sha256(api_key.encode()).hexdigest()
    )
    return WebSettingsConfig(
        client_id=client_id,
        api_key=api_key,
        public_base=public_base,
        api_base=os.environ.get("WORKOS_API_BASE", "https://api.workos.com"),
        session_secret=session_secret,
    )


# ---- tiny stdlib-only signed token (avoids an itsdangerous dependency) ----


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _sign(secret: str, data: str, *, salt: str = "") -> str:
    body = _b64e(json.dumps({"d": data, "t": int(time.time())}).encode())
    sig = _b64e(
        hmac.new(secret.encode(), (salt + body).encode(), hashlib.sha256).digest()
    )
    return f"{body}.{sig}"


def _unsign(secret: str, token: str, *, max_age: int, salt: str = "") -> str | None:
    try:
        body, sig = token.split(".", 1)
        expected = _b64e(
            hmac.new(secret.encode(), (salt + body).encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64d(body))
        if int(time.time()) - int(payload["t"]) > max_age:
            return None
        return payload["d"]
    except Exception:
        return None


class AccountSettings:
    """Starlette routes for the `/account` credential-capture flow.

    ``exchange_code`` and ``validate_credentials`` are injectable for testing;
    the defaults call WorkOS and BiblioCommons respectively.
    """

    def __init__(
        self,
        cfg: WebSettingsConfig,
        store: CredentialStore,
        *,
        exchange_code=None,
        validate_credentials=None,
        on_credentials_changed=None,
    ) -> None:
        self.cfg = cfg
        self.store = store
        self._exchange = exchange_code or self._default_exchange
        self._validate = validate_credentials or self._default_validate
        self._on_credentials_changed = on_credentials_changed

    @property
    def routes(self) -> list[Route]:
        return [
            Route("/account/login", self.login, methods=["GET"]),
            Route("/account/callback", self.callback, methods=["GET"]),
            Route("/account", self.account, methods=["GET", "POST"]),
            Route("/account/logout", self.logout, methods=["POST"]),
        ]

    # --- default integrations ---

    async def _default_exchange(self, code: str) -> str:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{self.cfg.api_base}/user_management/authenticate",
                json={
                    "client_id": self.cfg.client_id,
                    "client_secret": self.cfg.api_key,
                    "grant_type": "authorization_code",
                    "code": code,
                },
            )
            r.raise_for_status()
            return r.json()["user"]["id"]

    async def _default_validate(self, library: str, card: str, pin: str) -> None:
        # Client.authenticate is blocking + network; run off the event loop.
        def _do() -> None:
            Client(library).authenticate(card, pin)

        await anyio.to_thread.run_sync(_do)

    # --- helpers ---

    def _set_cookie(self, resp, name: str, value: str, max_age: int) -> None:
        resp.set_cookie(
            name,
            value,
            max_age=max_age,
            httponly=True,
            secure=self.cfg.cookie_secure,
            samesite="lax",
            path="/account",
        )

    def _session_subject(self, request) -> str | None:
        cookie = request.cookies.get("bc_session")
        if not cookie:
            return None
        return _unsign(
            self.cfg.session_secret, cookie, max_age=self.cfg.session_max_age
        )

    # --- handlers ---

    async def login(self, request):
        state = secrets.token_urlsafe(16)
        params = urllib.parse.urlencode(
            {
                "response_type": "code",
                "client_id": self.cfg.client_id,
                "redirect_uri": self.cfg.redirect_uri,
                "provider": "authkit",
                "state": state,
            }
        )
        resp = RedirectResponse(
            f"{self.cfg.api_base}/user_management/authorize?{params}", status_code=302
        )
        self._set_cookie(
            resp, "bc_state", _sign(self.cfg.session_secret, state, salt="state"), 600
        )
        return resp

    async def callback(self, request):
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        cookie = request.cookies.get("bc_state")
        expected = (
            _unsign(
                self.cfg.session_secret, cookie, max_age=_STATE_MAX_AGE, salt="state"
            )
            if cookie
            else None
        )
        if not code or not state or state != expected:
            return PlainTextResponse(
                "Login link expired or invalid. Start again from /account.",
                status_code=400,
            )
        try:
            subject = await self._exchange(code)
        except Exception:
            logger.warning("WorkOS code exchange failed", exc_info=True)
            return PlainTextResponse(
                "Sign-in failed. Please try again.", status_code=400
            )
        resp = RedirectResponse("/account", status_code=302)
        self._set_cookie(
            resp,
            "bc_session",
            _sign(self.cfg.session_secret, subject),
            self.cfg.session_max_age,
        )
        resp.delete_cookie("bc_state", path="/account")
        return resp

    async def account(self, request):
        subject = self._session_subject(request)
        if not subject:
            return RedirectResponse("/account/login", status_code=302)

        if request.method == "POST":
            form = await request.form()
            library = (form.get("library") or "").strip()
            card = (form.get("card") or "").strip()
            pin = (form.get("pin") or "").strip()
            if not (library and card and pin):
                return HTMLResponse(
                    _page(error="Library, card number, and PIN are all required."),
                    status_code=400,
                )
            try:
                await self._validate(library, card, pin)
            except Exception:
                return HTMLResponse(
                    _page(
                        error="Couldn't sign in to that library with this card and "
                        "PIN. Double-check them and try again."
                    ),
                    status_code=400,
                )
            self.store.put(
                subject,
                UserCredentials(
                    library=library,
                    card=card,
                    pin=pin,
                    default_pickup_branch=(form.get("default_pickup_branch") or None),
                    default_format=(form.get("default_format") or None),
                    digital_notification_email=(
                        form.get("digital_notification_email") or None
                    ),
                ),
            )
            if self._on_credentials_changed is not None:
                self._on_credentials_changed(subject)
            return HTMLResponse(_page(saved=True))

        return HTMLResponse(_page(configured=self.store.get(subject) is not None))

    async def logout(self, request):
        resp = RedirectResponse("/account/login", status_code=302)
        resp.delete_cookie("bc_session", path="/account")
        return resp


def _page(*, error: str = "", saved: bool = False, configured: bool = False) -> str:
    """Minimal self-contained HTML for the settings form. No PIN is ever echoed."""
    banner = ""
    if saved:
        banner = (
            '<p class="ok">Saved. You can close this tab and use the connector.</p>'
        )
    elif error:
        banner = f'<p class="err">{error}</p>'
    elif configured:
        banner = '<p class="ok">A library card is on file. Re-submit to update it.</p>'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>getbiblio · library account</title>
<style>
 body {{ font-family: system-ui, sans-serif; max-width: 32rem;
        margin: 3rem auto; padding: 0 1rem; }}
 label {{ display:block; margin:.75rem 0 .25rem; font-weight:600; }}
 input {{ width:100%; padding:.5rem; font-size:1rem; box-sizing:border-box; }}
 button {{ margin-top:1.25rem; padding:.6rem 1.2rem; font-size:1rem; }}
 .ok {{ color:#137333; }} .err {{ color:#c5221f; }}
 small {{ color:#555; }}
</style></head><body>
<h1>Connect your library card</h1>
<p>Used only to act on your behalf in the catalog. Your PIN is kept in memory
for this session and never written to disk.</p>
{banner}
<form method="post" action="/account">
 <label>Library subdomain <small>(e.g. seattle, sfpl)</small></label>
 <input name="library" autocomplete="off" required>
 <label>Card number</label>
 <input name="card" autocomplete="off" required>
 <label>PIN</label>
 <input name="pin" type="password" autocomplete="off" required>
 <label>Default pickup branch <small>(optional)</small></label>
 <input name="default_pickup_branch" autocomplete="off">
 <label>Digital notification email <small>(optional)</small></label>
 <input name="digital_notification_email" type="email" autocomplete="off">
 <button type="submit">Save</button>
</form>
</body></html>"""


def register_account_routes(mcp, cfg: WebSettingsConfig, store: CredentialStore, **kw):
    """Register the /account routes on an MCPServer instance's HTTP app."""
    app = AccountSettings(cfg, store, **kw)
    for route in app.routes:
        mcp.custom_route(route.path, methods=list(route.methods or ["GET"]))(
            route.endpoint
        )
    return app
