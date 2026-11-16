"""Entrypoint for THUMBIFY - Telegram Auto Thumbnail Bot."""

import asyncio
import atexit
import os
import sys
from pathlib import Path
from app.config import load_config, ConfigError
from app.services.thumbnail import ThumbnailError
from app.bot import ThumbifyBot
from app.utils.crypto_patch import apply_crypto_acceleration
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
PID_FILE = Path("thumbify.pid")


def _write_pid() -> None:
    """Record current process ID for background process management."""
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")


def _remove_pid() -> None:
    """Remove PID file on clean exit."""
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def main() -> None:
    """Load configuration, validate environment, and run the bot."""
    print("=" * 60)
    print("  THUMBIFY — Telegram Auto Thumbnail Bot")
    print("=" * 60)

    # Enable hardware AES-IGE acceleration
    apply_crypto_acceleration()

    try:
        config = load_config()
    except ConfigError as exc:
        print(f"\n[CONFIGURATION ERROR] {exc}\n")
        print("Please check your .env file or copy .env.example to .env and configure it.")
        sys.exit(1)

    _write_pid()
    atexit.register(_remove_pid)

    try:
        bot = ThumbifyBot(config=config)
        asyncio.run(bot.run())
    except ThumbnailError as exc:
        print(f"\n[THUMBNAIL ERROR] {exc}\n")
        print("Please verify that assets/thumbnail.jpg exists and is a valid image.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutdown requested by user. Exiting THUMBIFY...")
    except Exception as exc:
        logger.exception("Fatal error occurred during bot execution: %s", exc)
        sys.exit(1)
    finally:
        _remove_pid()


if __name__ == "__main__":
    main()
