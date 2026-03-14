"""Game endpoints — scoreboard, live games, calendar."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query

from gamesync import main as app_state
from gamesync.sports.models import LeagueId

router = APIRouter(tags=["games"])


@router.get("/games")
async def get_games(
    date: str | None = Query(None, description="Date in YYYY-MM-DD format"),
    league: str | None = Query(None, description="Filter by league"),
):
    """Get all games for followed teams."""
    if not app_state.registry or not app_state.db:
        return {"games": []}

    followed = await app_state.db.get_followed_teams()
    if not followed:
        return {"games": []}

    target_date = None
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    all_games = []
    leagues_to_check = set()
    for t in followed:
        if league and t.league.value != league:
            continue
        leagues_to_check.add(t.league)

    for lid in leagues_to_check:
        provider = app_state.registry.get(lid)
        if provider:
            try:
                games = await provider.get_scoreboard(target_date)
                team_ids = {t.team_id for t in followed if t.league == lid}
                relevant = [
                    g for g in games
                    if g.home_team.id in team_ids or g.away_team.id in team_ids
                ]
                all_games.extend(relevant)
            except Exception:
                pass

    return {"games": [g.model_dump(mode="json") for g in all_games]}


@router.get("/games/live")
async def get_live_games():
    """Get currently live games for followed teams."""
    if not app_state.scheduler:
        return {"games": []}

    snapshots = app_state.scheduler.poller.get_all_snapshots()
    live = [
        g for g in snapshots.values()
        if g.status.value in ("live", "halftime")
    ]
    return {"games": [g.model_dump(mode="json") for g in live]}


@router.get("/games/all")
async def get_all_games(
    date: str | None = Query(None),
    league: str | None = Query(None),
):
    """Get all games (not just followed teams) for browsing."""
    if not app_state.registry:
        return {"games": []}

    target_date = None
    if date:
        target_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    all_games = []
    for lid in LeagueId:
        if league and lid.value != league:
            continue
        provider = app_state.registry.get(lid)
        if provider:
            try:
                games = await provider.get_scoreboard(target_date)
                all_games.extend(games)
            except Exception:
                pass

    return {"games": [g.model_dump(mode="json") for g in all_games]}


@router.get("/games/calendar")
async def get_calendar(days: int = Query(30, ge=1, le=90)):
    """Get upcoming games grouped by date."""
    if not app_state.registry or not app_state.db:
        return {"calendar": {}}

    followed = await app_state.db.get_followed_teams()
    if not followed:
        return {"calendar": {}}

    calendar: dict[str, list] = {}
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Check each day
    for day_offset in range(days):
        target = today + timedelta(days=day_offset)
        date_str = target.strftime("%Y-%m-%d")
        day_games = []

        for lid in set(t.league for t in followed):
            provider = app_state.registry.get(lid)
            if provider:
                try:
                    games = await provider.get_scoreboard(target)
                    team_ids = {t.team_id for t in followed if t.league == lid}
                    relevant = [
                        g for g in games
                        if g.home_team.id in team_ids or g.away_team.id in team_ids
                    ]
                    day_games.extend(relevant)
                except Exception:
                    pass

        if day_games:
            calendar[date_str] = [g.model_dump(mode="json") for g in day_games]

    return {"calendar": calendar}
