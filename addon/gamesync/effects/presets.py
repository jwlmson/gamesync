"""Built-in effect presets for each sport event type."""

from __future__ import annotations

from gamesync.effects.models import (
    AudioTarget,
    EffectPrimitive,
    EffectSequence,
    EffectStep,
    LightTarget,
)
from gamesync.sports.models import GameEventType, SportType


def _make_targets(entity_ids: list[str]) -> list[LightTarget]:
    return [LightTarget(entity_ids=entity_ids)]


def get_preset(
    sport: SportType,
    event_type: GameEventType,
    entity_ids: list[str],
    primary_color: str = "#FFFFFF",
    secondary_color: str = "#000000",
    audio_entity: str | None = None,
    audio_url: str | None = None,
) -> EffectSequence:
    """Get the default effect preset for a sport + event type."""
    targets = _make_targets(entity_ids)

    # Select preset based on sport + event type
    key = (sport, event_type)
    builder = PRESET_BUILDERS.get(key, _default_score)

    sequence = builder(targets, primary_color, secondary_color)

    # Add audio if configured
    if audio_entity and audio_url:
        sequence.audio = AudioTarget(entity_id=audio_entity, media_url=audio_url)

    return sequence


def _nfl_touchdown(
    targets: list[LightTarget], primary: str, secondary: str
) -> EffectSequence:
    return EffectSequence(
        name="NFL Touchdown",
        steps=[
            EffectStep(
                primitive=EffectPrimitive.FLASH,
                targets=targets,
                params={"color_hex": primary, "on_ms": 200, "off_ms": 100, "count": 5},
            ),
            EffectStep(
                primitive=EffectPrimitive.SOLID,
                targets=targets,
                params={"color_hex": primary, "duration_ms": 3000},
            ),
            EffectStep(primitive=EffectPrimitive.RESTORE, targets=targets),
        ],
    )


def _nfl_field_goal(
    targets: list[LightTarget], primary: str, secondary: str
) -> EffectSequence:
    return EffectSequence(
        name="NFL Field Goal",
        steps=[
            EffectStep(
                primitive=EffectPrimitive.FLASH,
                targets=targets,
                params={"color_hex": primary, "on_ms": 300, "off_ms": 200, "count": 3},
            ),
            EffectStep(primitive=EffectPrimitive.RESTORE, targets=targets),
        ],
    )


def _hockey_goal(
    targets: list[LightTarget], primary: str, secondary: str
) -> EffectSequence:
    return EffectSequence(
        name="Hockey Goal",
        steps=[
            EffectStep(
                primitive=EffectPrimitive.FLASH,
                targets=targets,
                params={"color_hex": primary, "on_ms": 150, "off_ms": 100, "count": 8},
            ),
            EffectStep(
                primitive=EffectPrimitive.COLOR_CYCLE,
                targets=targets,
                params={"colors": [primary, secondary], "step_ms": 500, "cycles": 4},
            ),
            EffectStep(primitive=EffectPrimitive.RESTORE, targets=targets),
        ],
    )


def _soccer_goal(
    targets: list[LightTarget], primary: str, secondary: str
) -> EffectSequence:
    return EffectSequence(
        name="Soccer Goal",
        steps=[
            EffectStep(
                primitive=EffectPrimitive.FLASH,
                targets=targets,
                params={"color_hex": primary, "on_ms": 150, "off_ms": 100, "count": 8},
            ),
            EffectStep(
                primitive=EffectPrimitive.COLOR_CYCLE,
                targets=targets,
                params={"colors": [primary, secondary], "step_ms": 500, "cycles": 4},
            ),
            EffectStep(primitive=EffectPrimitive.RESTORE, targets=targets),
        ],
    )


def _nba_basket(
    targets: list[LightTarget], primary: str, secondary: str
) -> EffectSequence:
    return EffectSequence(
        name="NBA Basket",
        steps=[
            EffectStep(
                primitive=EffectPrimitive.PULSE,
                targets=targets,
                params={
                    "color_hex": primary,
                    "min_brightness": 128,
                    "max_brightness": 255,
                    "period_ms": 400,
                    "count": 3,
                },
            ),
            EffectStep(primitive=EffectPrimitive.RESTORE, targets=targets),
        ],
    )


def _mlb_run(
    targets: list[LightTarget], primary: str, secondary: str
) -> EffectSequence:
    return EffectSequence(
        name="MLB Run",
        steps=[
            EffectStep(
                primitive=EffectPrimitive.FLASH,
                targets=targets,
                params={"color_hex": primary, "on_ms": 300, "off_ms": 200, "count": 3},
            ),
            EffectStep(
                primitive=EffectPrimitive.FADE,
                targets=targets,
                params={"from_color": primary, "to_color": secondary, "duration_ms": 2000},
            ),
            EffectStep(primitive=EffectPrimitive.RESTORE, targets=targets),
        ],
    )


