"""Unit tests for configuration loading and validation."""

import pytest
from pathlib import Path
from app.config import load_config, ConfigError, AppConfig


def test_missing_required_variables(monkeypatch):
    """Test that missing required variables raise ConfigError."""
    monkeypatch.delenv("TG_API_ID", raising=False)
    monkeypatch.delenv("TG_API_HASH", raising=False)
    monkeypatch.delenv("TG_BOT_TOKEN", raising=False)
    monkeypatch.delenv("OWNER_ID", raising=False)

    with pytest.raises(ConfigError) as exc_info:
        load_config(env_path=Path("non_existent.env"))
    assert "Missing required configuration" in str(exc_info.value) or "TG_API" in str(exc_info.value)


def test_valid_configuration(monkeypatch, tmp_path):
    """Test loading a fully valid configuration."""
    monkeypatch.setenv("TG_API_ID", "1234567")
    monkeypatch.setenv("TG_API_HASH", "abcdef0123456789abcdef0123456789")
    monkeypatch.setenv("TG_BOT_TOKEN", "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ_123")
    monkeypatch.setenv("OWNER_ID", "987654321")
    monkeypatch.setenv("MAX_FILE_SIZE", "314572800")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    config = load_config(env_path=tmp_path / ".env")
    assert isinstance(config, AppConfig)
    assert config.tg_api_id == 1234567
    assert config.tg_api_hash == "abcdef0123456789abcdef0123456789"
    assert config.owner_id == 987654321
    assert config.max_file_size == 314572800
    assert config.log_level == "DEBUG"
    assert config.max_concurrent_jobs == 1
    assert config.retry_count == 3


def test_invalid_bot_token(monkeypatch, tmp_path):
    """Test that a malformed bot token is rejected."""
    monkeypatch.setenv("TG_API_ID", "1234567")
    monkeypatch.setenv("TG_API_HASH", "valid_hash_123")
    monkeypatch.setenv("TG_BOT_TOKEN", "invalid-bot-token-without-colon")
    monkeypatch.setenv("OWNER_ID", "987654321")

    with pytest.raises(ConfigError) as exc_info:
        load_config(env_path=tmp_path / ".env")
    assert "TG_BOT_TOKEN" in str(exc_info.value)


def test_invalid_owner_id(monkeypatch, tmp_path):
    """Test that a non-integer or negative OWNER_ID is rejected."""
    monkeypatch.setenv("TG_API_ID", "1234567")
    monkeypatch.setenv("TG_API_HASH", "valid_hash_123")
    monkeypatch.setenv("TG_BOT_TOKEN", "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ")
    monkeypatch.setenv("OWNER_ID", "-5")

    with pytest.raises(ConfigError) as exc_info:
        load_config(env_path=tmp_path / ".env")
    assert "positive integer" in str(exc_info.value)


def test_safe_repr(monkeypatch, tmp_path):
    """Test that __repr__ does not expose raw secret hash or full token."""
    monkeypatch.setenv("TG_API_ID", "1234567")
    monkeypatch.setenv("TG_API_HASH", "super_secret_hash")
    monkeypatch.setenv("TG_BOT_TOKEN", "999999999:VERY_SECRET_TOKEN_VALUE")
    monkeypatch.setenv("OWNER_ID", "987654321")

    config = load_config(env_path=tmp_path / ".env")
    rep = repr(config)
    assert "super_secret_hash" not in rep
    assert "VERY_SECRET_TOKEN_VALUE" not in rep
    assert "999999999:***" in rep

