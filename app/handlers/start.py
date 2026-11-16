"""Handler for /start command."""

from typing import Any
from telethon import events
from app.config import AppConfig
from app.utils.validators import format_size, validate_owner
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def register_start_handler(bot: Any, config: AppConfig) -> None:
    """Register /start command handler."""

    @bot.client.on(events.NewMessage(pattern=r"^/start$"))
    async def handle_start(event: events.NewMessage.Event) -> None:
        if not event.is_private or not validate_owner(event.sender_id, config.owner_id):
            logger.warning("Unauthorized /start attempt from user_id: %s", event.sender_id)
            return

        max_size_str = format_size(config.max_file_size)
        welcome_text = (
            "👋 **Welcome to THUMBIFY!**\n\n"
            "Your personal Telegram Auto Thumbnail Bot.\n\n"
            "Send any supported video or document and I'll return it using your configured thumbnail.\n\n"
            f"📦 **Maximum file size:** {max_size_str}\n\n"
            "Use /help to view available commands."
        )
        await event.respond(welcome_text)
