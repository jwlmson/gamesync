"""Sensor entities for GameSync — score, game state, next game."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
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
    """Set up GameSync sensors from a config entry."""
    coordinator: GameSyncCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get followed teams from the add-on to know which entities to create
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
            GameSyncScoreSensor(coordinator, team_id, abbr),
            GameSyncStateSensor(coordinator, team_id, abbr),
        ])

    async_add_entities(entities)


class GameSyncBaseSensor(CoordinatorEntity[GameSyncCoordinator], SensorEntity):
    """Base class for GameSync sensors."""

    def __init__(
        self, coordinator: GameSyncCoordinator, team_id: str, abbr: str
    ) -> None:
        super().__init__(coordinator)
        self._team_id = team_id
        self._abbr = abbr

    @property
    def _team_data(self) -> TeamScore | None:
        if self.coordinator.data:
            return self.coordinator.data.teams.get(self._team_id)
        return None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._team_id)},
            "name": f"GameSync {self._abbr}",
            "manufacturer": "GameSync",
            "model": "Sports Tracker",
        }


class GameSyncScoreSensor(GameSyncBaseSensor):
    """Sensor showing current score as 'home - away'."""

    @property
    def unique_id(self) -> str:
        return f"gamesync_{self._team_id}_score"

    @property
    def name(self) -> str:
        return f"GameSync {self._abbr} Score"

    @property
    def native_value(self) -> str:
        team = self._team_data
        if team:
            return team.score_display
        return "--"

    @property
    def extra_state_attributes(self) -> dict:
        team = self._team_data
        if not team:
            return {}
        return {
            "home_score": team.home_score,
            "away_score": team.away_score,
            "my_score": team.my_score,
            "opponent_score": team.opp_score,
            "period": team.period,
            "clock": team.clock,
            "game_id": team.game_id,
            "opponent": team.opponent,
            "venue": team.venue,
            "broadcast": team.broadcast,
        }


class GameSyncStateSensor(GameSyncBaseSensor):
    """Sensor showing game state: scheduled/live/halftime/final/off."""

    @property
    def unique_id(self) -> str:
        return f"gamesync_{self._team_id}_state"

    @property
    def name(self) -> str:
        return f"GameSync {self._abbr} Game State"

    @property
    def native_value(self) -> str:
        team = self._team_data
        if team:
            return team.status
        return "off"

    @property
    def extra_state_attributes(self) -> dict:
        team = self._team_data
        if not team:
            return {}
        return {
            "team_id": team.team_id,
            "league": team.league,
            "sport": team.sport,
            "opponent": team.opponent,
            "is_home": team.is_home,
            "start_time": team.start_time.isoformat() if team.start_time else None,
        }
