"""Unit tests for config loading. No network."""

from __future__ import annotations

import pytest

from bibliocommons_mcp.config import Config, ConfigError


def test_loads_from_toml(sample_config):
    cfg = Config.load()
    assert cfg.library == "seattle"
    assert cfg.default_pickup_branch == "Lake City"
    assert cfg.default_format == "MUSIC_CD"
    assert cfg.card == "1000000000000"
    assert cfg.pin == "0000"


def test_env_overrides_library(sample_config, monkeypatch):
    monkeypatch.setenv("BIBLIOCOMMONS_LIBRARY", "sfpl")
    cfg = Config.load()
    assert cfg.library == "sfpl"


def test_env_overrides_card_and_pin(sample_config, monkeypatch):
    monkeypatch.setenv("BIBLIOCOMMONS_CARD", "9999")
    monkeypatch.setenv("BIBLIOCOMMONS_PIN", "abcd")
    cfg = Config.load()
    assert cfg.card == "9999"
    assert cfg.pin == "abcd"


def test_env_overrides_pickup_branch(sample_config, monkeypatch):
    monkeypatch.setenv("BIBLIOCOMMONS_PICKUP_BRANCH", "Central Library")
    cfg = Config.load()
    assert cfg.default_pickup_branch == "Central Library"


def test_missing_library_raises(tmp_path, monkeypatch):
    cfg_path = tmp_path / "empty.toml"
    cfg_path.write_text("[credentials]\ncard = '1'\npin = '2'\n")
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_CONFIG", str(cfg_path))
    monkeypatch.delenv("BIBLIOCOMMONS_LIBRARY", raising=False)
    with pytest.raises(ConfigError, match="library"):
        Config.load()


def test_missing_credentials_raises(tmp_path, monkeypatch):
    cfg_path = tmp_path / "no-creds.toml"
    cfg_path.write_text('library = "seattle"\n')
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_CONFIG", str(cfg_path))
    monkeypatch.delenv("BIBLIOCOMMONS_CARD", raising=False)
    monkeypatch.delenv("BIBLIOCOMMONS_PIN", raising=False)
    with pytest.raises(ConfigError, match="credentials"):
        Config.load()


def test_readonly_load_allows_library_only(tmp_path, monkeypatch):
    """require_credentials=False boots catalog mode with no card/pin."""
    cfg_path = tmp_path / "no-creds.toml"
    cfg_path.write_text('library = "seattle"\n')
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_CONFIG", str(cfg_path))
    monkeypatch.delenv("BIBLIOCOMMONS_CARD", raising=False)
    monkeypatch.delenv("BIBLIOCOMMONS_PIN", raising=False)
    cfg = Config.load(require_credentials=False)
    assert cfg.library == "seattle"
    assert cfg.card is None
    assert cfg.pin is None
    assert cfg.has_credentials is False


def test_has_credentials_true_with_card_and_pin(sample_config):
    assert Config.load().has_credentials is True


def test_readonly_load_still_requires_library(tmp_path, monkeypatch):
    cfg_path = tmp_path / "empty.toml"
    cfg_path.write_text("")
    monkeypatch.setenv("BIBLIOCOMMONS_MCP_CONFIG", str(cfg_path))
    monkeypatch.delenv("BIBLIOCOMMONS_LIBRARY", raising=False)
    with pytest.raises(ConfigError, match="library"):
        Config.load(require_credentials=False)


def test_env_works_without_file(tmp_path, monkeypatch):
    """All values from env, no config file at all."""
    monkeypatch.setenv(
        "BIBLIOCOMMONS_MCP_CONFIG", str(tmp_path / "does-not-exist.toml")
    )
    monkeypatch.setenv("BIBLIOCOMMONS_LIBRARY", "sfpl")
    monkeypatch.setenv("BIBLIOCOMMONS_CARD", "x")
    monkeypatch.setenv("BIBLIOCOMMONS_PIN", "y")
    cfg = Config.load()
    assert cfg.library == "sfpl"
    assert cfg.card == "x"
    assert cfg.pin == "y"