def _f1_overtake(
    targets: list[LightTarget], primary: str, secondary: str
) -> EffectSequence:
    return EffectSequence(
        name="F1 Overtake",
        steps=[
            EffectStep(
                primitive=EffectPrimitive.FLASH,
                targets=targets,
                params={"color_hex": primary, "on_ms": 200, "off_ms": 100, "count": 3},
            ),
            EffectStep(primitive=EffectPrimitive.RESTORE, targets=targets),
        ],
    )


def _game_start(
    targets: list[LightTarget], primary: str, secondary: str
) -> EffectSequence:
    return EffectSequence(
        name="Game Start",
        steps=[
            EffectStep(
                primitive=EffectPrimitive.COLOR_CYCLE,
                targets=targets,
                params={"colors": [primary, secondary], "step_ms": 1000, "cycles": 3},
            ),
            EffectStep(
                primitive=EffectPrimitive.SOLID,
                targets=targets,
                params={"color_hex": primary, "duration_ms": 2000},
            ),
            EffectStep(primitive=EffectPrimitive.RESTORE, targets=targets),
        ],
    )


def _game_end_win(
    targets: list[LightTarget], primary: str, secondary: str
) -> EffectSequence:
    return EffectSequence(
        name="Game End - Win",
        steps=[
            EffectStep(
                primitive=EffectPrimitive.FLASH,
                targets=targets,
                params={"color_hex": primary, "on_ms": 100, "off_ms": 50, "count": 10},
            ),
            EffectStep(
                primitive=EffectPrimitive.PULSE,
                targets=targets,
                params={
                    "color_hex": primary,
                    "min_brightness": 75,
                    "max_brightness": 255,
                    "period_ms": 500,
                    "count": 5,
                },
            ),
            EffectStep(primitive=EffectPrimitive.RESTORE, targets=targets),
        ],
    )


def _game_end_loss(
    targets: list[LightTarget], primary: str, secondary: str
) -> EffectSequence:
    return EffectSequence(
        name="Game End - Loss",
        steps=[
            EffectStep(
                primitive=EffectPrimitive.FADE,
                targets=targets,
                params={"from_color": primary, "to_color": "#333333", "duration_ms": 3000},
            ),
            EffectStep(primitive=EffectPrimitive.RESTORE, targets=targets),
        ],
    )


def _default_score(
    targets: list[LightTarget], primary: str, secondary: str
) -> EffectSequence:
    return EffectSequence(
        name="Score",
        steps=[
            EffectStep(
                primitive=EffectPrimitive.FLASH,
                targets=targets,
                params={"color_hex": primary, "on_ms": 200, "off_ms": 100, "count": 5},
            ),
            EffectStep(primitive=EffectPrimitive.RESTORE, targets=targets),
        ],
    )


# Registry: (SportType, GameEventType) -> builder function
PRESET_BUILDERS = {
    # NFL
    (SportType.NFL, GameEventType.SCORE_CHANGE): _nfl_touchdown,
    (SportType.NFL, GameEventType.GAME_START): _game_start,
    (SportType.NFL, GameEventType.GAME_END): _game_end_win,
    # NBA
    (SportType.NBA, GameEventType.SCORE_CHANGE): _nba_basket,
    (SportType.NBA, GameEventType.GAME_START): _game_start,
    (SportType.NBA, GameEventType.GAME_END): _game_end_win,
    # NHL
    (SportType.NHL, GameEventType.SCORE_CHANGE): _hockey_goal,
    (SportType.NHL, GameEventType.GAME_START): _game_start,
    (SportType.NHL, GameEventType.GAME_END): _game_end_win,
    # MLB
    (SportType.MLB, GameEventType.SCORE_CHANGE): _mlb_run,
    (SportType.MLB, GameEventType.GAME_START): _game_start,
    (SportType.MLB, GameEventType.GAME_END): _game_end_win,
    # Soccer
    (SportType.SOCCER, GameEventType.SCORE_CHANGE): _soccer_goal,
    (SportType.SOCCER, GameEventType.GAME_START): _game_start,
    (SportType.SOCCER, GameEventType.GAME_END): _game_end_win,
    # F1
    (SportType.F1, GameEventType.POSITION_CHANGE): _f1_overtake,
    (SportType.F1, GameEventType.SAFETY_CAR): _f1_overtake,
}
