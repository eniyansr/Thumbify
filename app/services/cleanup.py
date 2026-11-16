"""Cleanup service for safe removal of temporary files and stale downloads."""

import time
from pathlib import Path
from typing import Optional, Union, Sequence
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CleanupService:
    """Manages secure and robust cleanup of temporary files and download workspaces."""

    def __init__(self, download_dir: Path) -> None:
        self.download_dir = Path(download_dir).resolve()

    def remove_file(self, file_path: Optional[Union[str, Path]]) -> bool:
        """
        Safely remove a single file, catching Windows file locks or permission issues.

        Args:
            file_path: Path to the file to be deleted.

        Returns:
            True if removed or already absent, False if removal failed.
        """
        if not file_path:
            return True

        target = Path(file_path).resolve()
        if not target.exists():
            return True

        # Safety check: Prevent deleting outside download_dir or deleting assets
        try:
            if not target.is_relative_to(self.download_dir):
                logger.warning("Refusing to delete file outside download directory: %s", target)
                return False
        except AttributeError:
            # Python < 3.9 fallback, though we are on Python 3.12+
            if str(self.download_dir) not in str(target):
                logger.warning("Refusing to delete file outside download directory: %s", target)
                return False

        try:
            target.unlink(missing_ok=True)
            logger.debug("Successfully cleaned up temporary file: %s", target.name)
            return True
        except PermissionError as exc:
            logger.warning("Permission denied deleting '%s' (file may be in use): %s", target.name, exc)
            return False
        except Exception as exc:
            logger.warning("Unexpected error deleting '%s': %s", target.name, exc)
            return False

    def remove_files(self, file_paths: Sequence[Optional[Union[str, Path]]]) -> None:
        """Safely remove a sequence of temporary files."""
        for path in file_paths:
            self.remove_file(path)

    def cleanup_stale_downloads(self, max_age_seconds: int = 7200) -> int:
        """
        Scan download_dir and remove files older than max_age_seconds (default 2 hours).

        Returns:
            Number of removed stale files.
        """
        if not self.download_dir.exists():
            return 0

        now = time.time()
        removed_count = 0

        for item in self.download_dir.iterdir():
            if item.is_file() and item.name != ".gitkeep":
                try:
                    file_age = now - item.stat().st_mtime
                    if file_age > max_age_seconds:
                        item.unlink(missing_ok=True)
                        removed_count += 1
                        logger.info("Removed stale temporary file: %s", item.name)
                except Exception as exc:
                    logger.warning("Error inspecting/removing stale file '%s': %s", item.name, exc)

        return removed_count

