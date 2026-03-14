"""Light control via HA services."""

from __future__ import annotations

import logging

from gamesync.ha_client.client import HAClient

logger = logging.getLogger(__name__)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color (#RRGGBB) to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


class LightController:
    """Control HA light entities."""

    def __init__(self, client: HAClient) -> None:
        self._client = client

    async def turn_on(
        self,
        entity_id: str,
        color_hex: str | None = None,
        brightness: int | None = None,
        transition: float | None = None,
    ) -> None:
        """Turn on a light with optional color/brightness."""
        data: dict = {"entity_id": entity_id}

        if color_hex:
            data["rgb_color"] = list(hex_to_rgb(color_hex))
        if brightness is not None:
            data["brightness"] = max(0, min(255, brightness))
        if transition is not None:
            data["transition"] = transition

        await self._client.call_service("light", "turn_on", data)

    async def turn_off(
        self, entity_id: str, transition: float | None = None
    ) -> None:
        data: dict = {"entity_id": entity_id}
        if transition is not None:
            data["transition"] = transition
        await self._client.call_service("light", "turn_off", data)

    async def get_state(self, entity_id: str) -> dict:
        """Get current state of a light entity."""
        return await self._client.get_state(entity_id)

    async def capture_states(self, entity_ids: list[str]) -> dict[str, dict]:
        """Capture current state of multiple lights for later restoration."""
        states = {}
        for eid in entity_ids:
            try:
                state = await self.get_state(eid)
                states[eid] = {
                    "state": state.get("state"),
                    "attributes": state.get("attributes", {}),
                }
            except Exception:
                logger.warning("Failed to capture state for %s", eid)
        return states

    async def restore_states(self, saved_states: dict[str, dict]) -> None:
        """Restore lights to previously captured state."""
        for eid, state_data in saved_states.items():
            try:
                if state_data["state"] == "off":
                    await self.turn_off(eid)
                else:
                    attrs = state_data.get("attributes", {})
                    color_hex = None
                    rgb = attrs.get("rgb_color")
                    if rgb:
                        color_hex = "#{:02x}{:02x}{:02x}".format(*rgb)
                    brightness = attrs.get("brightness")
                    await self.turn_on(eid, color_hex=color_hex, brightness=brightness)
            except Exception:
                logger.warning("Failed to restore state for %s", eid)

    async def get_all_lights(self) -> list[dict]:
        """Get all light entities from HA."""
        states = await self._client.get_states()
        return [
            {
                "entity_id": s["entity_id"],
                "name": s.get("attributes", {}).get("friendly_name", s["entity_id"]),
                "state": s["state"],
                "attributes": s.get("attributes", {}),
            }
            for s in states
            if s["entity_id"].startswith("light.")
        ]
