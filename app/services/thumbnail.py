"""Thumbnail service for loading, validating, resizing, and caching fixed thumbnails."""

import io
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from PIL import Image


class ThumbnailError(ValueError):
    """Raised when thumbnail validation or processing fails."""
    pass


class ThumbnailService:
    """
    Manages the fixed thumbnail lifecycle.
    Loads, validates, automatically resizes/compresses to Telegram-compliant specs,
    and caches the thumbnail for all subsequent uploads.
    """

    TARGET_WIDTH = 320
    TARGET_HEIGHT = 180
    MAX_FILE_SIZE_BYTES = 20 * 1024  # 20 KB preferred target

    def __init__(self, raw_path: Path, output_dir: Optional[Path] = None) -> None:
        self.raw_path = Path(raw_path).resolve()
        self.output_dir = (
            Path(output_dir).resolve() if output_dir else self.raw_path.parent
        )
        self.processed_path: Optional[Path] = None
        self._metadata: Optional[Dict[str, Any]] = None

    def initialize(self) -> Path:
        """
        Validate and initialize the thumbnail. If necessary, generates an
        optimized, resized, and compressed JPEG thumbnail.

        Returns:
            Path to the verified, ready-to-use thumbnail file.

        Raises:
            ThumbnailError: If the thumbnail file does not exist or is corrupted.
        """
        if not self.raw_path.exists():
            raise ThumbnailError(
                f"Thumbnail file not found at '{self.raw_path}'. "
                f"Please place a valid image at '{self.raw_path}'."
            )

        if not self.raw_path.is_file():
            raise ThumbnailError(
                f"Thumbnail path '{self.raw_path}' is not a regular file."
            )

        try:
            with Image.open(self.raw_path) as img:
                img_format = img.format
                width, height = img.size
                file_size = self.raw_path.stat().st_size

                # Check if it is already a compliant JPEG <= 320x180 and <= 20 KB
                is_compliant = (
                    img_format == "JPEG"
                    and width <= self.TARGET_WIDTH
                    and height <= self.TARGET_HEIGHT
                    and file_size <= self.MAX_FILE_SIZE_BYTES
                )

                if is_compliant:
                    self.processed_path = self.raw_path
                    self._metadata = {
                        "path": str(self.processed_path),
                        "width": width,
                        "height": height,
                        "size_bytes": file_size,
                        "format": "JPEG",
                    }
                    return self.processed_path

                # Otherwise, optimize and produce a compliant cached version
                optimized_path = self.output_dir / "thumbnail_optimized.jpg"
                self._optimize_and_save(img, optimized_path)
                self.processed_path = optimized_path
                return self.processed_path

        except Exception as exc:
            if isinstance(exc, ThumbnailError):
                raise
            raise ThumbnailError(f"Failed to process thumbnail image: {exc}") from exc

    def _optimize_and_save(self, img: Image.Image, destination: Path) -> None:
        """Resize, convert to RGB, compress under target size, and save as JPEG."""
        try:
            # Convert to RGB mode if RGBA, P, CMYK, etc.
            if img.mode != "RGB":
                rgb_img = img.convert("RGB")
            else:
                rgb_img = img.copy()

            # Resize maintaining aspect ratio to fit inside TARGET_WIDTH x TARGET_HEIGHT
            rgb_img.thumbnail(
                (self.TARGET_WIDTH, self.TARGET_HEIGHT),
                Image.Resampling.LANCZOS,
            )

            # Iteratively compress quality to stay under MAX_FILE_SIZE_BYTES
            quality = 90
            min_quality = 20
            buffer = io.BytesIO()

            while quality >= min_quality:
                buffer.seek(0)
                buffer.truncate()
                rgb_img.save(buffer, format="JPEG", quality=quality, optimize=True)
                if buffer.tell() <= self.MAX_FILE_SIZE_BYTES:
                    break
                quality -= 10

            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, "wb") as f:
                f.write(buffer.getvalue())

            final_w, final_h = rgb_img.size
            final_size = destination.stat().st_size

            self._metadata = {
                "path": str(destination),
                "width": final_w,
                "height": final_h,
                "size_bytes": final_size,
                "format": "JPEG",
            }
        except Exception as exc:
            raise ThumbnailError(f"Error compressing thumbnail: {exc}") from exc

    def get_thumbnail_path(self) -> Path:
        """Return the initialized thumbnail file path."""
        if not self.processed_path or not self.processed_path.exists():
            return self.initialize()
        return self.processed_path

    def get_thumbnail_metadata(self) -> Dict[str, Any]:
        """Return thumbnail metadata including dimensions and file size."""
        if not self._metadata:
            self.initialize()
        return self._metadata or {}

