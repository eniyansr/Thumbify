"""Large-file transfer engine using Telethon MTProto with progress tracking and rate-limiting."""

import asyncio
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, Any, Dict
from telethon import TelegramClient, errors
from telethon.tl.types import (
    DocumentAttributeVideo,
    DocumentAttributeFilename,
    Message,
)
from app.config import AppConfig
from app.services.thumbnail import ThumbnailService
from app.services.media_info import MediaInfoService
from app.services.cleanup import CleanupService
from app.utils.validators import (
    sanitize_filename,
    validate_file_size,
    format_size,
    is_video_extension,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ActiveJob:
    """Represents an active in-flight transfer job."""
    job_id: str
    user_id: int
    filename: str
    file_size: int
    started_at: float
    cancel_event: asyncio.Event
    current_stage: str = "Initializing"


class TransferCancelledError(Exception):
    """Raised when an active transfer is cancelled by the owner."""
    pass


class FileTransferService:
    """
    Manages streaming large-file downloads and uploads using Telethon MTProto,
    with progress throttling, cancellation, and error handling.
    """

    PROGRESS_THROTTLE_SECONDS = 5.0  # Conservative throttle to completely avoid Telegram FloodWait

    def __init__(
        self,
        client: TelegramClient,
        config: AppConfig,
        thumbnail_service: ThumbnailService,
        cleanup_service: CleanupService,
    ) -> None:
        self.client = client
        self.config = config
        self.thumbnail_service = thumbnail_service
        self.cleanup_service = cleanup_service
        self.semaphore = asyncio.Semaphore(config.max_concurrent_jobs)
        self.active_jobs: Dict[int, ActiveJob] = {}

    def is_busy(self) -> bool:
        """Check if max concurrent jobs limit has been reached."""
        return len(self.active_jobs) >= self.config.max_concurrent_jobs

    def cancel_active_job(self, user_id: int) -> bool:
        """Signal cancellation to an active job for the user."""
        job = self.active_jobs.get(user_id)
        if job:
            job.cancel_event.set()
            logger.info("Cancellation requested for job %s (user %s)", job.job_id, user_id)
            return True
        return False

    async def _safe_edit_message(self, status_msg: Message, text: str) -> None:
        """Safely edit status message, handling FloodWait or RPC errors without throwing."""
        try:
            await status_msg.edit(text)
        except errors.FloodWaitError as exc:
            logger.warning("Telegram FloodWait of %d seconds encountered while editing status.", exc.seconds)
            if exc.seconds <= 5:
                await asyncio.sleep(exc.seconds + 0.5)
                try:
                    await status_msg.edit(text)
                except Exception:
                    pass
        except errors.MessageNotModifiedError:
            pass
        except Exception as exc:
            logger.debug("Non-critical notice editing status message: %s", exc)

    def _create_progress_callback(
        self,
        status_msg: Message,
        action_name: str,
        total_size: int,
        cancel_event: asyncio.Event,
    ) -> Callable[[int, int], Any]:
        """
        Create a throttled progress callback that updates Telegram status
        and checks for cancellation, strictly preventing overlapping edit tasks.
        """
        last_update_time = [0.0]
        last_percent = [-1]
        is_updating = [False]

        def callback(current: int, total: int) -> None:
            if cancel_event.is_set():
                raise TransferCancelledError("Transfer cancelled by user.")

            effective_total = total or total_size
            if effective_total <= 0:
                return

            percent = int((current / effective_total) * 100)
            now = time.time()

            if (now - last_update_time[0] >= self.PROGRESS_THROTTLE_SECONDS) or percent >= 100:
                if percent != last_percent[0] and not is_updating[0]:
                    last_update_time[0] = now
                    last_percent[0] = percent
                    is_updating[0] = True
                    text = (
                        f"⏳ {action_name}... {percent}%\n"
                        f"📊 {format_size(current)} / {format_size(effective_total)}"
                    )

                    async def do_update():
                        try:
                            await self._safe_edit_message(status_msg, text)
                        finally:
                            is_updating[0] = False

                    asyncio.create_task(do_update())

        return callback

    async def process_media(self, event: Any, status_msg: Message) -> None:
        """
        Complete processing pipeline for received media file:
        Validate -> Download -> Inspect -> Apply Fixed Thumbnail -> Upload -> Cleanup.
        """
        message = event.message
        user_id = event.sender_id
        job_id = str(uuid.uuid4())[:8]

        # Extract file properties
        file_obj = message.file
        if not file_obj:
            await self._safe_edit_message(status_msg, "❌ No media file detected in this message.")
            return

        raw_filename = file_obj.name or "media_file"
        sanitized_name = sanitize_filename(raw_filename, default_name=f"file_{job_id}")
        file_size = file_obj.size or 0

        # Validate file size
        if not validate_file_size(file_size, self.config.max_file_size):
            err_msg = (
                f"❌ File size exceeds application limit.\n"
                f"File size: {format_size(file_size)}\n"
                f"Maximum allowed: {format_size(self.config.max_file_size)}"
            )
            await self._safe_edit_message(status_msg, err_msg)
            return

        # Check concurrency
        if self.is_busy():
            await self._safe_edit_message(
                status_msg,
                "⚠️ Bot is busy processing another file. Please wait for the current job to complete."
            )
            return

        cancel_event = asyncio.Event()
        job = ActiveJob(
            job_id=job_id,
            user_id=user_id,
            filename=sanitized_name,
            file_size=file_size,
            started_at=time.time(),
            cancel_event=cancel_event,
        )
        self.active_jobs[user_id] = job

        temp_download_path = self.config.download_dir / f"{job_id}_{sanitized_name}"

        try:
            async with self.semaphore:
                # Stage 1: Download
                job.current_stage = "Downloading"
                await self._safe_edit_message(
                    status_msg,
                    f"📥 Starting download of '{sanitized_name}' ({format_size(file_size)})..."
                )
                logger.info(
                    "[%s] Starting download of '%s' (%s) for user %s",
                    job_id, sanitized_name, format_size(file_size), user_id
                )

                download_callback = self._create_progress_callback(
                    status_msg=status_msg,
                    action_name="Downloading file",
                    total_size=file_size,
                    cancel_event=cancel_event,
                )

                downloaded_file = await self.client.download_media(
                    message=message,
                    file=temp_download_path,
                    progress_callback=download_callback,
                )

                if not downloaded_file or not Path(downloaded_file).exists():
                    raise RuntimeError("Download completed but destination file was not found.")

                download_path = Path(downloaded_file)
                logger.info("[%s] Download completed successfully: %s", job_id, download_path.name)

                # Stage 2: Fixed Thumbnail Preparation
                job.current_stage = "Applying Thumbnail"
                await self._safe_edit_message(status_msg, "🎨 Applying fixed thumbnail...")
                thumbnail_path = self.thumbnail_service.get_thumbnail_path()
                logger.info("[%s] Using fixed thumbnail: %s", job_id, thumbnail_path)

                # Stage 3: Media Inspection & Attributes Preparation
                is_video = is_video_extension(sanitized_name) or bool(message.video)
                attributes = [DocumentAttributeFilename(file_name=sanitized_name)]

                # Determine whether to send as document with thumbnail (default) or video player
                if not self.config.force_document and is_video:
                    media_meta = MediaInfoService.inspect(download_path)
                    logger.info(
                        "[%s] Video inspected: duration=%ss, w=%s, h=%s",
                        job_id, media_meta.duration, media_meta.width, media_meta.height
                    )
                    attributes.append(
                        DocumentAttributeVideo(
                            duration=media_meta.duration,
                            w=media_meta.width or 320,
                            h=media_meta.height or 180,
                            supports_streaming=True,
                        )
                    )
                    send_as_doc = False
                else:
                    # Output as document with thumbnail (matching user's reference card)
                    send_as_doc = True
                    logger.info("[%s] Preparing document delivery with custom thumbnail: %s", job_id, sanitized_name)

                # Stage 4: Upload Processed File
                job.current_stage = "Uploading"
                await self._safe_edit_message(
                    status_msg,
                    f"📤 Uploading processed '{sanitized_name}' with custom thumbnail..."
                )
                logger.info("[%s] Uploading processed file to chat %s", job_id, event.chat_id)

                upload_callback = self._create_progress_callback(
                    status_msg=status_msg,
                    action_name="Uploading processed file",
                    total_size=file_size,
                    cancel_event=cancel_event,
                )

                original_caption = (
                    getattr(message, "message", None)
                    or getattr(message, "text", None)
                    or ""
                )

                await self.client.send_file(
                    entity=event.chat_id,
                    file=download_path,
                    caption=original_caption,
                    thumb=str(thumbnail_path),
                    attributes=attributes,
                    force_document=send_as_doc,
                    progress_callback=upload_callback,
                )

                duration = time.time() - job.started_at
                await self._safe_edit_message(
                    status_msg,
                    f"✅ Completed successfully in {duration:.1f}s!\n"
                    f"📁 File: `{sanitized_name}`\n"
                    f"📦 Size: {format_size(file_size)}"
                )
                logger.info("[%s] Job completed successfully in %.2fs", job_id, duration)

        except TransferCancelledError:
            logger.info("[%s] Transfer was cancelled by user.", job_id)
            await self._safe_edit_message(status_msg, "🛑 Transfer cancelled by owner.")

        except errors.FloodWaitError as exc:
            logger.error("[%s] Telegram FloodWait: %d seconds required", job_id, exc.seconds)
            await self._safe_edit_message(
                status_msg,
                f"⚠️ Telegram rate limit reached. Please wait {exc.seconds} seconds."
            )

        except (errors.TimedOutError, asyncio.TimeoutError) as exc:
            logger.error("[%s] Network timeout occurred during transfer: %s", job_id, exc)
            await self._safe_edit_message(
                status_msg,
                "⚠️ Network timeout occurred. Please retry your transfer."
            )

        except Exception as exc:
            logger.exception("[%s] Unexpected error processing file: %s", job_id, exc)
            await self._safe_edit_message(
                status_msg,
                f"❌ Processing failed: {type(exc).__name__}. Please check bot logs."
            )

        finally:
            # Stage 5: Clean up temporary files
            self.cleanup_service.remove_file(temp_download_path)
            self.active_jobs.pop(user_id, None)
