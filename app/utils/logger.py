"""Structured logging configuration for THUMBIFY."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Base logs directory
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


class SensitiveDataFilter(logging.Filter):
    """Filter that masks sensitive tokens or hashes from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.msg)
        # Prevent token leaking
        if ":" in msg and any(c.isdigit() for c in msg.split(":")[0]):
            # Possible bot token pattern
            import re
            msg = re.sub(r"\d{8,12}:[A-Za-z0-9_-]{30,}", "[REDACTED_BOT_TOKEN]", msg)
            record.msg = msg
        return True


def setup_logger(
    name: str = "thumbify",
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """
    Configure and return a thread-safe logger with console and rotating file handlers.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    target_file = log_file or (LOGS_DIR / "thumbify.log")

    logger = logging.getLogger(name)
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    sensitive_filter = SensitiveDataFilter()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sensitive_filter)
    logger.addHandler(console_handler)

    # Rotating File Handler (5 MB per file, max 5 backup files)
    file_handler = RotatingFileHandler(
        filename=target_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(sensitive_filter)
    logger.addHandler(file_handler)

    return logger

