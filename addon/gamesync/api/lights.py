"""Light group management endpoints."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gamesync import main as app_state
from gamesync.storage.models import LightGroup

router = APIRouter(tags=["lights"])


class CreateGroupRequest(BaseModel):
    name: str
    entity_ids: list[str]
    team_ids: list[str] = []


class UpdateGroupRequest(BaseModel):
    name: str | None = None
    entity_ids: list[str] | None = None
    team_ids: list[str] | None = None


@router.get("/lights/entities")
async def get_light_entities():
    """Fetch available light entities from HA."""
    if not app_state.light_controller:
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        lights = await app_state.light_controller.get_all_lights()
        return {"lights": lights}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch lights from HA: {e}")


@router.get("/lights/groups")
async def get_light_groups():
    """List configured light groups."""
    if not app_state.db:
        return {"groups": []}

    groups = await app_state.db.get_light_groups()
    return {"groups": [g.model_dump(mode="json") for g in groups]}


@router.post("/lights/groups")
async def create_light_group(req: CreateGroupRequest):
    """Create a new light group."""
    if not app_state.db:
        raise HTTPException(status_code=503, detail="Service not ready")

    group = LightGroup(
        id=str(uuid4())[:8],
        name=req.name,
        entity_ids=req.entity_ids,
        team_ids=req.team_ids,
    )
    await app_state.db.save_light_group(group)
    return {"status": "ok", "group": group.model_dump(mode="json")}


@router.put("/lights/groups/{group_id}")
async def update_light_group(group_id: str, req: UpdateGroupRequest):
    """Update a light group."""
    if not app_state.db:
        raise HTTPException(status_code=503, detail="Service not ready")

    groups = await app_state.db.get_light_groups()
    existing = next((g for g in groups if g.id == group_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="Group not found")

    if req.name is not None:
        existing.name = req.name
    if req.entity_ids is not None:
        existing.entity_ids = req.entity_ids
    if req.team_ids is not None:
        existing.team_ids = req.team_ids

    await app_state.db.save_light_group(existing)
    return {"status": "ok", "group": existing.model_dump(mode="json")}


@router.delete("/lights/groups/{group_id}")
async def delete_light_group(group_id: str):
    """Delete a light group."""
    if not app_state.db:
        raise HTTPException(status_code=503, detail="Service not ready")

    await app_state.db.delete_light_group(group_id)
    return {"status": "ok"}
