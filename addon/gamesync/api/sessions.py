"""Active game session API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionResponse(BaseModel):
    id: int
    game_id: str
    followed_team_id: str
    is_primary: bool
    effects_enabled: bool
    last_score_home: int
    last_score_away: int
    created_at: str


@router.get("", response_model=list[SessionResponse])
async def list_sessions():
    from gamesync.main import db
    sessions = await db.get_active_sessions()
    return [
        SessionResponse(
            id=s.id, game_id=s.game_id,
            followed_team_id=s.followed_team_id,
            is_primary=s.is_primary,
            effects_enabled=s.effects_enabled,
            last_score_home=s.last_score_home,
            last_score_away=s.last_score_away,
            created_at=s.created_at,
        )
        for s in sessions
        if s.id is not None
    ]


@router.post("/{session_id}/make-primary")
async def make_primary(session_id: int):
    from gamesync.main import session_manager
    if not session_manager:
        raise HTTPException(500, "Session manager not initialized")
    try:
        await session_manager.set_primary(session_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"status": "ok", "primary_session_id": session_id}


@router.delete("/{session_id}")
async def end_session(session_id: int):
    from gamesync.main import session_manager
    if not session_manager:
        raise HTTPException(500, "Session manager not initialized")
    await session_manager.end_session(session_id)
    return {"status": "ended"}
