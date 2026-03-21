"""Unit tests for storage/db.py and storage/migrations.py."""

from __future__ import annotations

import pytest
import pytest_asyncio
import aiosqlite

from gamesync.storage.db import Database, SCHEMA_VERSION
from gamesync.storage.migrations import get_schema_version, run_migrations
from gamesync.storage.models import AppConfig, FollowedTeam

from tests.conftest import make_followed_team


# ── Schema ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_schema_version_is_3(db):
    """Fresh in-memory database should be at schema version 3."""
    assert SCHEMA_VERSION == 3
    async with db._db.execute("SELECT version FROM schema_version") as cur:
        row = await cur.fetchone()
    assert row is not None
    assert row[0] == 3


@pytest.mark.asyncio
async def test_pregame_columns_exist(db):
    """followed_teams table must have pregame_alert columns."""
    async with db._db.execute("PRAGMA table_info(followed_teams)") as cur:
        cols = {row[1] async for row in cur}
    assert "pregame_alert_enabled" in cols
    assert "pregame_alert_minutes" in cols


# ── Migrations ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_migrate_v2_to_v3():
    """Starting from a v2 schema (no pregame columns) migrates cleanly to v3."""
    # Build minimal v2 schema by hand (no pregame_alert columns)
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("""
        CREATE TABLE schema_version (version INTEGER PRIMARY KEY)
    """)
    await conn.execute("""
        CREATE TABLE followed_teams (
            team_id TEXT PRIMARY KEY,
            league TEXT NOT NULL,
            delay_seconds INTEGER DEFAULT 0,
            effects_enabled INTEGER DEFAULT 1,
            auto_sync_enabled INTEGER DEFAULT 0,
            priority_rank INTEGER DEFAULT 100
        )
    """)
    await conn.execute("INSERT INTO schema_version VALUES (2)")
    await conn.commit()

    await run_migrations(conn)

    # Use MAX to handle multiple version rows left by INSERT OR REPLACE pattern
    async with conn.execute("SELECT MAX(version) FROM schema_version") as cur:
        row = await cur.fetchone()
    assert row[0] == 3

    async with conn.execute("PRAGMA table_info(followed_teams)") as cur:
        cols = {row[1] async for row in cur}
    assert "pregame_alert_enabled" in cols
    assert "pregame_alert_minutes" in cols

    async with conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pregame_alerts_sent'") as cur:
        row = await cur.fetchone()
    assert row is not None

    await conn.close()


# ── Follow / get ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_follow_and_get_team(db):
    """follow_team persists a team; get_followed_team returns it with all fields."""
    team = make_followed_team(
        team_id="nfl-42",
        league="nfl",
        pregame_alert_enabled=True,
        pregame_alert_minutes=15,
    )
    await db.follow_team(team)

    fetched = await db.get_followed_team("nfl-42")
    assert fetched is not None
    assert fetched.team_id == "nfl-42"
    assert fetched.pregame_alert_enabled is True
    assert fetched.pregame_alert_minutes == 15


@pytest.mark.asyncio
async def test_unfollow_removes_team(db):
    await db.follow_team(make_followed_team(team_id="rem-1"))
    await db.unfollow_team("rem-1")
    assert await db.get_followed_team("rem-1") is None


@pytest.mark.asyncio
async def test_update_followed_team_pregame_fields(db):
    """update_followed_team can toggle pregame alert settings."""
    await db.follow_team(make_followed_team(team_id="upd-1"))

    await db.update_followed_team(
        "upd-1",
        pregame_alert_enabled=True,
        pregame_alert_minutes=10,
    )

    fetched = await db.get_followed_team("upd-1")
    assert fetched.pregame_alert_enabled is True
    assert fetched.pregame_alert_minutes == 10


# ── Pregame alert deduplication ────────────────────────────────────────

@pytest.mark.asyncio
async def test_pregame_alert_deduplication_roundtrip(db):
    """record_pregame_alert_sent + has_pregame_alert_been_sent behave correctly."""
    game_id, team_id, minutes = "g-1", "t-1", 30

    # Not yet sent
    result = await db.has_pregame_alert_been_sent(game_id, team_id, minutes)
    assert result is False

    await db.record_pregame_alert_sent(game_id, team_id, minutes)

    # Now it's sent
    result = await db.has_pregame_alert_been_sent(game_id, team_id, minutes)
    assert result is True


@pytest.mark.asyncio
async def test_pregame_alert_record_is_idempotent(db):
    """Calling record_pregame_alert_sent twice doesn't raise (INSERT OR IGNORE)."""
    await db.record_pregame_alert_sent("g-2", "t-2", 15)
    await db.record_pregame_alert_sent("g-2", "t-2", 15)  # should not raise
    assert await db.has_pregame_alert_been_sent("g-2", "t-2", 15) is True


# ── Event log ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_log_event_idempotent(db):
    """log_event uses INSERT OR IGNORE — duplicate event_id is silently skipped."""
    await db.log_event(
        event_id="evt-1", game_id="g-1", event_type="score_change",
        team_id="t-1", league="nfl", timestamp="2024-01-01T00:00:00",
        data={"points": 3},
    )
    # Same event_id again — must not raise and must not create duplicate
    await db.log_event(
        event_id="evt-1", game_id="g-1", event_type="score_change",
        team_id="t-1", league="nfl", timestamp="2024-01-01T00:00:00",
        data={"points": 99},  # different data — should be ignored
    )
    rows = await db.get_event_log()
    matching = [r for r in rows if r["id"] == "evt-1"]
    assert len(matching) == 1
    # Original data was kept
    assert matching[0]["data"]["points"] == 3


# ── App config roundtrip ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_app_config_roundtrip(db):
    """save_app_config + get_app_config round-trips all AppConfig fields."""
    cfg = AppConfig(
        default_delay_seconds=10,
        poll_interval_live=5,
        poll_interval_gameday=120,
        poll_interval_idle=600,
        tts_entity="tts.google",
        tts_language="fr",
        tts_enabled=True,
        default_audio_entity="media_player.living_room",
        global_mute=True,
        effect_max_duration_seconds=45,
        effect_brightness_limit=200,
    )
    await db.save_app_config(cfg)
    loaded = await db.get_app_config()

    assert loaded.default_delay_seconds == 10
    assert loaded.poll_interval_live == 5
    assert loaded.tts_entity == "tts.google"
    assert loaded.tts_language == "fr"
    assert loaded.tts_enabled is True
    assert loaded.global_mute is True
    assert loaded.effect_brightness_limit == 200
