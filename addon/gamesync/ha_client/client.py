"""Home Assistant Supervisor API client."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


class HAClient:
    """Client for the Home Assistant Supervisor REST API.

    Inside an HA add-on, the Supervisor API is available at
    http://supervisor/core/api with the SUPERVISOR_TOKEN env var.
    """

    def __init__(self, supervisor_url: str, supervisor_token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=supervisor_url,
            timeout=10.0,
            headers={
                "Authorization": f"Bearer {supervisor_token}",
                "Content-Type": "application/json",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def call_service(
        self, domain: str, service: str, data: dict | None = None
    ) -> dict:
        """Call a Home Assistant service."""
        url = f"/services/{domain}/{service}"
        resp = await self._client.post(url, json=data or {})
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    async def get_states(self) -> list[dict]:
        """Get all entity states."""
        resp = await self._client.get("/states")
        resp.raise_for_status()
        return resp.json()

    async def get_state(self, entity_id: str) -> dict:
        """Get state of a single entity."""
        resp = await self._client.get(f"/states/{entity_id}")
        resp.raise_for_status()
        return resp.json()

    async def fire_event(self, event_type: str, data: dict | None = None) -> None:
        """Fire an event on the HA event bus."""
        resp = await self._client.post(f"/events/{event_type}", json=data or {})
        resp.raise_for_status()
        logger.debug("Fired HA event: %s data=%s", event_type, data)
