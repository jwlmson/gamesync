"""Health check endpoint."""

from fastapi import APIRouter

from gamesync import main as app_state

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    status = {
        "status": "ok",
        "version": "0.1.0",
    }
    if app_state.scheduler:
        status["scheduler"] = app_state.scheduler.get_status()
    if app_state.delay_buffer:
        status["pending_delayed_events"] = app_state.delay_buffer.pending_count
    return status
