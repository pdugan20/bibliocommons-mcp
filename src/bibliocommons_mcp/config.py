"""Config loader for bibliocommons-mcp.

Loads ~/.config/bibliocommons-mcp/config.toml (mode 0600). Env vars override:
  BIBLIOCOMMONS_MCP_CONFIG          override the config file path
  BIBLIOCOMMONS_LIBRARY             override library subdomain
  BIBLIOCOMMONS_CARD                override credentials.card
  BIBLIOCOMMONS_PIN                 override credentials.pin
  BIBLIOCOMMONS_PICKUP_BRANCH       override default_pickup_branch
  BIBLIOCOMMONS_DIGITAL_EMAIL       override digital_notification_email
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "bibliocommons-mcp" / "config.toml"


@dataclass(frozen=True)
class Config:
    library: str
    card: str
    pin: str
    default_pickup_branch: str | None = None
    default_format: str | None = None
    # Required for `place_digital_hold` — BC's gateway puts the digital
    # notification address inside `materialParams.email` on the hold
    # POST. The user already has one configured on the BC account
    # itself (visible in the gateway's `entities.accounts[...]
    # .digitalNotificationEmail` field), but we don't probe for it at
    # startup; let the user mirror it here if they want to place
    # digital holds, otherwise the tool fails with a clear message.
    digital_notification_email: str | None = None

    @classmethod
    def load(cls, path: Path | None = None) -> Config:
        path = Path(
            os.environ.get("BIBLIOCOMMONS_MCP_CONFIG", path or DEFAULT_CONFIG_PATH)
        )
        data: dict = {}
        if path.exists():
            data = tomllib.loads(path.read_text())
        creds = (
            data.get("credentials", {})
            if isinstance(data.get("credentials"), dict)
            else {}
        )

        library = os.environ.get("BIBLIOCOMMONS_LIBRARY") or data.get("library")
        card = os.environ.get("BIBLIOCOMMONS_CARD") or creds.get("card")
        pin = os.environ.get("BIBLIOCOMMONS_PIN") or creds.get("pin")

        if not library:
            raise ConfigError(
                f"missing 'library' (set in {path} or BIBLIOCOMMONS_LIBRARY)"
            )
        if not card or not pin:
            raise ConfigError(
                f"missing credentials (set [credentials] card+pin in {path} "
                "or BIBLIOCOMMONS_CARD / BIBLIOCOMMONS_PIN env vars)"
            )

        return cls(
            library=library,
            card=str(card),
            pin=str(pin),
            default_pickup_branch=(
                os.environ.get("BIBLIOCOMMONS_PICKUP_BRANCH")
                or data.get("default_pickup_branch")
            ),
            default_format=data.get("default_format"),
            digital_notification_email=(
                os.environ.get("BIBLIOCOMMONS_DIGITAL_EMAIL")
                or data.get("digital_notification_email")
            ),
        )


class ConfigError(RuntimeError):
    pass
