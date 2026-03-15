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


async def async_emergency_stop(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle gamesync.emergency_stop — kills all active effects immediately."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        return
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{coordinator.base_url}/global/emergency-stop",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                result = await resp.json()
                _LOGGER.info(
                    "GameSync emergency stop: %d effects cancelled",
                    result.get("stopped_count", 0),
                )
    except Exception as e:
        _LOGGER.error("GameSync: Emergency stop failed: %s", e)


async def async_mute_toggle(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle gamesync.mute_toggle — toggle global mute state."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        return
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{coordinator.base_url}/global/mute",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                result = await resp.json()
                muted = result.get("muted", False)
                _LOGGER.info("GameSync mute toggled: muted=%s", muted)
                hass.bus.async_fire("gamesync_mute_changed", {"muted": muted})
    except Exception as e:
        _LOGGER.error("GameSync: Mute toggle failed: %s", e)


async def async_set_primary_session(hass: HomeAssistant, call: ServiceCall) -> None:
    """Handle gamesync.set_primary_session — switch the active primary game."""
    coordinator = _get_coordinator(hass)
    if not coordinator:
        return
    session_id = call.data.get("session_id")
    if not session_id:
        _LOGGER.error("GameSync: set_primary_session requires session_id")
        return
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{coordinator.base_url}/sessions/{session_id}/make-primary",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                _LOGGER.info("GameSync primary session set: %s", session_id)
                hass.bus.async_fire("gamesync_session_changed", {"primary_session_id": session_id})
        await coordinator.async_request_refresh()
    except Exception as e:
        _LOGGER.error("GameSync: set_primary_session failed: %s", e)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register GameSync services."""
    hass.services.async_register(DOMAIN, "trigger_effect", async_trigger_effect)
    hass.services.async_register(DOMAIN, "set_delay", async_set_delay)
    hass.services.async_register(DOMAIN, "emergency_stop", async_emergency_stop)
    hass.services.async_register(DOMAIN, "mute_toggle", async_mute_toggle)
    hass.services.async_register(DOMAIN, "set_primary_session", async_set_primary_session)
    hass.services.async_register(DOMAIN, "refresh", async_refresh)
