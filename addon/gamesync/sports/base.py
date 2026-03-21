"""Abstract base class for sport data providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from gamesync.sports.models import Game, GameEvent, LeagueId, Team


class SportProvider(ABC):
    """Base class all sport providers must implement."""

    @property
    @abstractmethod
    def league_id(self) -> LeagueId:
        """The league this provider handles."""

    @abstractmethod
    async def get_teams(self) -> list[Team]:
        """Return all teams in this league."""

    @abstractmethod
    async def get_schedule(
        self, team_id: str, start: datetime, end: datetime
    ) -> list[Game]:
        """Return scheduled games for a team in a date range."""

    @abstractmethod
    async def get_live_games(self, team_ids: list[str] | None = None) -> list[Game]:
        """Return currently live games, optionally filtered to specific teams."""

    @abstractmethod
    async def get_scoreboard(self, date: datetime | None = None) -> list[Game]:
        """Return all games on the scoreboard for a given date (default today)."""

    def detect_events(self, old: Game, new: Game) -> list[GameEvent]:
        """Compare two snapshots of the same game and detect events.

        Default implementation handles score changes, status transitions.
        Subclasses can override for sport-specific events.
        """
        from uuid import uuid4
        from gamesync.sports.models import GameEventType, GameStatus

        events: list[GameEvent] = []

        # Status transitions
        if old.status != new.status:

            if new.status == GameStatus.LIVE and old.status in (
                GameStatus.SCHEDULED,
                GameStatus.PREGAME,
            ):
                events.append(
                    GameEvent(
                        id=str(uuid4()),
                        game_id=new.id,
                        event_type=GameEventType.GAME_START,
                        league=new.league,
                        details={
                            "home_team": new.home_team.display_name,
                            "away_team": new.away_team.display_name,
                        },
                    )
                )
            elif new.status == GameStatus.HALFTIME:
                events.append(
                    GameEvent(
                        id=str(uuid4()),
                        game_id=new.id,
                        event_type=GameEventType.HALFTIME,
                        league=new.league,
                    )
                )
            elif new.status == GameStatus.FINAL:
                # Determine winner
                result = "draw"
                winner_id = None
                if new.score:
                    if new.score.home > new.score.away:
                        result = "home_win"
                        winner_id = new.home_team.id
                    elif new.score.away > new.score.home:
                        result = "away_win"
                        winner_id = new.away_team.id

                events.append(
                    GameEvent(
                        id=str(uuid4()),
                        game_id=new.id,
                        event_type=GameEventType.GAME_END,
                        team_id=winner_id,
                        league=new.league,
                        new_score=new.score,
                        details={"result": result},
                    )
                )

        # Score changes
        if old.score and new.score:
            if new.score.home > old.score.home:
                events.append(
                    GameEvent(
                        id=str(uuid4()),
                        game_id=new.id,
                        event_type=GameEventType.SCORE_CHANGE,
                        team_id=new.home_team.id,
                        team_name=new.home_team.display_name,
                        league=new.league,
                        old_score=old.score,
                        new_score=new.score,
                        details={
                            "scoring_team": "home",
                            "points_scored": new.score.home - old.score.home,
                        },
                    )
                )
            if new.score.away > old.score.away:
                events.append(
                    GameEvent(
                        id=str(uuid4()),
                        game_id=new.id,
                        event_type=GameEventType.SCORE_CHANGE,
                        team_id=new.away_team.id,
                        team_name=new.away_team.display_name,
                        league=new.league,
                        old_score=old.score,
                        new_score=new.score,
                        details={
                            "scoring_team": "away",
                            "points_scored": new.score.away - old.score.away,
                        },
                    )
                )

            # Period changes
            if new.score.period != old.score.period and new.score.period:
                events.append(
                    GameEvent(
                        id=str(uuid4()),
                        game_id=new.id,
                        event_type=GameEventType.PERIOD_START,
                        league=new.league,
                        details={"period": new.score.period},
                    )
                )

        return events
