"""DataUpdateCoordinator — polls the GameSync add-on REST API."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_ADDON_HOST,
    CONF_ADDON_PORT,
    DEFAULT_ADDON_HOST,
    DEFAULT_ADDON_PORT,
    DOMAIN,
    EVENT_GAME_END,
    EVENT_GAME_START,
    EVENT_MUTE_CHANGED,
    EVENT_PERIOD_CHANGE,
    EVENT_SCORE,
    EVENT_SESSION_CHANGED,
    EVENT_SPECIAL,
    UPDATE_INTERVAL,
)
from .models import GamesyncData, TeamScore

_LOGGER = logging.getLogger(__name__)

_GAMESYNC_TO_HA_EVENT: dict[str, str] = {
    "score_change": EVENT_SCORE,
    "game_start": EVENT_GAME_START,
    "game_end": EVENT_GAME_END,
    "period_start": EVENT_PERIOD_CHANGE,
    "period_end": EVENT_PERIOD_CHANGE,
    "halftime": EVENT_PERIOD_CHANGE,
    "red_zone": EVENT_SPECIAL,
    "power_play": EVENT_SPECIAL,
    "yellow_card": EVENT_SPECIAL,
    "red_card": EVENT_SPECIAL,
    "safety_car": EVENT_SPECIAL,
    "position_change": EVENT_SPECIAL,
}


class GameSyncCoordinator(DataUpdateCoordinator[GamesyncData]):
    """Polls the GameSync add-on and distributes data to entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self._entry = entry
        host = entry.data.get(CONF_ADDON_HOST, DEFAULT_ADDON_HOST)
        port = entry.data.get(CONF_ADDON_PORT, DEFAULT_ADDON_PORT)
        self._base_url = f"http://{host}:{port}/api"
        self._session: aiohttp.ClientSession | None = None
        self._last_event_ids: set[str] = set()

    @property
    def base_url(self) -> str:
        return self._base_url

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _fetch(self, path: str) -> dict:
        session = await self._get_session()
        url = f"{self._base_url}{path}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _async_update_data(self) -> GamesyncData:
        """Fetch data from add-on and fire HA events for new GameEvents."""
        try:
            results = await asyncio.gather(
                self._fetch("/games/live"),
                self._fetch("/teams/followed"),
                self._fetch("/events/history?limit=50"),
                self._fetch("/sessions"),
                self._fetch("/config"),
                return_exceptions=True,
            )
        except Exception as err:
            raise UpdateFailed(f"Cannot connect to GameSync add-on: {err}") from err

        live_data, followed_data, history_data, sessions_data, config_data = results
        data = GamesyncData()

        if not isinstance(followed_data, Exception) and not isinstance(live_data, Exception):
            data.raw_live_games = live_data.get("games", [])
            followed_teams = {t["team_id"]: t for t in followed_data.get("teams", [])}
            for game in data.raw_live_games:
                self._process_game(game, followed_teams, data)

        if not isinstance(sessions_data, Exception):
            data.active_sessions = sessions_data if isinstance(sessions_data, list) else []
            data.primary_session = next(
                (s for s in data.active_sessions if s.get("is_primary")), None
            )

        if not isinstance(config_data, Exception):
            data.global_mute = config_data.get("global_mute", False)

        if not isinstance(history_data, Exception):
            self._fire_new_events(history_data.get("events", []))

        return data

    def _process_game(
        self, game: dict, followed_teams: dict, data: GamesyncData
    ) -> None:
        home = game.get("home_team", {})
        away = game.get("away_team", {})
        score = game.get("score", {}) or {}

        for team_data, is_home, opp_data in [
            (home, True, away),
            (away, False, home),
        ]:
            tid = team_data.get("id", "")
            if tid not in followed_teams:
                continue

            ts = TeamScore(
                team_id=tid,
                team_name=team_data.get("display_name", tid),
                abbreviation=team_data.get("abbreviation", ""),
                league=game.get("league", ""),
                sport=game.get("sport", ""),
                game_id=game.get("id", ""),
                status=game.get("status", "scheduled"),
                home_score=score.get("home", 0),
                away_score=score.get("away", 0),
                is_home=is_home,
                period=score.get("period"),
                clock=score.get("clock"),
                opponent=opp_data.get("display_name"),
                opponent_id=opp_data.get("id"),
                venue=game.get("venue"),
                broadcast=game.get("broadcast"),
            )
            data.teams[tid] = ts

    def _fire_new_events(self, events: list[dict]) -> None:
        for event in events:
            eid = event.get("id", "")
            if eid in self._last_event_ids:
                continue
            self._last_event_ids.add(eid)

            event_type_str = event.get("event_type", "")
            ha_event = _GAMESYNC_TO_HA_EVENT.get(event_type_str)
            if ha_event:
                self.hass.bus.async_fire(ha_event, event)

        # Prevent unbounded growth
        if len(self._last_event_ids) > 1000:
            self._last_event_ids = set(list(self._last_event_ids)[-500:])

    async def async_shutdown(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
