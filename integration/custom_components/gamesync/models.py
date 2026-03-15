"""Data models mapping the add-on REST API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TeamScore:
    team_id: str
    team_name: str
    abbreviation: str
    league: str
    sport: str
    game_id: str
    status: str  # scheduled / live / halftime / final / off
    home_score: int = 0
    away_score: int = 0
    is_home: bool = False
    period: str | None = None
    clock: str | None = None
    opponent: str | None = None
    opponent_id: str | None = None
    start_time: datetime | None = None
    venue: str | None = None
    broadcast: str | None = None
    next_game_time: datetime | None = None
    next_game_opponent: str | None = None

    @property
    def my_score(self) -> int:
        return self.home_score if self.is_home else self.away_score

    @property
    def opp_score(self) -> int:
        return self.away_score if self.is_home else self.home_score

    @property
    def is_winning(self) -> bool:
        return self.my_score > self.opp_score

    @property
    def score_display(self) -> str:
        if self.status in ("live", "halftime", "final"):
            return f"{self.home_score} - {self.away_score}"
        return "--"


@dataclass
class GamesyncData:
    """All data fetched from the add-on, keyed by team_id."""
    teams: dict[str, TeamScore] = field(default_factory=dict)
    raw_live_games: list[dict] = field(default_factory=list)
    scheduler_status: dict = field(default_factory=dict)
    active_sessions: list[dict] = field(default_factory=list)
    primary_session: dict | None = None
    global_mute: bool = False
