"""ESPN NFL provider."""

from __future__ import annotations

from datetime import datetime

from gamesync.sports.base import SportProvider
from gamesync.sports.espn import ESPNClient, parse_espn_game, parse_espn_team
from gamesync.sports.models import (
    Game,
    GameEvent,
    GameEventType,
    LeagueId,
    SportType,
    Team,
)


class ESPNNFLProvider(SportProvider):
    SPORT_PATH = "football/nfl"
    LEAGUE = LeagueId.NFL
    SPORT = SportType.NFL

    def __init__(self, client: ESPNClient) -> None:
        self._client = client

    @property
    def league_id(self) -> LeagueId:
        return self.LEAGUE

    async def get_teams(self) -> list[Team]:
        data = await self._client.get_teams_list(self.SPORT_PATH)
        teams = []
        for group in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
            teams.append(parse_espn_team(group, self.LEAGUE, self.SPORT))
        return teams

    async def get_schedule(
        self, team_id: str, start: datetime, end: datetime
    ) -> list[Game]:
        # ESPN scoreboard is date-based; iterate days
        games = []
        current = start
        while current <= end:
            scoreboard = await self.get_scoreboard(current)
            for game in scoreboard:
                if game.home_team.id == team_id or game.away_team.id == team_id:
                    games.append(game)
            current = current.replace(day=current.day + 1)
        return games

    async def get_live_games(self, team_ids: list[str] | None = None) -> list[Game]:
        all_games = await self.get_scoreboard()
        live = [g for g in all_games if g.status.value in ("live", "halftime")]
        if team_ids:
            live = [
                g for g in live
                if g.home_team.id in team_ids or g.away_team.id in team_ids
            ]
        return live

    async def get_scoreboard(self, date: datetime | None = None) -> list[Game]:
        data = await self._client.get_scoreboard(self.SPORT_PATH, date)
        events = data.get("events", [])
        return [parse_espn_game(e, self.LEAGUE, self.SPORT) for e in events]

    def detect_events(self, old: Game, new: Game) -> list[GameEvent]:
        """NFL-specific event detection including red zone."""
        from uuid import uuid4

        events = super().detect_events(old, new)

        # Red zone detection from situation data (if available in details)
        # ESPN sometimes provides situation data in competition details
        # For now, we detect based on score changes typical of NFL
        # (touchdowns = 6-7 point jumps, field goals = 3)
        if old.score and new.score:
            for side, team in [("home", new.home_team), ("away", new.away_team)]:
                old_pts = old.score.home if side == "home" else old.score.away
                new_pts = new.score.home if side == "home" else new.score.away
                diff = new_pts - old_pts
                if diff > 0:
                    # Enrich existing score_change events with NFL-specific detail
                    scoring_type = "unknown"
                    if diff >= 6:
                        scoring_type = "touchdown"
                    elif diff == 3:
                        scoring_type = "field_goal"
                    elif diff == 2:
                        scoring_type = "safety_or_conversion"
                    elif diff == 1:
                        scoring_type = "extra_point"

                    # Find the matching score_change event and add detail
                    for evt in events:
                        if (
                            evt.event_type == GameEventType.SCORE_CHANGE
                            and evt.team_id == team.id
                        ):
                            evt.details = evt.details or {}
                            evt.details["scoring_type"] = scoring_type

        return events
