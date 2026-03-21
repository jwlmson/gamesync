"""Shared test fixtures for GameSync test suite."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio

from gamesync.storage.db import Database
from gamesync.storage.models import FollowedTeam, AppConfig
from gamesync.sports.models import (
    Game, GameStatus, LeagueId, SportType, Team, Score,
)


# ── Database fixture ───────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db():
    """In-memory SQLite database, fully initialised with schema v3."""
    database = Database(":memory:")
    await database.initialize()
    # Seed leagues/event types so FK constraints are satisfiable
    from gamesync.storage.seeders import seed_leagues_and_event_types
    await seed_leagues_and_event_types(database)
    yield database
    await database.close()


# ── Team / game factory helpers ────────────────────────────────────────

def make_team(
    team_id: str = "team-home",
    name: str = "Home Team",
    abbreviation: str = "HME",
    display_name: str = "Home Team FC",
    league: LeagueId = LeagueId.NFL,
    sport: SportType = SportType.NFL,
    primary_color: str | None = "#FF0000",
    secondary_color: str | None = "#0000FF",
) -> Team:
    return Team(
        id=team_id,
        name=name,
        abbreviation=abbreviation,
        display_name=display_name,
        logo_url=None,
        primary_color=primary_color,
        secondary_color=secondary_color,
        league=league,
        sport=sport,
    )


def make_game(
    game_id: str = "game-1",
    status: GameStatus = GameStatus.LIVE,
    home_score: int = 0,
    away_score: int = 0,
    period: str | None = None,
    home_team: Team | None = None,
    away_team: Team | None = None,
    league: LeagueId = LeagueId.NFL,
    sport: SportType = SportType.NFL,
    start_time: datetime | None = None,
) -> Game:
    if home_team is None:
        home_team = make_team("team-home", "Home Team", "HME", "Home Team FC", league, sport)
    if away_team is None:
        away_team = make_team("team-away", "Away Team", "AWY", "Away Team FC", league, sport)
    if start_time is None:
        start_time = datetime.now(timezone.utc)
    return Game(
        id=game_id,
        league=league,
        sport=sport,
        home_team=home_team,
        away_team=away_team,
        status=status,
        score=Score(home=home_score, away=away_score, period=period),
        start_time=start_time,
        venue="Stadium",
        broadcast=None,
    )


def make_followed_team(
    team_id: str = "team-home",
    league: str = "nfl",
    pregame_alert_enabled: bool = False,
    pregame_alert_minutes: int = 30,
    effects_enabled: bool = True,
) -> FollowedTeam:
    return FollowedTeam(
        team_id=team_id,
        league=league,
        delay_seconds=0,
        effects_enabled=effects_enabled,
        auto_sync_enabled=False,
        priority_rank=100,
        pregame_alert_enabled=pregame_alert_enabled,
        pregame_alert_minutes=pregame_alert_minutes,
    )
