"""ESPN Soccer provider — handles multiple soccer leagues."""

from __future__ import annotations

from datetime import datetime

from gamesync.sports.base import SportProvider
from gamesync.sports.espn import ESPNClient, parse_espn_game, parse_espn_team
from gamesync.sports.models import (
    Game,
    GameEvent,
    GameEventType,
    LeagueId,
    LEAGUE_ESPN_PATH,
    SportType,
    Team,
)


class ESPNSoccerProvider(SportProvider):
    """Provider for a specific soccer league via ESPN."""

    SPORT = SportType.SOCCER

    def __init__(self, client: ESPNClient, league: LeagueId) -> None:
        self._client = client
        self._league = league
        self._sport_path = LEAGUE_ESPN_PATH[league]

    @property
    def league_id(self) -> LeagueId:
        return self._league

    async def get_teams(self) -> list[Team]:
        data = await self._client.get_teams_list(self._sport_path)
        teams = []
        for group in data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", []):
            teams.append(parse_espn_team(group, self._league, self.SPORT))
        return teams

    async def get_schedule(self, team_id: str, start: datetime, end: datetime) -> list[Game]:
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
            live = [g for g in live if g.home_team.id in team_ids or g.away_team.id in team_ids]
        return live

    async def get_scoreboard(self, date: datetime | None = None) -> list[Game]:
        data = await self._client.get_scoreboard(self._sport_path, date)
        return [parse_espn_game(e, self._league, self.SPORT) for e in data.get("events", [])]

    def detect_events(self, old: Game, new: Game) -> list[GameEvent]:
        events = super().detect_events(old, new)

        # Enrich soccer score changes as goals
        for evt in events:
            if evt.event_type == GameEventType.SCORE_CHANGE:
                evt.details = evt.details or {}
                evt.details["scoring_type"] = "goal"

        return events
