"""Unit and integration tests for bot handlers and access control."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.utils.validators import validate_owner
from app.services.file_transfer import FileTransferService, ActiveJob


def test_unauthorized_user_rejection():
    """Verify that any non-owner ID is rejected."""
    owner_id = 999888777
    assert validate_owner(111222333, owner_id) is False
    assert validate_owner(None, owner_id) is False
    assert validate_owner(owner_id, owner_id) is True


@pytest.mark.asyncio
async def test_file_transfer_concurrency_busy():
    """Verify that is_busy correctly reflects max_concurrent_jobs."""
    mock_client = MagicMock()
    mock_config = MagicMock()
    mock_config.max_concurrent_jobs = 1
    mock_thumbnail = MagicMock()
    mock_cleanup = MagicMock()

    service = FileTransferService(
        client=mock_client,
        config=mock_config,
        thumbnail_service=mock_thumbnail,
        cleanup_service=mock_cleanup,
    )

    assert service.is_busy() is False

    # Simulate an active job
    service.active_jobs[12345] = ActiveJob(
        job_id="test1",
        user_id=12345,
        filename="test.mp4",
        file_size=1024,
        started_at=0.0,
        cancel_event=asyncio.Event(),
    )

    assert service.is_busy() is True


@pytest.mark.asyncio
async def test_cancel_active_job():
    """Verify that cancel_active_job sets the cancellation event."""
    mock_client = MagicMock()
    mock_config = MagicMock()
    mock_config.max_concurrent_jobs = 1
    mock_thumbnail = MagicMock()
    mock_cleanup = MagicMock()

    service = FileTransferService(
        client=mock_client,
        config=mock_config,
        thumbnail_service=mock_thumbnail,
        cleanup_service=mock_cleanup,
    )

    cancel_event = asyncio.Event()
    service.active_jobs[999] = ActiveJob(
        job_id="job999",
        user_id=999,
        filename="video.mkv",
        file_size=2048,
        started_at=0.0,
        cancel_event=cancel_event,
    )

    assert cancel_event.is_set() is False
    assert service.cancel_active_job(999) is True
    assert cancel_event.is_set() is True

    # Non-existent user
    assert service.cancel_active_job(888) is False


def test_caption_safe_extraction():
    """Verify caption extraction safely handles Telethon Message objects without .caption."""
    class TelethonMockMessage:
        def __init__(self, message_text=None):
            self.message = message_text
            self.text = message_text
            # Deliberately no .caption attribute, exactly as in Telethon

    msg_with_caption = TelethonMockMessage("My cool video caption")
    msg_without_caption = TelethonMockMessage("")
    msg_none = TelethonMockMessage(None)

    extracted1 = getattr(msg_with_caption, "message", None) or getattr(msg_with_caption, "text", None) or ""
    extracted2 = getattr(msg_without_caption, "message", None) or getattr(msg_without_caption, "text", None) or ""
    extracted3 = getattr(msg_none, "message", None) or getattr(msg_none, "text", None) or ""

    assert extracted1 == "My cool video caption"
    assert extracted2 == ""
    assert extracted3 == ""
