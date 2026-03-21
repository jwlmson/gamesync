"""Unit tests for effects/composer.py — EffectComposer 3-tier resolution."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from gamesync.effects.composer import EffectComposer
from gamesync.effects.models import EffectSequence
from gamesync.sports.models import (
    GameEvent, GameEventType, LeagueId,
)
from gamesync.storage.models import EventTypeDefinition, GameOverrideConfiguration


# ── Helpers ────────────────────────────────────────────────────────────

def _make_event(
    event_type: GameEventType = GameEventType.SCORE_CHANGE,
    team_id: str = "team-home",
    league: LeagueId = LeagueId.NFL,
    game_id: str = "game-1",
) -> GameEvent:
    from uuid import uuid4
    return GameEvent(
        id=str(uuid4()),
        game_id=game_id,
        event_type=event_type,
        team_id=team_id,
        league=league,
    )


def _score_change_event_type_def() -> EventTypeDefinition:
    return EventTypeDefinition(
        id=1,
        league_id=1,
        event_code="score_change",
        display_name="Score Change",
        points_value=1,
        default_effect_type="flash",
    )


def _make_team_event_config(event_type_id: int = 1):
    from gamesync.storage.models import TeamEventConfiguration
    return TeamEventConfiguration(
        id=1,
        followed_team_id="team-home",
        event_type_id=event_type_id,
        light_effect_type="pulse",
        light_color_hex="#00FF00",
        target_light_entities=["light.team"],
        sound_asset_id=None,
        target_media_players=[],
        fire_ha_event=True,
        duration_seconds=5.0,
    )


def _make_override_event_config(inherit: bool = False):
    from gamesync.storage.models import GameOverrideEventConfiguration
    return GameOverrideEventConfiguration(
        id=1,
        game_override_id=1,
        event_type_id=1,
        inherit=inherit,
        light_effect_type="solid",
        light_color_hex="#FF0000",
        target_light_entities=["light.override"],
        sound_asset_id=None,
        target_media_players=[],
        fire_ha_event=True,
        duration_seconds=3.0,
    )


def _mock_db_no_override_no_team():
    db = AsyncMock()
    db.get_game_override = AsyncMock(return_value=None)
    db.get_team_event_configs = AsyncMock(return_value=[])
    db.get_event_type_definitions = AsyncMock(return_value=[_score_change_event_type_def()])
    return db


def _mock_db_with_team_config():
    db = AsyncMock()
    db.get_game_override = AsyncMock(return_value=None)
    db.get_team_event_configs = AsyncMock(return_value=[_make_team_event_config()])
    db.get_event_type_definitions = AsyncMock(return_value=[_score_change_event_type_def()])
    return db


def _mock_db_with_override(inherit: bool = False):
    db = AsyncMock()
    override = GameOverrideConfiguration(
        id=1, game_id="game-1", followed_team_id="team-home",
        is_enabled=True, note="",
    )
    db.get_game_override = AsyncMock(return_value=override)
    db.get_game_override_event_configs = AsyncMock(
        return_value=[_make_override_event_config(inherit=inherit)]
    )
    db.get_team_event_configs = AsyncMock(return_value=[_make_team_event_config()])
    db.get_event_type_definitions = AsyncMock(return_value=[_score_change_event_type_def()])
    return db


# ── Tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_returns_none_for_empty_entity_ids():
    """Composer returns None when no entity IDs are provided."""
    composer = EffectComposer(db=_mock_db_no_override_no_team())
    event = _make_event()
    result = await composer.compose(event, entity_ids=[])
    assert result is None


@pytest.mark.asyncio
async def test_falls_through_to_preset():
    """With no override and no team config, the sport preset is used."""
    db = _mock_db_no_override_no_team()
    composer = EffectComposer(db=db)
    event = _make_event()
    result = await composer.compose(event, entity_ids=["light.test"])
    assert isinstance(result, EffectSequence)


@pytest.mark.asyncio
async def test_falls_through_to_team_config():
    """With no game override but a team config, team config is used (Tier 2)."""
    db = _mock_db_with_team_config()
    composer = EffectComposer(db=db)
    event = _make_event()
    result = await composer.compose(event, entity_ids=["light.test"], game_id="game-1")
    assert isinstance(result, EffectSequence)
    # Team config specifies pulse — verify the step primitive
    assert result.steps[0].primitive.value == "pulse"


@pytest.mark.asyncio
async def test_uses_game_override_when_inherit_false():
    """Game override with inherit=False wins over team config (Tier 1)."""
    db = _mock_db_with_override(inherit=False)
    composer = EffectComposer(db=db)
    event = _make_event()
    result = await composer.compose(event, entity_ids=["light.test"], game_id="game-1")
    assert isinstance(result, EffectSequence)
    # Override specifies solid
    assert result.steps[0].primitive.value == "solid"


@pytest.mark.asyncio
async def test_inherit_true_skips_override():
    """Game override with inherit=True falls through to team config (Tier 2)."""
    db = _mock_db_with_override(inherit=True)
    composer = EffectComposer(db=db)
    event = _make_event()
    result = await composer.compose(event, entity_ids=["light.test"], game_id="game-1")
    assert isinstance(result, EffectSequence)
    # Falls to team config: pulse
    assert result.steps[0].primitive.value == "pulse"
