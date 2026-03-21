"""HTTP integration tests for /api/effects endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import httpx
from fastapi import FastAPI

# Import main first to avoid circular import (main.py calls create_app() at module level
# which imports all api routers; subsequent imports of individual routers then work fine).
import gamesync.main  # noqa: F401
from gamesync.api.effects import router
from gamesync.effects.presets import PRESET_BUILDERS
from gamesync.storage.models import LightGroup


# ── App fixture ────────────────────────────────────────────────────────

def _make_mock_executor(muted: bool = False) -> MagicMock:
    executor = MagicMock()
    executor.muted = muted
    executor.execute = AsyncMock()
    return executor


@pytest_asyncio.fixture
async def client(db):
    """HTTP test client with real DB, mocked executor/composer/registry."""
    app = FastAPI()
    app.include_router(router, prefix="/api")

    executor = _make_mock_executor()

    with patch.multiple(
        "gamesync.main",
        db=db,
        effect_composer=MagicMock(),
        effect_executor=executor,
        registry=None,
    ):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as ac:
            # Expose executor so tests can inspect it
            ac._executor = executor
            yield ac


# ── Tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_presets_returns_all_event_types(client):
    """GET /api/effects/presets lists all registered sport/event_type combos."""
    resp = await client.get("/api/effects/presets")
    assert resp.status_code == 200
    presets = resp.json()["presets"]
    # We have PRESET_BUILDERS entries — ensure they're all listed
    expected_count = len(PRESET_BUILDERS)
    assert len(presets) == expected_count
    for p in presets:
        assert "sport" in p
        assert "event_type" in p


@pytest.mark.asyncio
async def test_trigger_effect_with_light_group(client, db):
    """POST /api/effects/trigger fires an effect when a light group exists."""
    # Seed a light group so the endpoint doesn't return 400
    group = LightGroup(id="grp-1", name="Living Room", entity_ids=["light.lr"], team_ids=[])
    await db.save_light_group(group)

    resp = await client.post(
        "/api/effects/trigger",
        json={"event_type": "score_change"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "triggered"
    assert body["lights"] >= 1


@pytest.mark.asyncio
async def test_trigger_effect_no_lights_returns_400(client):
    """POST /api/effects/trigger with no configured lights → 400."""
    resp = await client.post(
        "/api/effects/trigger",
        json={"event_type": "score_change"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_trigger_effect_invalid_event_type_returns_400(client, db):
    """POST /api/effects/trigger with unknown event_type → 400."""
    group = LightGroup(id="grp-2", name="Test", entity_ids=["light.x"], team_ids=[])
    await db.save_light_group(group)

    resp = await client.post(
        "/api/effects/trigger",
        json={"event_type": "not_a_real_event"},
    )
    assert resp.status_code == 400
