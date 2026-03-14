"""Global controls API — mute toggle, emergency stop."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/global", tags=["global"])


class MuteResponse(BaseModel):
    muted: bool


class EmergencyStopResponse(BaseModel):
    stopped_count: int


@router.post("/mute", response_model=MuteResponse)
async def toggle_mute():
    """Toggle the global mute state."""
    from gamesync.main import db, effect_executor

    if not db or not effect_executor:
        raise HTTPException(500, "Not initialized")

    config = await db.get_app_config()
    new_mute = not config.global_mute
    config.global_mute = new_mute
    await db.save_app_config(config)

    effect_executor.muted = new_mute
    return MuteResponse(muted=new_mute)


@router.post("/emergency-stop", response_model=EmergencyStopResponse)
async def emergency_stop():
    """Kill ALL active effects immediately."""
    from gamesync.main import effect_executor

    if not effect_executor:
        raise HTTPException(500, "Not initialized")

    count = await effect_executor.emergency_stop()
    return EmergencyStopResponse(stopped_count=count)
