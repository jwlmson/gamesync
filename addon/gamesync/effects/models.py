"""Effect composition models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from gamesync.sports.models import GameEventType


class EffectPrimitive(str, Enum):
    FLASH = "flash"
    COLOR_CYCLE = "color_cycle"
    FADE = "fade"
    SOLID = "solid"
    PULSE = "pulse"
    RESTORE = "restore"


class LightTarget(BaseModel):
    entity_ids: list[str]
    group_name: str | None = None


class AudioTarget(BaseModel):
    entity_id: str
    media_url: str | None = None
    tts_message: str | None = None


class EffectStep(BaseModel):
    primitive: EffectPrimitive
    targets: list[LightTarget]
    params: dict = {}
    delay_after_ms: int = 0


class EffectSequence(BaseModel):
    name: str
    steps: list[EffectStep]
    audio: AudioTarget | None = None
    tts: AudioTarget | None = None
    restore_after: bool = True


class EffectConfig(BaseModel):
    """User's saved configuration for a specific event type + team."""
    team_id: str
    event_type: GameEventType
    sequence: EffectSequence
    enabled: bool = True
