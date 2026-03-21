"""Pre-game alert checker.

Detects when a followed team's game is about to start and emits a
PREGAME_ALERT GameEvent, deduplicated via the pregame_alerts_sent DB table.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from gamesync.sports.models import Game, GameEvent, GameEventType, GameStatus
from gamesync.storage.models import FollowedTeam

logger = logging.getLogger(__name__)

# Fire the alert if game starts within [threshold ± WINDOW] seconds.
ALERT_WINDOW_SECONDS = 90


class PreGameChecker:
    """Checks upcoming games and emits pre-game alert events."""

    def __init__(self, db: object) -> None:
        # db is a Database instance; typed as object to avoid circular imports.
        self._db = db

    async def check(
        self,
        games: list[Game],
        followed_teams: list[FollowedTeam],
    ) -> list[GameEvent]:
        """Return PREGAME_ALERT events for games within their alert threshold.

        Only games with status SCHEDULED or PREGAME are considered. Each alert
        fires at most once per (game_id, team_id, alert_minutes) triple.
        """
        now = datetime.now(timezone.utc)
        events: list[GameEvent] = []

        for team in followed_teams:
            if not team.pregame_alert_enabled:
                continue

            for game in games:
                if game.status not in (GameStatus.SCHEDULED, GameStatus.PREGAME):
                    continue

                # Determine if this team is playing in this game
                if game.home_team.id == team.team_id:
                    team_name = game.home_team.display_name
                elif game.away_team.id == team.team_id:
                    team_name = game.away_team.display_name
                else:
                    continue

                # Normalise start_time to UTC
                start = game.start_time
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                else:
                    start = start.astimezone(timezone.utc)

                minutes_until = (start - now).total_seconds() / 60
                threshold = team.pregame_alert_minutes
                window = ALERT_WINDOW_SECONDS / 60  # convert to minutes

                if not (threshold - window < minutes_until <= threshold + window):
                    continue

                # Deduplicate via DB
                already_sent = await self._db.has_pregame_alert_been_sent(
                    game.id, team.team_id, threshold
                )
                if already_sent:
                    continue

                await self._db.record_pregame_alert_sent(
                    game.id, team.team_id, threshold
                )

                # Build a deterministic event ID so restarts can't double-log
                stable_key = f"{game.id}:{team.team_id}:pregame:{threshold}"
                event_id = str(uuid.uuid5(uuid.NAMESPACE_OID, stable_key))

                event = GameEvent(
                    id=event_id,
                    game_id=game.id,
                    event_type=GameEventType.PREGAME_ALERT,
                    team_id=team.team_id,
                    team_name=team_name,
                    league=game.league,
                    details={
                        "alert_minutes": threshold,
                        "start_time": start.isoformat(),
                        "home_team": game.home_team.display_name,
                        "away_team": game.away_team.display_name,
                        "venue": game.venue,
                    },
                )
                events.append(event)
                logger.info(
                    "Pre-game alert: %s game in %d min (%s vs %s)",
                    team_name,
                    round(minutes_until),
                    game.home_team.abbreviation,
                    game.away_team.abbreviation,
                )

        return events
