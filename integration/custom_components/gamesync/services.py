"""Service handlers for GameSync HA integration."""

from __future__ import annotations

import logging

import aiohttp
from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN
from .coordinator import GameSyncCoordinator

_LOGGER = logging.getLogger(__name__)


def _get_coordinator(hass: HomeAssistant) -> GameSyncCoordinator | None:
    """Get first coordinator entry."""
    entries = hass.data.get(DOMAIN, {})
    if entries:
        return next(iter(entries.values()))
    return None


async def async_trigger_effect(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle gamesync.trigger_effect service call."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        _LOGGER.error("GameSync: No coordinator available")
        return

    team_id = call.data.get("team_id", "")
    event_type = call.data.get("event_type", "score_change")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{coordinator.base_url}/effects/trigger",
                json={"team_id": team_id, "event_type": event_type},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                _LOGGER.info("GameSync effect triggered: %s / %s", team_id, event_type)
    except Exception as e:
        _LOGGER.error("GameSync: Failed to trigger effect: %s", e)


async def async_set_delay(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle gamesync.set_delay service call."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        return

    team_id = call.data.get("team_id", "")
    delay = call.data.get("delay_seconds", 0)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{coordinator.base_url}/teams/follow/{team_id}",
                json={"delay_seconds": delay},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                _LOGGER.info("GameSync delay set: %s = %ds", team_id, delay)
    except Exception as e:
        _LOGGER.error("GameSync: Failed to set delay: %s", e)


async def async_refresh(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle gamesync.refresh service call."""
    coordinator = _get_coordinator(hass)
    if coordinator:
        await coordinator.async_request_refresh()


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register GameSync services."""
    hass.services.async_register(DOMAIN, "trigger_effect", async_trigger_effect)
    hass.services.async_register(DOMAIN, "set_delay", async_set_delay)
    hass.services.async_register(DOMAIN, "refresh", async_refresh)
