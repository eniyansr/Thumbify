"""Unit tests for validation and sanitization utilities."""

import pytest
from app.utils.validators import (
    validate_owner,
    sanitize_filename,
    validate_file_size,
    format_size,
    is_video_extension,
)


def test_validate_owner():
    """Test owner authorization check."""
    owner_id = 123456789
    assert validate_owner(123456789, owner_id) is True
    assert validate_owner("123456789", owner_id) is True
    assert validate_owner(987654321, owner_id) is False
    assert validate_owner(None, owner_id) is False


def test_sanitize_filename_path_traversal():
    """Test that path traversal attempts are neutralized."""
    assert sanitize_filename("../../../etc/shadow") == "shadow"
    assert sanitize_filename("..\\..\\Windows\\System32\\calc.exe") == "calc.exe"
    assert sanitize_filename("/var/log/syslog.txt") == "syslog.txt"


def test_sanitize_filename_prohibited_characters():
    """Test removal of illegal characters (<>:"/\\|?*)."""
    assert sanitize_filename('bad<name>:test?.mp4') == 'bad_name__test_.mp4'
    assert sanitize_filename('sample*file|name".pdf') == 'sample_file_name_.pdf'


def test_sanitize_filename_empty_or_whitespace():
    """Test fallback when filename is empty or whitespace."""
    assert sanitize_filename("") == "file"
    assert sanitize_filename("   ") == "file"
    assert sanitize_filename("...", default_name="document.pdf") == "document.pdf"


def test_validate_file_size():
    """Test file size validation."""
    max_size = 400 * 1024 * 1024  # 400 MB
    assert validate_file_size(1024, max_size) is True
    assert validate_file_size(max_size, max_size) is True
    assert validate_file_size(0, max_size) is False
    assert validate_file_size(-100, max_size) is False
    assert validate_file_size(max_size + 1, max_size) is False


def test_format_size():
    """Test readable size formatting."""
    assert format_size(500) == "500 B"
    assert format_size(1024 * 50) == "50.0 KB"
    assert format_size(1024 * 1024 * 350) == "350.0 MB"
    assert format_size(1024 * 1024 * 1024 * 2) == "2.00 GB"


def test_is_video_extension():
    """Test video extension detection."""
    assert is_video_extension("movie.mp4") is True
    assert is_video_extension("clip.MKV") is True
    assert is_video_extension("archive.zip") is False
    assert is_video_extension("report.pdf") is False

