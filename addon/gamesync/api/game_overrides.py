"""Game override API — per-game effect overrides."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gamesync.storage.models import (
    GameOverrideConfiguration,
    GameOverrideEventConfiguration,
)

router = APIRouter(prefix="/games", tags=["game-overrides"])


class OverrideEventConfigRequest(BaseModel):
    event_type_id: int
    inherit: bool = True
    light_effect_type: str = "flash"
    light_color_hex: str = "#FFFFFF"
    target_light_entities: list[str] = []
    sound_asset_id: int | None = None
    target_media_players: list[str] = []
    fire_ha_event: bool = True
    duration_seconds: float = 5.0


class OverrideRequest(BaseModel):
    followed_team_id: str
    is_enabled: bool = True
    note: str = ""
    event_configs: list[OverrideEventConfigRequest] = []


class OverrideEventConfigResponse(BaseModel):
    id: int
    event_type_id: int
    inherit: bool
    light_effect_type: str
    light_color_hex: str
    target_light_entities: list[str]
    sound_asset_id: int | None
    target_media_players: list[str]
    fire_ha_event: bool
    duration_seconds: float


class OverrideResponse(BaseModel):
    id: int
    game_id: str
    followed_team_id: str
    is_enabled: bool
    note: str
    event_configs: list[OverrideEventConfigResponse] = []


@router.get("/{game_id}/override", response_model=OverrideResponse | None)
async def get_override(game_id: str, team_id: str | None = None):
    from gamesync.main import db
    if not team_id:
        overrides = await db.get_game_overrides_for_game(game_id)
        if not overrides:
            return None
        override = overrides[0]
    else:
        override = await db.get_game_override(game_id, team_id)
    if not override or not override.id:
        return None

    event_configs = await db.get_game_override_event_configs(override.id)
    return OverrideResponse(
        id=override.id, game_id=override.game_id,
        followed_team_id=override.followed_team_id,
        is_enabled=override.is_enabled, note=override.note,
        event_configs=[
            OverrideEventConfigResponse(
                id=ec.id, event_type_id=ec.event_type_id,
                inherit=ec.inherit, light_effect_type=ec.light_effect_type,
                light_color_hex=ec.light_color_hex,
                target_light_entities=ec.target_light_entities,
                sound_asset_id=ec.sound_asset_id,
                target_media_players=ec.target_media_players,
                fire_ha_event=ec.fire_ha_event,
                duration_seconds=ec.duration_seconds,
            )
            for ec in event_configs
            if ec.id is not None
        ],
    )


@router.post("/{game_id}/override", response_model=OverrideResponse)
async def create_override(game_id: str, body: OverrideRequest):
    from gamesync.main import db

    override = GameOverrideConfiguration(
        game_id=game_id,
        followed_team_id=body.followed_team_id,
        is_enabled=body.is_enabled,
        note=body.note,
    )
    override_id = await db.upsert_game_override(override)

    # Save event configs
    saved_events = []
    for ec in body.event_configs:
        oe = GameOverrideEventConfiguration(
            game_override_id=override_id,
            event_type_id=ec.event_type_id,
            inherit=ec.inherit,
            light_effect_type=ec.light_effect_type,
            light_color_hex=ec.light_color_hex,
            target_light_entities=ec.target_light_entities,
            sound_asset_id=ec.sound_asset_id,
            target_media_players=ec.target_media_players,
            fire_ha_event=ec.fire_ha_event,
            duration_seconds=ec.duration_seconds,
        )
        oe_id = await db.upsert_game_override_event_config(oe)
        oe.id = oe_id
        saved_events.append(oe)

    return OverrideResponse(
        id=override_id, game_id=game_id,
        followed_team_id=body.followed_team_id,
        is_enabled=body.is_enabled, note=body.note,
        event_configs=[
            OverrideEventConfigResponse(
                id=ec.id, event_type_id=ec.event_type_id,
                inherit=ec.inherit, light_effect_type=ec.light_effect_type,
                light_color_hex=ec.light_color_hex,
                target_light_entities=ec.target_light_entities,
                sound_asset_id=ec.sound_asset_id,
                target_media_players=ec.target_media_players,
                fire_ha_event=ec.fire_ha_event,
                duration_seconds=ec.duration_seconds,
            )
            for ec in saved_events
            if ec.id is not None
        ],
    )


@router.put("/{game_id}/override", response_model=OverrideResponse)
async def update_override(game_id: str, body: OverrideRequest):
    return await create_override(game_id, body)


@router.delete("/{game_id}/override")
async def delete_override(game_id: str, team_id: str):
    from gamesync.main import db
    await db.delete_game_override(game_id, team_id)
    return {"status": "deleted"}
