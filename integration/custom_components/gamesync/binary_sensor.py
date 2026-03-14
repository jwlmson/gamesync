"""Binary sensor entities for GameSync — game_live, team_winning."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GameSyncCoordinator
from .models import TeamScore


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: GameSyncCoordinator = hass.data[DOMAIN][entry.entry_id]

    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{coordinator.base_url}/teams/followed",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                data = await resp.json()
                teams = data.get("teams", [])
    except Exception:
        teams = []

    entities = []
    for team in teams:
        team_id = team["team_id"]
        abbr = team_id.split(":")[-1][:6].upper()
        entities.extend([
            GameSyncLiveSensor(coordinator, team_id, abbr),
            GameSyncWinningSensor(coordinator, team_id, abbr),
        ])

    async_add_entities(entities)


class GameSyncLiveSensor(CoordinatorEntity[GameSyncCoordinator], BinarySensorEntity):
    """Binary sensor: ON when a game is live for this team."""

    def __init__(self, coordinator, team_id, abbr):
        super().__init__(coordinator)
        self._team_id = team_id
        self._abbr = abbr

    @property
    def unique_id(self) -> str:
        return f"gamesync_{self._team_id}_live"

    @property
    def name(self) -> str:
        return f"GameSync {self._abbr} Live"

    @property
    def device_class(self):
        return BinarySensorDeviceClass.RUNNING

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data:
            return False
        team = self.coordinator.data.teams.get(self._team_id)
        return team is not None and team.status in ("live", "halftime")

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._team_id)},
            "name": f"GameSync {self._abbr}",
            "manufacturer": "GameSync",
            "model": "Sports Tracker",
        }


class GameSyncWinningSensor(CoordinatorEntity[GameSyncCoordinator], BinarySensorEntity):
    """Binary sensor: ON when team is currently winning."""

    def __init__(self, coordinator, team_id, abbr):
        super().__init__(coordinator)
        self._team_id = team_id
        self._abbr = abbr

    @property
    def unique_id(self) -> str:
        return f"gamesync_{self._team_id}_winning"

    @property
    def name(self) -> str:
        return f"GameSync {self._abbr} Winning"

    @property
    def is_on(self) -> bool:
        if not self.coordinator.data:
            return False
        team = self.coordinator.data.teams.get(self._team_id)
        return team is not None and team.status in ("live", "halftime") and team.is_winning

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._team_id)},
            "name": f"GameSync {self._abbr}",
            "manufacturer": "GameSync",
            "model": "Sports Tracker",
        }
