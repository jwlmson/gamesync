"""OpenF1 provider for Formula 1 live timing."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from gamesync.sports.base import SportProvider
from gamesync.sports.models import (
    Game,
    GameEvent,
    GameEventType,
    GameStatus,
    LeagueId,
    Score,
    SportType,
    Team,
)

logger = logging.getLogger(__name__)

OPENF1_BASE = "https://api.openf1.org/v1"

# F1 constructor team colors (2024-2025)
F1_TEAM_COLORS: dict[str, tuple[str, str]] = {
    "Red Bull Racing": ("#3671C6", "#FFD700"),
    "Ferrari": ("#E8002D", "#FFEB00"),
    "Mercedes": ("#27F4D2", "#000000"),
    "McLaren": ("#FF8000", "#000000"),
    "Aston Martin": ("#229971", "#CEDC00"),
    "Alpine": ("#FF87BC", "#0093CC"),
    "Williams": ("#64C4FF", "#041E42"),
    "RB": ("#6692FF", "#FFFFFF"),
    "Kick Sauber": ("#52E252", "#000000"),
    "Haas F1 Team": ("#B6BABD", "#E6002D"),
}


class OpenF1Provider(SportProvider):
    """Formula 1 data via OpenF1 API."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=OPENF1_BASE,
            timeout=15.0,
            headers={"User-Agent": "GameSync/0.1"},
        )
        self._drivers_cache: dict[int, list[dict]] = {}
        self._last_positions: dict[int, dict[int, int]] = {}  # session_key -> {driver_number: position}

    async def close(self) -> None:
        await self._client.aclose()

    @property
    def league_id(self) -> LeagueId:
        return LeagueId.F1

    async def get_teams(self) -> list[Team]:
        """Return F1 constructor teams."""
        teams = []
        for name, (primary, secondary) in F1_TEAM_COLORS.items():
            teams.append(
                Team(
                    id=f"f1:{name.lower().replace(' ', '_')}",
                    name=name,
                    abbreviation=name[:3].upper(),
                    display_name=name,
                    primary_color=primary,
                    secondary_color=secondary,
                    league=LeagueId.F1,
                    sport=SportType.F1,
                )
            )
        return teams

    async def get_schedule(
        self, team_id: str, start: datetime, end: datetime
    ) -> list[Game]:
        """Get F1 session schedule."""
        resp = await self._client.get(
            "/sessions",
            params={"year": start.year},
        )
        resp.raise_for_status()
        sessions = resp.json()

        games = []
        for s in sessions:
            session_start = datetime.fromisoformat(s["date_start"].replace("Z", "+00:00"))
            if start <= session_start <= end and s.get("session_type") == "Race":
                games.append(self._session_to_game(s))
        return games

    async def get_live_games(self, team_ids: list[str] | None = None) -> list[Game]:
        """Check for live F1 sessions."""
        games = await self.get_scoreboard()
        return [g for g in games if g.status == GameStatus.LIVE]

    async def get_scoreboard(self, date: datetime | None = None) -> list[Game]:
        """Get current/recent F1 sessions."""
        params: dict = {}
        if date:
            params["date_start>"] = date.strftime("%Y-%m-%dT00:00:00")
            params["date_start<"] = date.strftime("%Y-%m-%dT23:59:59")

        resp = await self._client.get("/sessions", params=params)
        resp.raise_for_status()
        sessions = resp.json()

        games = []
        for s in sessions:
            if s.get("session_type") in ("Race", "Sprint", "Qualifying", "Practice"):
                games.append(self._session_to_game(s))
        return games

    def _session_to_game(self, session: dict) -> Game:
        """Convert an OpenF1 session to a Game object."""
        session_start = datetime.fromisoformat(
            session["date_start"].replace("Z", "+00:00")
        )
        session_end = (
            datetime.fromisoformat(session["date_end"].replace("Z", "+00:00"))
            if session.get("date_end")
            else None
        )

        now = datetime.now(timezone.utc)
        if session_end and now > session_end:
            status = GameStatus.FINAL
        elif now >= session_start:
            status = GameStatus.LIVE
        else:
            status = GameStatus.SCHEDULED

        # F1 uses a special representation — home_team is "F1" itself
        f1_team = Team(
            id="f1:formula1",
            name="Formula 1",
            abbreviation="F1",
            display_name=f"F1 {session.get('session_type', 'Session')}",
            league=LeagueId.F1,
            sport=SportType.F1,
        )

        return Game(
            id=f"f1:{session['session_key']}",
            league=LeagueId.F1,
            sport=SportType.F1,
            home_team=f1_team,
            away_team=f1_team,
            status=status,
            score=Score(
                home=0,
                away=0,
                period=session.get("session_type"),
                clock=session.get("circuit_short_name"),
            ),
            start_time=session_start,
            venue=session.get("circuit_short_name"),
            last_updated=datetime.now(timezone.utc),
        )

    async def get_race_control(self, session_key: int) -> list[dict]:
        """Fetch race control messages (flags, safety car, etc.)."""
        resp = await self._client.get(
            "/race_control",
            params={"session_key": session_key},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_positions(self, session_key: int) -> list[dict]:
        """Fetch position data for a session."""
        resp = await self._client.get(
            "/position",
            params={"session_key": session_key},
        )
        resp.raise_for_status()
        return resp.json()

    def detect_events(self, old: Game, new: Game) -> list[GameEvent]:
        """F1-specific event detection — safety car, flags."""
        events = super().detect_events(old, new)
        # F1-specific events would be detected via race_control polling
        # in the scheduler, not game-to-game diff
        return events

    def detect_race_control_events(
        self, messages: list[dict], last_seen_index: int
    ) -> tuple[list[GameEvent], int]:
        """Detect events from race control messages."""
        events: list[GameEvent] = []
        new_index = last_seen_index

        for i, msg in enumerate(messages):
            if i <= last_seen_index:
                continue
            new_index = i

            category = msg.get("category", "").upper()
            flag = msg.get("flag", "").upper() if msg.get("flag") else None
            message = msg.get("message", "")

            if category == "SAFETYCAR" or "SAFETY CAR" in message.upper():
                events.append(
                    GameEvent(
                        id=str(uuid4()),
                        game_id="f1:live",
                        event_type=GameEventType.SAFETY_CAR,
                        league=LeagueId.F1,
                        details={"message": message, "flag": flag},
                    )
                )
            elif category == "FLAG":
                if flag == "YELLOW":
                    events.append(
                        GameEvent(
                            id=str(uuid4()),
                            game_id="f1:live",
                            event_type=GameEventType.YELLOW_FLAG,
                            league=LeagueId.F1,
                            details={"message": message, "flag": flag},
                        )
                    )
                elif flag == "RED":
                    events.append(
                        GameEvent(
                            id=str(uuid4()),
                            game_id="f1:live",
                            event_type=GameEventType.RED_FLAG,
                            league=LeagueId.F1,
                            details={"message": message, "flag": flag},
                        )
                    )

        return events, new_index
