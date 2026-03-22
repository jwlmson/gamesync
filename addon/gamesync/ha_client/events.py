"""Fire events on the HA event bus."""

from __future__ import annotations

import logging

from gamesync.ha_client.client import HAClient
from gamesync.sports.models import GameEvent, GameEventType

logger = logging.getLogger(__name__)

# Map our event types to HA event names
EVENT_TYPE_MAP: dict[GameEventType, str] = {
    GameEventType.SCORE_CHANGE: "gamesync_score",
    GameEventType.GAME_START: "gamesync_game_start",
    GameEventType.GAME_END: "gamesync_game_end",
    GameEventType.PERIOD_START: "gamesync_period_change",
    GameEventType.PERIOD_END: "gamesync_period_change",
    GameEventType.HALFTIME: "gamesync_period_change",
    GameEventType.RED_ZONE: "gamesync_special",
    GameEventType.POWER_PLAY: "gamesync_special",
    GameEventType.YELLOW_CARD: "gamesync_special",
    GameEventType.RED_CARD: "gamesync_special",
    GameEventType.SAFETY_CAR: "gamesync_special",
    GameEventType.YELLOW_FLAG: "gamesync_special",
    GameEventType.RED_FLAG: "gamesync_special",
    GameEventType.POSITION_CHANGE: "gamesync_special",
    GameEventType.PREGAME_ALERT: "gamesync_pregame",
}


class HAEventFirer:
    """Publishes GameEvents to the HA event bus."""

    def __init__(self, client: HAClient) -> None:
        self._client = client

    async def fire(self, event: GameEvent) -> None:
        """Fire a GameEvent as an HA event."""
        ha_event_name = EVENT_TYPE_MAP.get(event.event_type, "gamesync_special")

        data = {
            "event_type": event.event_type.value,
            "game_id": event.game_id,
            "league": event.league.value,
            "timestamp": event.timestamp.isoformat(),
        }

        if event.team_id:
            data["team_id"] = event.team_id
        if event.team_name:
            data["team_name"] = event.team_name
        if event.new_score:
            data["home_score"] = event.new_score.home
            data["away_score"] = event.new_score.away
        if event.details:
            data.update(event.details)

        try:
            await self._client.fire_event(ha_event_name, data)
        except Exception:
            logger.exception("Failed to fire HA event: %s", ha_event_name)
