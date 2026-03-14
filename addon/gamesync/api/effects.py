"""Effect endpoints — trigger, configure, list presets."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gamesync import main as app_state
from gamesync.effects.presets import PRESET_BUILDERS, get_preset
from gamesync.sports.models import GameEvent, GameEventType, LeagueId, LEAGUE_SPORT_MAP, SportType

router = APIRouter(tags=["effects"])


class TriggerRequest(BaseModel):
    team_id: str | None = None
    event_type: str = "score_change"
    league: str | None = None


@router.get("/effects/presets")
async def list_presets():
    """List all available effect presets."""
    presets = []
    for (sport, event_type), _ in PRESET_BUILDERS.items():
        presets.append({
            "sport": sport.value,
            "event_type": event_type.value,
        })
    return {"presets": presets}


@router.post("/effects/trigger")
async def trigger_effect(req: TriggerRequest):
    """Manually trigger an effect for testing."""
    if not app_state.db or not app_state.effect_composer or not app_state.effect_executor:
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        event_type = GameEventType(req.event_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {req.event_type}")

    # Find light entities for this team
    light_groups = await app_state.db.get_light_groups()
    entity_ids: list[str] = []
    for group in light_groups:
        if req.team_id and req.team_id in group.team_ids:
            entity_ids.extend(group.entity_ids)
        elif not req.team_id:
            entity_ids.extend(group.entity_ids)

    if not entity_ids:
        # Fallback: use all light groups
        for group in light_groups:
            entity_ids.extend(group.entity_ids)

    if not entity_ids:
        raise HTTPException(
            status_code=400,
            detail="No light groups configured. Add lights in the Lights settings.",
        )

    # Determine colors
    primary_color = "#FFFFFF"
    secondary_color = "#000000"
    sport = SportType.NFL  # default

    if req.league:
        try:
            league = LeagueId(req.league)
            sport = LEAGUE_SPORT_MAP.get(league, SportType.NFL)
        except ValueError:
            pass

    # Try to find team colors from provider
    if req.team_id and app_state.registry:
        for lid in LeagueId:
            provider = app_state.registry.get(lid)
            if provider:
                try:
                    teams = await provider.get_teams()
                    for t in teams:
                        if t.id == req.team_id:
                            primary_color = t.primary_color or primary_color
                            secondary_color = t.secondary_color or secondary_color
                            sport = t.sport
                            break
                except Exception:
                    pass

    # Build and execute effect
    sequence = get_preset(
        sport=sport,
        event_type=event_type,
        entity_ids=entity_ids,
        primary_color=primary_color,
        secondary_color=secondary_color,
    )

    # Run in background so the API returns immediately
    asyncio.create_task(app_state.effect_executor.execute(sequence, group_key="manual"))

    return {"status": "triggered", "effect": sequence.name, "lights": len(entity_ids)}
