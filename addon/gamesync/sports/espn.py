"""ESPN API client — shared logic for all ESPN-backed sport providers."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from gamesync.sports.models import (
    Game,
    GameStatus,
    LeagueId,
    Score,
    SportType,
    Team,
)

logger = logging.getLogger(__name__)

ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

# Map ESPN status type.state to our GameStatus
ESPN_STATUS_MAP: dict[str, GameStatus] = {
    "pre": GameStatus.SCHEDULED,
    "in": GameStatus.LIVE,
    "post": GameStatus.FINAL,
    "postponed": GameStatus.POSTPONED,
    "cancelled": GameStatus.CANCELLED,
}


class ESPNClient:
    """Shared HTTP client for ESPN API requests."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=ESPN_BASE_URL,
            timeout=15.0,
            headers={"User-Agent": "GameSync/0.1"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_scoreboard(
        self,
        sport_path: str,
        date: datetime | None = None,
    ) -> dict:
        """Fetch the scoreboard for a given sport/league path."""
        params = {}
        if date:
            params["dates"] = date.strftime("%Y%m%d")

        url = f"/{sport_path}/scoreboard"
        logger.debug("ESPN request: %s params=%s", url, params)

        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_teams_list(self, sport_path: str) -> dict:
        """Fetch team list for a sport/league."""
        url = f"/{sport_path}/teams"
        params = {"limit": 200}
        resp = await self._client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def parse_espn_team(team_data: dict, league: LeagueId, sport: SportType) -> Team:
    """Parse an ESPN team object into our Team model."""
    team = team_data.get("team", team_data)
    return Team(
        id=f"{league.value}:{team['id']}",
        name=team.get("name", ""),
        abbreviation=team.get("abbreviation", ""),
        display_name=team.get("displayName", team.get("name", "")),
        logo_url=team.get("logo", team.get("logos", [{}])[0].get("href") if team.get("logos") else None),
        primary_color=f"#{team['color']}" if team.get("color") else None,
        secondary_color=f"#{team['alternateColor']}" if team.get("alternateColor") else None,
        league=league,
        sport=sport,
    )


def parse_espn_game(event: dict, league: LeagueId, sport: SportType) -> Game:
    """Parse an ESPN scoreboard event into our Game model."""
    competition = event["competitions"][0]
    competitors = competition["competitors"]

    # ESPN lists home team first sometimes, away first others — check the flag
    home_data = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
    away_data = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

    home_team = parse_espn_team(home_data, league, sport)
    away_team = parse_espn_team(away_data, league, sport)

    # Status
    status_obj = event.get("status", {})
    status_type = status_obj.get("type", {})
    state = status_type.get("state", "pre")
    status = ESPN_STATUS_MAP.get(state, GameStatus.SCHEDULED)

    # Check for halftime
    if state == "in":
        detail = status_type.get("detail", "").lower()
        if "halftime" in detail or "half" in detail:
            status = GameStatus.HALFTIME

    # Score
    home_score = int(home_data.get("score", "0") or "0")
    away_score = int(away_data.get("score", "0") or "0")

    # Period info from status
    period = status_type.get("detail", None)
    period_number = status_obj.get("period", None)
    clock = status_obj.get("displayClock", None)

    # Period scores from linescores
    period_scores = None
    home_linescores = home_data.get("linescores", [])
    away_linescores = away_data.get("linescores", [])
    if home_linescores:
        period_scores = [
            {
                "period": i + 1,
                "home": int(h.get("value", 0)),
                "away": int(a.get("value", 0)) if i < len(away_linescores) else 0,
            }
            for i, (h, a) in enumerate(
                zip(home_linescores, away_linescores)
            )
        ]

    score = Score(
        home=home_score,
        away=away_score,
        period_scores=period_scores,
        clock=clock,
        period=period,
        period_number=period_number,
    )

    # Venue
    venue = competition.get("venue", {}).get("fullName")

    # Broadcast
    broadcasts = competition.get("broadcasts", [])
    broadcast = None
    if broadcasts:
        names = broadcasts[0].get("names", [])
        if names:
            broadcast = names[0]

    # Start time
    start_time = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))

    return Game(
        id=f"{league.value}:{event['id']}",
        league=league,
        sport=sport,
        home_team=home_team,
        away_team=away_team,
        status=status,
        score=score,
        start_time=start_time,
        venue=venue,
        broadcast=broadcast,
        last_updated=datetime.now(timezone.utc),
    )
