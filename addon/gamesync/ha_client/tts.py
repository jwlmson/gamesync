"""Text-to-speech via HA services."""

from __future__ import annotations

import logging

from gamesync.ha_client.client import HAClient

logger = logging.getLogger(__name__)


class TTSController:
    """Text-to-speech announcements via HA TTS service."""

    def __init__(self, client: HAClient) -> None:
        self._client = client

    async def speak(
        self,
        entity_id: str,
        message: str,
        language: str = "en",
    ) -> None:
        """Announce a message via TTS on a media_player."""
        await self._client.call_service(
            "tts",
            "speak",
            {
                "entity_id": entity_id,
                "message": message,
                "language": language,
            },
        )
        logger.debug("TTS on %s: %s", entity_id, message)
