"""Handler for incoming media uploads (videos and documents)."""

from typing import Any
from telethon import events
from app.config import AppConfig
from app.services.file_transfer import FileTransferService
from app.utils.validators import validate_owner
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_upload_handlers(
    bot: Any,
    config: AppConfig,
    transfer_service: FileTransferService,
) -> None:
    """Register media upload handler."""

    @bot.client.on(events.NewMessage)
    async def handle_media_upload(event: events.NewMessage.Event) -> None:
        # Ignore messages that are not private chats
        if not event.is_private:
            return

        # Security: strictly verify owner identity
        if not validate_owner(event.sender_id, config.owner_id):
            logger.warning(
                "Unauthorized upload attempt blocked from sender_id: %s",
                event.sender_id
            )
            return

        # Ignore bot commands
        text = (event.message.text or "").strip()
        if text.startswith("/"):
            return

        # Verify that the message contains a media file (document, video, audio)
        if not event.message.file:
            # Plain text message that isn't a command
            await event.respond(
                "💬 Send or forward any video or document file, and I'll apply your fixed thumbnail to it.\n"
                "Type /help for instructions."
            )
            return

        # Send initial acknowledgment
        status_msg = await event.respond("⏳ File received. Validating...")

        # Run file processing pipeline
        await transfer_service.process_media(event=event, status_msg=status_msg)

