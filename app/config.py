"""Configuration management for THUMBIFY Telegram Auto Thumbnail Bot."""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent


class ConfigError(ValueError):
    """Raised when application configuration is missing or invalid."""
    pass


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration dataclass."""
    tg_api_id: int
    tg_api_hash: str
    tg_bot_token: str
    owner_id: int
    max_file_size: int
    max_concurrent_jobs: int
    download_dir: Path
    thumbnail_path: Path
    log_level: str
    retry_count: int
    transfer_timeout: int
    force_document: bool = True

    def __repr__(self) -> str:
        """Safe representation hiding sensitive credentials."""
        token_preview = (
            f"{self.tg_bot_token.split(':')[0]}:***"
            if ":" in self.tg_bot_token
            else "***"
        )
        return (
            f"AppConfig("
            f"tg_api_id={self.tg_api_id}, "
            f"tg_api_hash='***', "
            f"tg_bot_token='{token_preview}', "
            f"owner_id={self.owner_id}, "
            f"max_file_size={self.max_file_size} bytes, "
            f"max_concurrent_jobs={self.max_concurrent_jobs}, "
            f"download_dir='{self.download_dir}', "
            f"thumbnail_path='{self.thumbnail_path}', "
            f"force_document={self.force_document}, "
            f"log_level='{self.log_level}')"
        )


def _parse_int_env(var_name: str, value: Optional[str], default: Optional[int] = None) -> int:
    """Parse integer environment variable with descriptive errors."""
    if value is None or not value.strip():
        if default is not None:
            return default
        raise ConfigError(f"Missing required configuration: '{var_name}'")
    try:
        parsed = int(value.strip())
        if parsed <= 0:
            raise ConfigError(f"Configuration '{var_name}' must be a positive integer, got: {parsed}")
        return parsed
    except ValueError as exc:
        raise ConfigError(f"Configuration '{var_name}' must be an integer: {exc}") from exc


def load_config(env_path: Optional[Path] = None) -> AppConfig:
    """
    Load and validate environment configuration from .env file or environment.

    Raises:
        ConfigError: If any required setting is missing or invalid.
    """
    if env_path is not None:
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv(dotenv_path=BASE_DIR / ".env")

    # Required: TG_API_ID
    raw_api_id = os.getenv("TG_API_ID")
    tg_api_id = _parse_int_env("TG_API_ID", raw_api_id)

    # Required: TG_API_HASH
    tg_api_hash = (os.getenv("TG_API_HASH") or "").strip()
    if not tg_api_hash or tg_api_hash == "your_api_hash_here":
        raise ConfigError(
            "Missing or unconfigured 'TG_API_HASH'. Obtain it from https://my.telegram.org."
        )

    # Required: TG_BOT_TOKEN
    tg_bot_token = (os.getenv("TG_BOT_TOKEN") or "").strip()
    if not tg_bot_token or tg_bot_token.startswith("your_") or ":" not in tg_bot_token:
        raise ConfigError(
            "Missing or invalid 'TG_BOT_TOKEN'. Obtain a valid token from @BotFather."
        )
    if not re.match(r"^\d+:[A-Za-z0-9_-]+$", tg_bot_token):
        raise ConfigError(
            "Invalid format for 'TG_BOT_TOKEN'. Expected format: '<bot_id>:<secret_hash>'"
        )

    # Required: OWNER_ID
    raw_owner_id = os.getenv("OWNER_ID")
    owner_id = _parse_int_env("OWNER_ID", raw_owner_id)

    # Optional: MAX_FILE_SIZE (default 400 MB)
    raw_max_size = os.getenv("MAX_FILE_SIZE")
    max_file_size = _parse_int_env("MAX_FILE_SIZE", raw_max_size, default=400 * 1024 * 1024)

    # Optional: MAX_CONCURRENT_JOBS (default 1)
    raw_jobs = os.getenv("MAX_CONCURRENT_JOBS")
    max_concurrent_jobs = _parse_int_env("MAX_CONCURRENT_JOBS", raw_jobs, default=1)

    # Optional: DOWNLOAD_DIR (default BASE_DIR / "downloads")
    raw_download_dir = (os.getenv("DOWNLOAD_DIR") or "downloads").strip()
    download_dir = (BASE_DIR / raw_download_dir).resolve()

    # Optional: THUMBNAIL_PATH (default BASE_DIR / "assets" / "thumbnail.jpg")
    raw_thumbnail_path = (os.getenv("THUMBNAIL_PATH") or "assets/thumbnail.jpg").strip()
    thumbnail_path = (BASE_DIR / raw_thumbnail_path).resolve()

    # Optional: LOG_LEVEL (default INFO)
    log_level = (os.getenv("LOG_LEVEL") or "INFO").strip().upper()
    valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in valid_log_levels:
        raise ConfigError(
            f"Invalid 'LOG_LEVEL': {log_level}. Allowed: {', '.join(sorted(valid_log_levels))}"
        )

    # Optional: RETRY_COUNT (default 3)
    raw_retries = os.getenv("RETRY_COUNT")
    retry_count = _parse_int_env("RETRY_COUNT", raw_retries, default=3)

    # Optional: TRANSFER_TIMEOUT in seconds (default 3600 = 1 hour)
    raw_timeout = os.getenv("TRANSFER_TIMEOUT")
    transfer_timeout = _parse_int_env("TRANSFER_TIMEOUT", raw_timeout, default=3600)

    # Optional: FORCE_DOCUMENT (default True to output as document with thumbnail)
    raw_force_doc = (os.getenv("FORCE_DOCUMENT") or "true").strip().lower()
    force_document = raw_force_doc in ("1", "true", "yes", "on")

    # Ensure directories exist
    download_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        tg_api_id=tg_api_id,
        tg_api_hash=tg_api_hash,
        tg_bot_token=tg_bot_token,
        owner_id=owner_id,
        max_file_size=max_file_size,
        max_concurrent_jobs=max_concurrent_jobs,
        download_dir=download_dir,
        thumbnail_path=thumbnail_path,
        log_level=log_level,
        retry_count=retry_count,
        transfer_timeout=transfer_timeout,
        force_document=force_document,
    )
