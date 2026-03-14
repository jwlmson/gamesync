"""Event history and SSE stream endpoints."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Query, Request
from sse_starlette.sse import EventSourceResponse

from gamesync import main as app_state

router = APIRouter(tags=["events"])


@router.get("/events/history")
async def get_event_history(
    limit: int = Query(100, ge=1, le=500),
    team_id: str | None = Query(None),
    event_type: str | None = Query(None),
):
    """Get recent event history."""
    if not app_state.db:
        return {"events": []}

    events = await app_state.db.get_event_log(
        limit=limit,
        team_id=team_id,
        event_type=event_type,
    )
    return {"events": events}


@router.get("/events/stream")
async def event_stream(request: Request):
    """Server-Sent Events stream for real-time updates."""
    if not app_state.emitter:
        return {"error": "Service not ready"}

    queue = app_state.emitter.create_sse_queue()

    async def generate():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": event.event_type.value,
                        "data": json.dumps(event.model_dump(mode="json")),
                    }
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {"event": "keepalive", "data": "{}"}
        finally:
            app_state.emitter.remove_sse_queue(queue)

    return EventSourceResponse(generate())
