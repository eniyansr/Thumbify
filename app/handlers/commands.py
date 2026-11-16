"""Command handlers for /help, /status, /id, /cancel, /thumbnail, and /info."""

import sys
import time
from typing import Any
from telethon import events
from app import __version__
from app.config import AppConfig
from app.services.thumbnail import ThumbnailService
from app.services.file_transfer import FileTransferService
from app.utils.validators import validate_owner, format_size
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_command_handlers(
    bot: Any,
    config: AppConfig,
    thumbnail_service: ThumbnailService,
    transfer_service: FileTransferService,
) -> None:
    """Register all administrative bot commands."""

    start_time = time.time()

    @bot.client.on(events.NewMessage(pattern=r"^/help$"))
    async def handle_help(event: events.NewMessage.Event) -> None:
        if not event.is_private or not validate_owner(event.sender_id, config.owner_id):
            return

        max_size_str = format_size(config.max_file_size)
        help_text = (
            "📖 **THUMBIFY Help & Instructions**\n\n"
            "**Supported Formats:**\n"
            "• **Videos:** MP4, MKV, MOV, AVI, WEBM, FLV, WMV, 3GP, TS\n"
            "• **Documents:** PDF, ZIP, RAR, APK, DOCX, XLSX, PPTX, TXT, and other Telegram files\n\n"
            f"**File Size Limit:** Up to {max_size_str}\n\n"
            "**How to use:**\n"
            "1. Simply send or forward any video or document file directly to this chat.\n"
            "2. The bot will download the file, apply your fixed thumbnail, and send it back to you.\n"
            "3. Original filenames, extensions, and captions are preserved.\n\n"
            "ℹ️ _Note: Telegram clients on Android render video thumbnails instantly in the inline player. "
            "For documents, thumbnail preview support depends on Telegram client caching and file type._\n\n"
            "**Available Commands:**\n"
            "/start — Welcome message\n"
            "/help — This guide\n"
            "/status — Current bot, job, and thumbnail status\n"
            "/thumbnail — View your configured fixed thumbnail\n"
            "/cancel — Cancel an ongoing transfer\n"
            "/id — Show your Telegram User ID\n"
            "/info — Version and environment details"
        )
        await event.respond(help_text)

    @bot.client.on(events.NewMessage(pattern=r"^/status$"))
    async def handle_status(event: events.NewMessage.Event) -> None:
        if not event.is_private or not validate_owner(event.sender_id, config.owner_id):
            return

        uptime_seconds = int(time.time() - start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        # Thumbnail status
        try:
            meta = thumbnail_service.get_thumbnail_metadata()
            thumb_info = (
                f"✅ Loaded ({meta.get('width', 0)}x{meta.get('height', 0)} px, "
                f"{format_size(meta.get('size_bytes', 0))})"
            )
        except Exception as exc:
            thumb_info = f"❌ Error: {exc}"

        # Job status
        active_job = transfer_service.active_jobs.get(config.owner_id)
        if active_job:
            elapsed = int(time.time() - active_job.started_at)
            job_status = (
                f"🔄 Active: '{active_job.filename}'\n"
                f"• Stage: {active_job.current_stage}\n"
                f"• Size: {format_size(active_job.file_size)}\n"
                f"• Running for: {elapsed}s"
            )
        else:
            job_status = "🟢 Idle (ready for new uploads)"

        status_text = (
            "📊 **THUMBIFY System Status**\n\n"
            f"• **Bot Status:** Online\n"
            f"• **Uptime:** {uptime_str}\n"
            f"• **Fixed Thumbnail:** {thumb_info}\n"
            f"• **Processing Queue:** {job_status}\n"
            f"• **Max File Size:** {format_size(config.max_file_size)}"
        )
        await event.respond(status_text)

    @bot.client.on(events.NewMessage(pattern=r"^/id$"))
    async def handle_id(event: events.NewMessage.Event) -> None:
        if not event.is_private or not validate_owner(event.sender_id, config.owner_id):
            return

        await event.respond(
            f"🆔 **Your Telegram ID:** `{event.sender_id}`\n"
            f"👑 **Role:** Authorized Owner"
        )

    @bot.client.on(events.NewMessage(pattern=r"^/cancel$"))
    async def handle_cancel(event: events.NewMessage.Event) -> None:
        if not event.is_private or not validate_owner(event.sender_id, config.owner_id):
            return

        cancelled = transfer_service.cancel_active_job(config.owner_id)
        if cancelled:
            await event.respond("🛑 Cancellation signal sent. The active transfer will terminate shortly.")
        else:
            await event.respond("ℹ️ No active transfer job found to cancel.")

    @bot.client.on(events.NewMessage(pattern=r"^/thumbnail$"))
    async def handle_thumbnail(event: events.NewMessage.Event) -> None:
        if not event.is_private or not validate_owner(event.sender_id, config.owner_id):
            return

        try:
            thumb_path = thumbnail_service.get_thumbnail_path()
            meta = thumbnail_service.get_thumbnail_metadata()
            caption = (
                f"🖼 **Fixed Thumbnail Preview**\n\n"
                f"• Dimensions: {meta.get('width', 0)} × {meta.get('height', 0)} pixels\n"
                f"• Format: {meta.get('format', 'JPEG')}\n"
                f"• Size: {format_size(meta.get('size_bytes', 0))}\n"
                f"• Path: `{thumb_path.name}`"
            )
            await bot.client.send_file(
                entity=event.chat_id,
                file=thumb_path,
                caption=caption,
            )
        except Exception as exc:
            logger.exception("Failed to send thumbnail preview: %s", exc)
            await event.respond(f"❌ Failed to load thumbnail: {exc}")

    @bot.client.on(events.NewMessage(pattern=r"^/info$"))
    async def handle_info(event: events.NewMessage.Event) -> None:
        if not event.is_private or not validate_owner(event.sender_id, config.owner_id):
            return

        info_text = (
            "ℹ️ **THUMBIFY System Information**\n\n"
            f"• **Version:** {__version__}\n"
            f"• **Engine:** Telethon MTProto Client\n"
            f"• **Python:** {sys.version.split()[0]}\n"
            f"• **Max Transfer Size:** {format_size(config.max_file_size)}\n"
            f"• **Max Concurrent Jobs:** {config.max_concurrent_jobs}\n"
            f"• **Transfer Timeout:** {config.transfer_timeout}s\n"
            f"• **Retries:** {config.retry_count}\n"
            f"• **Owner ID:** `{config.owner_id}`"
        )
        await event.respond(info_text)

