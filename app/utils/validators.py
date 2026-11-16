"""Validation and sanitization utilities for THUMBIFY."""

import re
from pathlib import Path
from typing import Optional, Set

# Prohibited filename characters on Windows/Linux and control characters
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

SUPPORTED_EXTENSIONS: Set[str] = {
    # Video extensions
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".m4v", ".3gp", ".ts",
    # Document / Archive extensions
    ".pdf", ".zip", ".rar", ".7z", ".tar", ".gz", ".apk",
    ".docx", ".xlsx", ".pptx", ".doc", ".xls", ".ppt",
    ".txt", ".csv", ".json", ".epub", ".iso",
}


def validate_owner(user_id: Optional[int], owner_id: int) -> bool:
    """Check if the requesting user matches the authorized owner ID."""
    if user_id is None:
        return False
    return int(user_id) == int(owner_id)


def sanitize_filename(filename: Optional[str], default_name: str = "file") -> str:
    """
    Sanitize a filename to prevent path traversal, injection, or invalid characters.

    Args:
        filename: Original user-provided filename.
        default_name: Fallback base name if the provided name is empty or invalid.

    Returns:
        Safe, sanitized filename with path traversal characters stripped.
    """
    if not filename or not filename.strip():
        return default_name

    # Extract only the base name (strip any directory parts: / or \)
    raw_name = Path(filename.strip()).name

    # Remove dangerous/illegal characters
    sanitized = INVALID_FILENAME_CHARS.sub("_", raw_name)

    # Remove leading dots or spaces (e.g. .. or .hidden or hidden.)
    sanitized = sanitized.strip(". ")

    # If completely empty after stripping, return default_name
    if not sanitized:
        return default_name

    # Truncate length if excessively long (max 255 chars)
    if len(sanitized) > 255:
        stem = Path(sanitized).stem[:240]
        suffix = Path(sanitized).suffix[:15]
        sanitized = f"{stem}{suffix}"

    return sanitized


def validate_file_size(size_bytes: int, max_file_size: int) -> bool:
    """
    Check if a file size is within acceptable limits.

    Args:
        size_bytes: Size of the incoming file in bytes.
        max_file_size: Maximum allowed size in bytes.

    Returns:
        True if size is between 1 byte and max_file_size, False otherwise.
    """
    return 0 < size_bytes <= max_file_size


def format_size(size_bytes: int) -> str:
    """Format bytes into human-readable string (KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def is_video_extension(filename: str) -> bool:
    """Check if the filename has a common video extension."""
    suffix = Path(filename).suffix.lower()
    return suffix in {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".m4v", ".3gp", ".ts"}

