"""Storage / persistence models — Mowgli v7 expanded data model."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────
#  Enums
# ──────────────────────────────────────────────────────────────────────

class SoundCategory(str, Enum):
    BUILT_IN = "built_in"
    CUSTOM = "custom"


# ──────────────────────────────────────────────────────────────────────
#  Core — kept / extended from v1
# ──────────────────────────────────────────────────────────────────────

class FollowedTeam(BaseModel):
    """A team the user is tracking."""
    team_id: str
    league: str  # LeagueId value
    delay_seconds: int = 0
    effects_enabled: bool = True
    auto_sync_enabled: bool = False
    priority_rank: int = 100  # lower = higher priority


class LightGroup(BaseModel):
    id: str
    name: str
    entity_ids: list[str]
    team_ids: list[str] = []


class AppConfig(BaseModel):
    api_football_key: str | None = None
    default_delay_seconds: int = 0
    poll_interval_live: int = 15
    poll_interval_gameday: int = 60
    poll_interval_idle: int = 300
    tts_entity: str | None = None
    tts_language: str = "en"
    default_audio_entity: str | None = None
    global_mute: bool = False
    effect_max_duration_seconds: int = 30
    effect_brightness_limit: int = 255


# ──────────────────────────────────────────────────────────────────────
#  Leagues & Event Types
# ──────────────────────────────────────────────────────────────────────

class League(BaseModel):
    """Formal league definition, stored in DB and seeded on first run."""
    id: int | None = None
    code: str  # e.g. "nfl", "eng.1"
    name: str  # e.g. "NFL", "Premier League"
    sport_type: str  # SportType value
    polling_interval_minutes: int = 15
    enabled: bool = True


class EventTypeDefinition(BaseModel):
    """Per-league scoring/event type definition."""
    id: int | None = None
    league_id: int
    event_code: str  # e.g. "touchdown", "field_goal"
    display_name: str  # e.g. "Touchdown"
    points_value: int = 0
    default_effect_type: str = "flash"  # EffectPrimitive value


# ──────────────────────────────────────────────────────────────────────
#  Team Event Configuration
# ──────────────────────────────────────────────────────────────────────

class TeamEventConfiguration(BaseModel):
    """Per-team per-event-type effect configuration."""
    id: int | None = None
    followed_team_id: str
    event_type_id: int
    light_effect_type: str = "flash"
    light_color_hex: str = "#FFFFFF"
    target_light_entities: list[str] = []
    sound_asset_id: int | None = None
    target_media_players: list[str] = []
    fire_ha_event: bool = True
    duration_seconds: float = 5.0


# ──────────────────────────────────────────────────────────────────────
#  Game Overrides
# ──────────────────────────────────────────────────────────────────────

class GameOverrideConfiguration(BaseModel):
    """Per-game override header."""
    id: int | None = None
    game_id: str
    followed_team_id: str
    is_enabled: bool = True
    note: str = ""


class GameOverrideEventConfiguration(BaseModel):
    """Per-event override within a game override."""
    id: int | None = None
    game_override_id: int
    event_type_id: int
    inherit: bool = True  # True = use team default, False = use overridden values
    light_effect_type: str = "flash"
    light_color_hex: str = "#FFFFFF"
    target_light_entities: list[str] = []
    sound_asset_id: int | None = None
    target_media_players: list[str] = []
    fire_ha_event: bool = True
    duration_seconds: float = 5.0


# ──────────────────────────────────────────────────────────────────────
#  Sound Assets
# ──────────────────────────────────────────────────────────────────────

class SoundAsset(BaseModel):
    """Audio file in the sound library."""
    id: int | None = None
    name: str
    category: SoundCategory = SoundCategory.BUILT_IN
    file_path: str = ""
    duration_seconds: float = 0.0
    file_size_bytes: int = 0


# ──────────────────────────────────────────────────────────────────────
#  Active Game Sessions
# ──────────────────────────────────────────────────────────────────────

class ActiveGameSession(BaseModel):
    """Runtime tracking of a live game being monitored."""
    id: int | None = None
    game_id: str
    followed_team_id: str
    is_primary: bool = False
    effects_enabled: bool = True
    last_score_home: int = 0
    last_score_away: int = 0
    created_at: str = ""


# ──────────────────────────────────────────────────────────────────────
#  Score Events (deduplication + history)
# ──────────────────────────────────────────────────────────────────────

class ScoreEvent(BaseModel):
    """Individual score event for deduplication and history."""
    id: int | None = None
    game_id: str
    event_type_id: int | None = None
    scoring_team_id: str | None = None
    points_scored: int = 0
    game_time: str = ""
    processed: bool = False
    created_at: str = ""
