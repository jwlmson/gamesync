"""HA entity discovery and validation API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/ha", tags=["ha-entities"])


class EntityResponse(BaseModel):
    entity_id: str
    friendly_name: str | None = None
    state: str | None = None


class ValidateRequest(BaseModel):
    entity_ids: list[str]


class ValidateResponse(BaseModel):
    valid: list[str]
    invalid: list[str]


@router.get("/entities", response_model=list[EntityResponse])
async def list_entities(domain: str = Query("light")):
    """Fetch HA entities by domain (light, media_player, etc.)."""
    from gamesync.main import ha_client
    if not ha_client:
        raise HTTPException(500, "HA client not initialized")

    try:
        states = await ha_client.get_states()
    except Exception as e:
        raise HTTPException(502, f"Failed to fetch HA states: {e}")

    entities = []
    for s in states:
        entity_id = s.get("entity_id", "")
        if entity_id.startswith(f"{domain}."):
            entities.append(EntityResponse(
                entity_id=entity_id,
                friendly_name=s.get("attributes", {}).get("friendly_name"),
                state=s.get("state"),
            ))

    return sorted(entities, key=lambda e: e.entity_id)


@router.post("/validate-entities", response_model=ValidateResponse)
async def validate_entities(body: ValidateRequest):
    """Validate that entity IDs exist in HA."""
    from gamesync.main import ha_client
    if not ha_client:
        raise HTTPException(500, "HA client not initialized")

    try:
        states = await ha_client.get_states()
    except Exception as e:
        raise HTTPException(502, f"Failed to fetch HA states: {e}")

    known_ids = {s.get("entity_id") for s in states}
    valid = [eid for eid in body.entity_ids if eid in known_ids]
    invalid = [eid for eid in body.entity_ids if eid not in known_ids]

    return ValidateResponse(valid=valid, invalid=invalid)
