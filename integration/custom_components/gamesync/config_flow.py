"""Config flow for GameSync integration."""

from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ADDON_HOST,
    CONF_ADDON_PORT,
    DEFAULT_ADDON_HOST,
    DEFAULT_ADDON_PORT,
    DOMAIN,
)


async def _test_connection(hass: HomeAssistant, host: str, port: int) -> bool:
    """Test connectivity to the GameSync add-on."""
    url = f"http://{host}:{port}/api/health"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return resp.status == 200
    except Exception:
        return False


class GameSyncConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GameSync."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            host = user_input[CONF_ADDON_HOST]
            port = user_input[CONF_ADDON_PORT]

            if await _test_connection(self.hass, host, port):
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"GameSync ({host}:{port})",
                    data=user_input,
                )
            else:
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_ADDON_HOST, default=DEFAULT_ADDON_HOST): str,
                vol.Required(CONF_ADDON_PORT, default=DEFAULT_ADDON_PORT): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
