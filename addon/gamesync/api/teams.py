"""Team endpoints — browse, follow, unfollow."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gamesync import main as app_state
from gamesync.sports.models import LeagueId
from gamesync.storage.models import FollowedTeam

router = APIRouter(tags=["teams"])


class FollowRequest(BaseModel):
    team_id: str
    league: str
    delay_seconds: int = 0


class UpdateFollowRequest(BaseModel):
    delay_seconds: int | None = None
    effects_enabled: bool | None = None
    auto_sync_enabled: bool | None = None
    priority_rank: int | None = None
    pregame_alert_enabled: bool | None = None
    pregame_alert_minutes: int | None = None


class TeamEventConfigRequest(BaseModel):
    event_type_id: int
    light_effect_type: str = "flash"
    light_color_hex: str = "#FFFFFF"
    target_light_entities: list[str] = []
    sound_asset_id: int | None = None
    target_media_players: list[str] = []
    fire_ha_event: bool = True
    duration_seconds: float = 5.0


class BulkEventConfigRequest(BaseModel):
    configs: list[TeamEventConfigRequest]


@router.get("/teams")
async def get_all_teams(league: str | None = None, search: str | None = None):
    """Get all available teams, optionally filtered."""
    if not app_state.registry:
        return {"teams": []}

    all_teams = []
    for lid in LeagueId:
        if league and lid.value != league:
            continue
        provider = app_state.registry.get(lid)
        if provider:
            try:
                teams = await provider.get_teams()
                all_teams.extend(teams)
            except Exception:
                pass

    if search:
        search_lower = search.lower()
        all_teams = [
            t for t in all_teams
            if search_lower in t.display_name.lower()
            or search_lower in t.abbreviation.lower()
        ]

    # Group by league
    by_league: dict[str, list] = {}
    for t in all_teams:
        by_league.setdefault(t.league.value, []).append(t.model_dump(mode="json"))

    return {"teams": by_league}


@router.get("/teams/followed")
async def get_followed_teams():
    """Get list of followed teams with config."""
    if not app_state.db:
        return {"teams": []}

    teams = await app_state.db.get_followed_teams()
    return {"teams": [t.model_dump(mode="json") for t in teams]}


@router.post("/teams/follow")
async def follow_team(req: FollowRequest):
    """Follow a team."""
    if not app_state.db or not app_state.scheduler or not app_state.delay_buffer:
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        league = LeagueId(req.league)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid league: {req.league}")

    team = FollowedTeam(
        team_id=req.team_id,
        league=league.value,
        delay_seconds=req.delay_seconds,
    )
    await app_state.db.follow_team(team)

    # Update delay buffer
    app_state.delay_buffer.set_delay(req.team_id, req.delay_seconds)

    # Update scheduler
    followed = await app_state.db.get_followed_teams()
    team_leagues = {t.team_id: t.league for t in followed}
    app_state.scheduler.set_followed_teams(team_leagues)
    app_state.scheduler.set_followed_team_configs(followed)
    await app_state.scheduler.refresh_leagues()

    return {"status": "ok", "team": team.model_dump(mode="json")}


@router.delete("/teams/follow/{team_id:path}")
async def unfollow_team(team_id: str):
    """Unfollow a team."""
    if not app_state.db or not app_state.scheduler:
        raise HTTPException(status_code=503, detail="Service not ready")

    await app_state.db.unfollow_team(team_id)

    # Update scheduler
    followed = await app_state.db.get_followed_teams()
    team_leagues = {t.team_id: t.league for t in followed}
    app_state.scheduler.set_followed_teams(team_leagues)
    app_state.scheduler.set_followed_team_configs(followed)
    await app_state.scheduler.refresh_leagues()

    return {"status": "ok"}


@router.put("/teams/follow/{team_id:path}")
async def update_followed_team(team_id: str, req: UpdateFollowRequest):
    """Update delay or effects_enabled for a followed team."""
    if not app_state.db or not app_state.delay_buffer:
        raise HTTPException(status_code=503, detail="Service not ready")

    updates = {}
    if req.delay_seconds is not None:
        updates["delay_seconds"] = req.delay_seconds
        app_state.delay_buffer.set_delay(team_id, req.delay_seconds)
    if req.effects_enabled is not None:
        updates["effects_enabled"] = req.effects_enabled
    if req.auto_sync_enabled is not None:
        updates["auto_sync_enabled"] = req.auto_sync_enabled
    if req.priority_rank is not None:
        updates["priority_rank"] = req.priority_rank
    if req.pregame_alert_enabled is not None:
        updates["pregame_alert_enabled"] = req.pregame_alert_enabled
    if req.pregame_alert_minutes is not None:
        updates["pregame_alert_minutes"] = req.pregame_alert_minutes

    if updates:
        await app_state.db.update_followed_team(team_id, **updates)

    # Refresh pregame checker configs in the scheduler
    if app_state.scheduler:
        followed = await app_state.db.get_followed_teams()
        app_state.scheduler.set_followed_team_configs(followed)

    return {"status": "ok"}


# ── Team Event Configurations ──────────────────────────────────────


@router.get("/teams/{team_id:path}/events")
async def get_team_event_configs(team_id: str):
    """Get all event configurations for a team."""
    if not app_state.db:
        raise HTTPException(status_code=503, detail="Service not ready")
    configs = await app_state.db.get_team_event_configs(team_id)
    return {"configs": [c.model_dump(mode="json") for c in configs]}


@router.put("/teams/{team_id:path}/events")
async def bulk_update_team_event_configs(team_id: str, body: BulkEventConfigRequest):
    """Bulk update event configurations for a team."""
    if not app_state.db:
        raise HTTPException(status_code=503, detail="Service not ready")

    from gamesync.storage.models import TeamEventConfiguration

    configs = [
        TeamEventConfiguration(
            followed_team_id=team_id,
            event_type_id=c.event_type_id,
            light_effect_type=c.light_effect_type,
            light_color_hex=c.light_color_hex,
            target_light_entities=c.target_light_entities,
            sound_asset_id=c.sound_asset_id,
            target_media_players=c.target_media_players,
            fire_ha_event=c.fire_ha_event,
            duration_seconds=c.duration_seconds,
        )
        for c in body.configs
    ]
    await app_state.db.bulk_upsert_team_event_configs(configs)
    return {"status": "ok", "count": len(configs)}


@router.post("/teams/{team_id:path}/events/copy-from/{source_team_id:path}")
async def copy_team_event_configs(team_id: str, source_team_id: str):
    """Copy all event configurations from one team to another."""
    if not app_state.db:
        raise HTTPException(status_code=503, detail="Service not ready")
    count = await app_state.db.copy_team_event_configs(source_team_id, team_id)
    return {"status": "ok", "copied": count}
