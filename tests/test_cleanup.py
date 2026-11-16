"""Unit tests for CleanupService."""

import time
from pathlib import Path
from app.services.cleanup import CleanupService


def test_cleanup_single_file(tmp_path):
    """Test standard single file cleanup within download directory."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()

    temp_file = download_dir / "temp_video.mp4"
    temp_file.write_bytes(b"dummy video data")

    service = CleanupService(download_dir=download_dir)
    assert temp_file.exists()

    result = service.remove_file(temp_file)
    assert result is True
    assert not temp_file.exists()


def test_cleanup_non_existent_file(tmp_path):
    """Test cleanup of already removed or non-existent file."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()

    service = CleanupService(download_dir=download_dir)
    result = service.remove_file(download_dir / "ghost_file.mp4")
    assert result is True


def test_refuse_delete_outside_download_dir(tmp_path):
    """Test that files outside download_dir are protected from deletion."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()

    protected_file = tmp_path / "important_asset.jpg"
    protected_file.write_bytes(b"precious asset data")

    service = CleanupService(download_dir=download_dir)
    result = service.remove_file(protected_file)

    assert result is False
    assert protected_file.exists()


def test_cleanup_stale_downloads(tmp_path):
    """Test removal of old files while preserving new ones and .gitkeep."""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()

    gitkeep = download_dir / ".gitkeep"
    gitkeep.write_text("")

    recent_file = download_dir / "recent.mp4"
    recent_file.write_bytes(b"recent content")

    stale_file = download_dir / "stale.mp4"
    stale_file.write_bytes(b"stale content")

    # Set stale_file mtime to 3 hours ago
    old_time = time.time() - 10800
    import os
    os.utime(stale_file, (old_time, old_time))

    service = CleanupService(download_dir=download_dir)
    removed = service.cleanup_stale_downloads(max_age_seconds=7200)

    assert removed == 1
    assert not stale_file.exists()
    assert recent_file.exists()
    assert gitkeep.exists()

