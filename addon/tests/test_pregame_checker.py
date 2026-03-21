"""Unit tests for engine/pregame_checker.py — PreGameChecker."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

import pytest

from gamesync.engine.pregame_checker import PreGameChecker
from gamesync.sports.models import GameEventType, GameStatus, LeagueId, SportType

from tests.conftest import make_game, make_followed_team, make_team


def _mock_db(already_sent: bool = False) -> AsyncMock:
    """Return a mock DB with pregame alert stubs."""
    db = AsyncMock()
    db.has_pregame_alert_been_sent = AsyncMock(return_value=already_sent)
    db.record_pregame_alert_sent = AsyncMock()
    return db


def _future_game(minutes_away: float, **kwargs):
    """Create a SCHEDULED game starting ``minutes_away`` minutes from now."""
    start = datetime.now(timezone.utc) + timedelta(minutes=minutes_away)
    return make_game(
        status=GameStatus.SCHEDULED,
        start_time=start,
        league=LeagueId.NFL,
        sport=SportType.NFL,
        **kwargs,
    )


# ── Tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fires_when_in_window():
    """Game 29.5 min away with 30 min threshold → alert fires."""
    db = _mock_db(already_sent=False)
    checker = PreGameChecker(db)

    game = _future_game(29.5)
    team = make_followed_team(
        team_id=game.home_team.id,
        pregame_alert_enabled=True,
        pregame_alert_minutes=30,
    )
    events = await checker.check([game], [team])

    assert len(events) == 1
    assert events[0].event_type == GameEventType.PREGAME_ALERT


@pytest.mark.asyncio
async def test_no_fire_outside_window():
    """Game 60 min away with 30 min threshold → no alert."""
    db = _mock_db(already_sent=False)
    checker = PreGameChecker(db)

    game = _future_game(60)
    team = make_followed_team(
        team_id=game.home_team.id,
        pregame_alert_enabled=True,
        pregame_alert_minutes=30,
    )
    events = await checker.check([game], [team])

    assert events == []


@pytest.mark.asyncio
async def test_no_fire_when_already_sent():
    """Deduplication: if already sent, no new event."""
    db = _mock_db(already_sent=True)
    checker = PreGameChecker(db)

    game = _future_game(29.5)
    team = make_followed_team(
        team_id=game.home_team.id,
        pregame_alert_enabled=True,
        pregame_alert_minutes=30,
    )
    events = await checker.check([game], [team])

    assert events == []
    db.record_pregame_alert_sent.assert_not_called()


@pytest.mark.asyncio
async def test_no_fire_when_disabled():
    """pregame_alert_enabled=False → no events regardless of timing."""
    db = _mock_db(already_sent=False)
    checker = PreGameChecker(db)

    game = _future_game(29.5)
    team = make_followed_team(
        team_id=game.home_team.id,
        pregame_alert_enabled=False,
        pregame_alert_minutes=30,
    )
    events = await checker.check([game], [team])

    assert events == []
    db.has_pregame_alert_been_sent.assert_not_called()


@pytest.mark.asyncio
async def test_dedup_record_written():
    """record_pregame_alert_sent is called when alert fires for the first time."""
    db = _mock_db(already_sent=False)
    checker = PreGameChecker(db)

    game = _future_game(29.5)
    team = make_followed_team(
        team_id=game.home_team.id,
        pregame_alert_enabled=True,
        pregame_alert_minutes=30,
    )
    await checker.check([game], [team])

    db.record_pregame_alert_sent.assert_awaited_once_with(
        game.id, team.team_id, team.pregame_alert_minutes
    )


@pytest.mark.asyncio
async def test_event_has_correct_fields():
    """Emitted event carries correct game_id, team_id, and details."""
    db = _mock_db(already_sent=False)
    checker = PreGameChecker(db)

    game = _future_game(29.5, game_id="game-abc")
    team = make_followed_team(
        team_id=game.home_team.id,
        pregame_alert_enabled=True,
        pregame_alert_minutes=30,
    )
    events = await checker.check([game], [team])

    ev = events[0]
    assert ev.game_id == "game-abc"
    assert ev.team_id == game.home_team.id
    assert ev.details["alert_minutes"] == 30
    assert "start_time" in ev.details


@pytest.mark.asyncio
async def test_home_and_away_team_separate_alerts():
    """Following both home and away teams → two separate events."""
    db = _mock_db(already_sent=False)
    checker = PreGameChecker(db)

    game = _future_game(29.5, game_id="game-double")
    home_team = make_followed_team(
        team_id=game.home_team.id,
        pregame_alert_enabled=True,
        pregame_alert_minutes=30,
    )
    away_team = make_followed_team(
        team_id=game.away_team.id,
        pregame_alert_enabled=True,
        pregame_alert_minutes=30,
    )
    events = await checker.check([game], [home_team, away_team])

    assert len(events) == 2
    team_ids = {e.team_id for e in events}
    assert game.home_team.id in team_ids
    assert game.away_team.id in team_ids
