"""HTTP integration tests for /api/teams endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import httpx
from fastapi import FastAPI

# Import main first to avoid circular import (main.py calls create_app() at module level
# which imports all api routers; subsequent imports of individual routers then work fine).
import gamesync.main  # noqa: F401
from gamesync.api.teams import router
from gamesync.storage.models import FollowedTeam

from tests.conftest import make_followed_team


# ── App fixture ────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(db):
    """HTTP test client with a real in-memory DB and mocked scheduler/buffer."""
    app = FastAPI()
    app.include_router(router, prefix="/api")

    mock_scheduler = MagicMock()
    mock_scheduler.set_followed_teams = MagicMock()
    mock_scheduler.set_followed_team_configs = MagicMock()
    mock_scheduler.refresh_leagues = AsyncMock()

    mock_delay_buffer = MagicMock()
    mock_delay_buffer.set_delay = MagicMock()

    with patch.multiple(
        "gamesync.main",
        db=db,
        scheduler=mock_scheduler,
        delay_buffer=mock_delay_buffer,
        registry=None,
    ):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac


# ── Tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_follow_team_returns_ok_and_persists(client, db):
    """POST /api/teams/follow → 200 and team is in DB."""
    resp = await client.post(
        "/api/teams/follow",
        json={"team_id": "nfl-22", "league": "nfl", "delay_seconds": 0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["team"]["team_id"] == "nfl-22"

    persisted = await db.get_followed_team("nfl-22")
    assert persisted is not None


@pytest.mark.asyncio
async def test_follow_invalid_league_returns_400(client):
    """POST /api/teams/follow with invalid league → 400."""
    resp = await client.post(
        "/api/teams/follow",
        json={"team_id": "x-1", "league": "FAKE_LEAGUE"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_unfollow_team_removes_from_db(client, db):
    await db.follow_team(make_followed_team(team_id="del-1"))

    resp = await client.delete("/api/teams/follow/del-1")
    assert resp.status_code == 200
    assert await db.get_followed_team("del-1") is None


@pytest.mark.asyncio
async def test_update_pregame_alert_fields(client, db):
    """PUT /api/teams/follow/{id} updates pregame_alert fields."""
    await db.follow_team(make_followed_team(team_id="upd-99"))

    resp = await client.put(
        "/api/teams/follow/upd-99",
        json={"pregame_alert_enabled": True, "pregame_alert_minutes": 10},
    )
    assert resp.status_code == 200

    fetched = await db.get_followed_team("upd-99")
    assert fetched.pregame_alert_enabled is True
    assert fetched.pregame_alert_minutes == 10


@pytest.mark.asyncio
async def test_get_followed_teams_returns_pregame_fields(client, db):
    """GET /api/teams/followed response includes pregame_alert fields."""
    await db.follow_team(
        make_followed_team(team_id="pg-1", pregame_alert_enabled=True, pregame_alert_minutes=20)
    )

    resp = await client.get("/api/teams/followed")
    assert resp.status_code == 200
    teams = resp.json()["teams"]
    pg = next((t for t in teams if t["team_id"] == "pg-1"), None)
    assert pg is not None
    assert pg["pregame_alert_enabled"] is True
    assert pg["pregame_alert_minutes"] == 20
