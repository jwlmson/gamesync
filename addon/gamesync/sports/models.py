"""Core domain models for sports data."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SportType(str, Enum):
    NFL = "nfl"
    NBA = "nba"
    NHL = "nhl"
    MLB = "mlb"
    SOCCER = "soccer"
    F1 = "f1"


class LeagueId(str, Enum):
    NFL = "nfl"
    NBA = "nba"
    NHL = "nhl"
    MLB = "mlb"
    EPL = "eng.1"
    MLS = "usa.1"
    CHAMPIONS_LEAGUE = "uefa.champions"
    LA_LIGA = "esp.1"
    BUNDESLIGA = "ger.1"
    F1 = "f1"


# Map league to sport type
LEAGUE_SPORT_MAP: dict[LeagueId, SportType] = {
    LeagueId.NFL: SportType.NFL,
    LeagueId.NBA: SportType.NBA,
    LeagueId.NHL: SportType.NHL,
    LeagueId.MLB: SportType.MLB,
    LeagueId.EPL: SportType.SOCCER,
    LeagueId.MLS: SportType.SOCCER,
    LeagueId.CHAMPIONS_LEAGUE: SportType.SOCCER,
    LeagueId.LA_LIGA: SportType.SOCCER,
    LeagueId.BUNDESLIGA: SportType.SOCCER,
    LeagueId.F1: SportType.F1,
}

# Map league to ESPN sport path
LEAGUE_ESPN_PATH: dict[LeagueId, str] = {
    LeagueId.NFL: "football/nfl",
    LeagueId.NBA: "basketball/nba",
    LeagueId.NHL: "hockey/nhl",
    LeagueId.MLB: "baseball/mlb",
    LeagueId.EPL: "soccer/eng.1",
    LeagueId.MLS: "soccer/usa.1",
    LeagueId.CHAMPIONS_LEAGUE: "soccer/uefa.champions",
    LeagueId.LA_LIGA: "soccer/esp.1",
    LeagueId.BUNDESLIGA: "soccer/ger.1",
}


class GameStatus(str, Enum):
    SCHEDULED = "scheduled"
    PREGAME = "pregame"
    LIVE = "live"
    HALFTIME = "halftime"
    FINAL = "final"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class GameEventType(str, Enum):
    SCORE_CHANGE = "score_change"
    GAME_START = "game_start"
    GAME_END = "game_end"
    PERIOD_START = "period_start"
    PERIOD_END = "period_end"
    HALFTIME = "halftime"
    RED_ZONE = "red_zone"
    POWER_PLAY = "power_play"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    SAFETY_CAR = "safety_car"
    POSITION_CHANGE = "position_change"
    PREGAME_ALERT = "pregame_alert"


class Team(BaseModel):
    id: str
    name: str
    abbreviation: str
    display_name: str
    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    league: LeagueId
    sport: SportType


class Score(BaseModel):
    home: int = 0
    away: int = 0
    period_scores: list[dict] | None = None
    clock: str | None = None
    period: str | None = None
    period_number: int | None = None


class Game(BaseModel):
    id: str
    league: LeagueId
    sport: SportType
    home_team: Team
    away_team: Team
    status: GameStatus
    score: Score | None = None
    start_time: datetime
    venue: str | None = None
    broadcast: str | None = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class GameEvent(BaseModel):
    id: str
    game_id: str
    event_type: GameEventType
    team_id: str | None = None
    team_name: str | None = None
    league: LeagueId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    old_score: Score | None = None
    new_score: Score | None = None
    details: dict | None = None
