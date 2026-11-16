"""Main bot controller class coordinating Telethon MTProto client and services."""

import asyncio
from pathlib import Path
from telethon import TelegramClient
from app.config import AppConfig
from app.services.thumbnail import ThumbnailService
from app.services.cleanup import CleanupService
from app.services.file_transfer import FileTransferService
from app.handlers.start import register_start_handler
from app.handlers.commands import register_command_handlers
from app.handlers.uploads import register_upload_handlers
from app.utils.crypto_patch import apply_crypto_acceleration
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ThumbifyBot:
    """Core bot controller for THUMBIFY Telegram Auto Thumbnail Bot."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._stopped = False

        self.thumbnail_service = ThumbnailService(
            raw_path=config.thumbnail_path,
            output_dir=config.thumbnail_path.parent,
        )
        self.cleanup_service = CleanupService(
            download_dir=config.download_dir,
        )

        # Store session file in workspace root
        session_path = Path("thumbify_bot")
        self.client = TelegramClient(
            session=str(session_path),
            api_id=config.tg_api_id,
            api_hash=config.tg_api_hash,
            # Robust connection settings
            timeout=120,
            auto_reconnect=True,
            retry_delay=3,
        )

        self.transfer_service = FileTransferService(
            client=self.client,
            config=self.config,
            thumbnail_service=self.thumbnail_service,
            cleanup_service=self.cleanup_service,
        )

    async def start(self) -> None:
        """Initialize crypto acceleration, thumbnail, cleanup, and connect MTProto bot client."""
        logger.info("Initializing THUMBIFY bot...")

        # 1. Enable hardware crypto acceleration
        apply_crypto_acceleration()

        # 2. Validate and prepare fixed thumbnail
        thumb_path = self.thumbnail_service.initialize()
        thumb_meta = self.thumbnail_service.get_thumbnail_metadata()
        logger.info(
            "Thumbnail loaded and validated: %s (%dx%d, %d bytes)",
            thumb_path.name,
            thumb_meta.get("width", 0),
            thumb_meta.get("height", 0),
            thumb_meta.get("size_bytes", 0),
        )

        # 3. Clean up any stale files from previous sessions
        stale_cleaned = self.cleanup_service.cleanup_stale_downloads(max_age_seconds=0)
        if stale_cleaned > 0:
            logger.info("Cleaned up %d stale temporary files.", stale_cleaned)

        # 4. Connect to Telegram MTProto
        logger.info("Connecting to Telegram MTProto as bot account...")
        await self.client.start(bot_token=self.config.tg_bot_token)

        me = await self.client.get_me()
        logger.info("Connected successfully as @%s (ID: %s)", me.username, me.id)
        logger.info("Authorized Owner ID: %s", self.config.owner_id)

        # 5. Register event handlers
        register_start_handler(self, self.config)
        register_command_handlers(self, self.config, self.thumbnail_service, self.transfer_service)
        register_upload_handlers(self, self.config, self.transfer_service)
        logger.info("All handlers registered successfully.")

    async def run(self) -> None:
        """Start the bot and keep listening for events with automatic reconnect."""
        await self.start()
        logger.info("Bot is now listening for events. Press Ctrl+C to terminate.")

        while not self._stopped:
            try:
                await self.client.run_until_disconnected()
                if self._stopped:
                    break
                logger.warning("Bot disconnected from Telegram. Attempting reconnection in 5s...")
                await asyncio.sleep(5)
                if not self.client.is_connected():
                    await self.client.connect()
            except (ConnectionError, asyncio.TimeoutError) as exc:
                logger.warning("Connection lost (%s). Reconnecting in 5s...", exc)
                await asyncio.sleep(5)
                try:
                    if not self.client.is_connected():
                        await self.client.connect()
                except Exception as rec_err:
                    logger.error("Failed to reconnect: %s", rec_err)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception("Unexpected error in bot event loop: %s", exc)
                await asyncio.sleep(5)

    async def stop(self) -> None:
        """Disconnect client and release resources cleanly."""
        self._stopped = True
        logger.info("Stopping THUMBIFY bot...")
        if self.client.is_connected():
            await self.client.disconnect()
        logger.info("THUMBIFY bot stopped cleanly.")
