"""Event type definitions API — per-league scoring events."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/event-types", tags=["event-types"])


class EventTypeResponse(BaseModel):
    id: int
    league_id: int
    league_code: str
    event_code: str
    display_name: str
    points_value: int
    default_effect_type: str


@router.get("", response_model=list[EventTypeResponse])
async def list_event_types(league: str | None = Query(None)):
    from gamesync.main import db

    league_id = None
    league_map: dict[int, str] = {}

    if league:
        league_obj = await db.get_league_by_code(league)
        if league_obj and league_obj.id:
            league_id = league_obj.id
            league_map[league_obj.id] = league_obj.code
    else:
        for lg in await db.get_leagues():
            if lg.id:
                league_map[lg.id] = lg.code

    event_types = await db.get_event_type_definitions(league_id=league_id)

    # Build league map if filtering by single league
    if league_id and league_id not in league_map:
        league_obj = await db.get_league_by_code(league or "")
        if league_obj and league_obj.id:
            league_map[league_obj.id] = league_obj.code

    return [
        EventTypeResponse(
            id=et.id,
            league_id=et.league_id,
            league_code=league_map.get(et.league_id, "unknown"),
            event_code=et.event_code,
            display_name=et.display_name,
            points_value=et.points_value,
            default_effect_type=et.default_effect_type,
        )
        for et in event_types
        if et.id is not None
    ]
