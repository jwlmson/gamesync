"""Media player control via HA services."""

from __future__ import annotations

import logging

from gamesync.ha_client.client import HAClient

logger = logging.getLogger(__name__)


class MediaController:
    """Control HA media_player entities for audio playback."""

    def __init__(self, client: HAClient) -> None:
        self._client = client

    async def play_media(
        self,
        entity_id: str,
        media_url: str,
        media_type: str = "music",
    ) -> None:
        """Play audio on a media_player entity."""
        await self._client.call_service(
            "media_player",
            "play_media",
            {
                "entity_id": entity_id,
                "media_content_id": media_url,
                "media_content_type": media_type,
            },
        )
        logger.debug("Playing media on %s: %s", entity_id, media_url)

    async def set_volume(self, entity_id: str, volume: float) -> None:
        """Set volume level (0.0 - 1.0)."""
        await self._client.call_service(
            "media_player",
            "volume_set",
            {"entity_id": entity_id, "volume_level": volume},
        )

    async def stop(self, entity_id: str) -> None:
        await self._client.call_service(
            "media_player", "media_stop", {"entity_id": entity_id}
        )

    async def get_all_media_players(self) -> list[dict]:
        """Get all media_player entities from HA."""
        states = await self._client.get_states()
        return [
            {
                "entity_id": s["entity_id"],
                "name": s.get("attributes", {}).get("friendly_name", s["entity_id"]),
                "state": s["state"],
            }
            for s in states
            if s["entity_id"].startswith("media_player.")
        ]
