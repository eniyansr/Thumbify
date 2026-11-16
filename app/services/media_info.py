"""Media metadata inspection for videos and documents using Hachoir and FFprobe."""

import subprocess
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class MediaMetadata:
    """Metadata extracted from video/audio/document files."""
    duration: int = 0
    width: int = 0
    height: int = 0
    is_video: bool = False
    codec: str = ""


class MediaInfoService:
    """Service to inspect and extract video dimensions, duration, and attributes."""

    @staticmethod
    def inspect(file_path: Path) -> MediaMetadata:
        """
        Inspect a media file and return its duration, width, height.
        Attempts hachoir first, then ffprobe if available.
        """
        file_path = Path(file_path).resolve()
        metadata = MediaMetadata()

        if not file_path.exists():
            return metadata

        # Try pure-Python hachoir first
        try:
            from hachoir.parser import createParser
            from hachoir.metadata import extractMetadata

            parser = createParser(str(file_path))
            if parser:
                with parser:
                    extracted = extractMetadata(parser)
                    if extracted:
                        metadata.is_video = True
                        if extracted.has("duration"):
                            # Duration in seconds
                            metadata.duration = int(extracted.get("duration").seconds)
                        if extracted.has("width"):
                            metadata.width = int(extracted.get("width"))
                        if extracted.has("height"):
                            metadata.height = int(extracted.get("height"))
                        if extracted.has("compression"):
                            metadata.codec = str(extracted.get("compression"))
                        return metadata
        except Exception as exc:
            logger.debug("Hachoir inspection fallback: %s", exc)

        # Fallback to ffprobe if installed
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "stream=width,height,codec_name:format=duration",
                "-of", "json",
                str(file_path),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                streams = data.get("streams", [])
                video_streams = [s for s in streams if s.get("width") and s.get("height")]
                if video_streams:
                    v_stream = video_streams[0]
                    metadata.is_video = True
                    metadata.width = int(v_stream.get("width", 0))
                    metadata.height = int(v_stream.get("height", 0))
                    metadata.codec = v_stream.get("codec_name", "")

                fmt = data.get("format", {})
                if "duration" in fmt:
                    metadata.duration = int(float(fmt["duration"]))
        except Exception as exc:
            logger.debug("FFprobe inspection error: %s", exc)

        return metadata

