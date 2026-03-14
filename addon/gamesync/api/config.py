"""App configuration endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from gamesync import main as app_state
from gamesync.storage.models import AppConfig

router = APIRouter(tags=["config"])


@router.get("/config")
async def get_config():
    """Get current app configuration."""
    if not app_state.db:
        raise HTTPException(status_code=503, detail="Service not ready")

    config = await app_state.db.get_app_config()
    return config.model_dump(mode="json")


@router.put("/config")
async def update_config(config: AppConfig):
    """Update app configuration."""
    if not app_state.db:
        raise HTTPException(status_code=503, detail="Service not ready")

    await app_state.db.save_app_config(config)

    # Update delay buffer default
    if app_state.delay_buffer:
        app_state.delay_buffer.set_default_delay(config.default_delay_seconds)

    return {"status": "ok"}
