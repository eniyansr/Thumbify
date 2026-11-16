"""Unit tests for ThumbnailService."""

import pytest
from pathlib import Path
from PIL import Image
from app.services.thumbnail import ThumbnailService, ThumbnailError


def test_missing_thumbnail_file(tmp_path):
    """Test that missing thumbnail file raises ThumbnailError."""
    service = ThumbnailService(raw_path=tmp_path / "does_not_exist.jpg")
    with pytest.raises(ThumbnailError) as exc_info:
        service.initialize()
    assert "Thumbnail file not found" in str(exc_info.value)


def test_invalid_thumbnail_corrupt_data(tmp_path):
    """Test that a corrupt non-image file raises ThumbnailError."""
    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_bytes(b"NOT_AN_IMAGE_DATA_123456")

    service = ThumbnailService(raw_path=corrupt_file)
    with pytest.raises(ThumbnailError) as exc_info:
        service.initialize()
    assert "Failed to process thumbnail" in str(exc_info.value)


def test_resize_and_compress_large_png(tmp_path):
    """Test that a large PNG image is resized to <=320x180 and converted to JPEG <=20KB."""
    large_png = tmp_path / "large.png"
    # Create 1920x1080 RGBA image
    img = Image.new("RGBA", (1920, 1080), color=(255, 0, 0, 128))
    img.save(large_png, format="PNG")

    service = ThumbnailService(raw_path=large_png, output_dir=tmp_path)
    ready_path = service.initialize()

    assert ready_path.exists()
    assert ready_path.name == "thumbnail_optimized.jpg"

    # Verify with Pillow
    with Image.open(ready_path) as res_img:
        assert res_img.format == "JPEG"
        assert res_img.mode == "RGB"
        w, h = res_img.size
        assert w <= 320
        assert h <= 180

    # Verify file size <= 20 KB (20480 bytes)
    assert ready_path.stat().st_size <= 20 * 1024

    metadata = service.get_thumbnail_metadata()
    assert metadata["format"] == "JPEG"
    assert metadata["width"] <= 320
    assert metadata["height"] <= 180
    assert metadata["size_bytes"] <= 20 * 1024


def test_already_compliant_thumbnail(tmp_path):
    """Test that an image already within specifications is directly accepted."""
    compliant_jpg = tmp_path / "compliant.jpg"
    img = Image.new("RGB", (320, 180), color=(0, 128, 255))
    img.save(compliant_jpg, format="JPEG", quality=80)

    service = ThumbnailService(raw_path=compliant_jpg)
    ready_path = service.initialize()
    assert ready_path == compliant_jpg


def test_existing_workspace_thumbnail():
    """Test that the workspace assets/thumbnail.jpg loads and validates successfully."""
    workspace_thumb = Path("assets/thumbnail.jpg").resolve()
    if workspace_thumb.exists():
        service = ThumbnailService(raw_path=workspace_thumb)
        ready_path = service.initialize()
        assert ready_path.exists()
        metadata = service.get_thumbnail_metadata()
        assert metadata["size_bytes"] <= 20 * 1024
        assert metadata["width"] <= 320
        assert metadata["height"] <= 180

