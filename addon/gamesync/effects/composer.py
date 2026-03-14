"""Effect composer — 3-tier resolution chain for game events.

Resolution order:
1. Game Override → game_override_event_configurations (if override exists and inherit=False)
2. Team Defaults → team_event_configurations for the scoring team
3. Sport Preset → built-in presets in presets.py
"""

from __future__ import annotations

import logging

from gamesync.effects.models import (
    AudioTarget,
    EffectConfig,
    EffectPrimitive,
    EffectSequence,
    EffectStep,
    LightTarget,
)
from gamesync.effects.presets import get_preset
from gamesync.sports.models import GameEvent, GameEventType, LEAGUE_SPORT_MAP
from gamesync.storage.db import Database
from gamesync.storage.models import (
    GameOverrideEventConfiguration,
    TeamEventConfiguration,
)

logger = logging.getLogger(__name__)


class EffectComposer:
    """Builds effect sequences for game events using 3-tier resolution."""

    def __init__(self, db: Database | None = None) -> None:
        self._db = db
        # Legacy in-memory configs (kept for backward compat)
        self._custom_configs: dict[str, dict[GameEventType, EffectConfig]] = {}

    def set_db(self, db: Database) -> None:
        """Set the database reference (for deferred initialization)."""
        self._db = db

    # Legacy methods — kept for backward compatibility
    def set_config(self, config: EffectConfig) -> None:
        team_configs = self._custom_configs.setdefault(config.team_id, {})
        team_configs[config.event_type] = config

    def load_configs(self, configs: list[EffectConfig]) -> None:
        for c in configs:
            self.set_config(c)

    async def compose(
        self,
        event: GameEvent,
        entity_ids: list[str],
        primary_color: str = "#FFFFFF",
        secondary_color: str = "#000000",
        audio_entity: str | None = None,
        audio_url: str | None = None,
        game_id: str | None = None,
    ) -> EffectSequence | None:
        """Build an effect sequence for a game event.

        Resolves through 3 tiers:
        1. Game Override (if exists and inherit=False)
        2. Team Event Configuration (DB)
        3. Sport Preset (built-in)
        """
        if not entity_ids:
            return None

        team_id = event.team_id
        effective_game_id = game_id or event.game_id

        # ── Tier 1: Game Override ───────────────────────────────────
        if self._db and team_id and effective_game_id:
            sequence = await self._resolve_game_override(
                effective_game_id, team_id, event, entity_ids, audio_entity
            )
            if sequence:
                logger.debug(
                    "Resolved effect from game override: game=%s team=%s",
                    effective_game_id, team_id,
                )
                return sequence

        # ── Tier 2: Team Event Configuration ────────────────────────
        if self._db and team_id:
            sequence = await self._resolve_team_config(
                team_id, event, entity_ids, audio_entity
            )
            if sequence:
                logger.debug(
                    "Resolved effect from team config: team=%s", team_id
                )
                return sequence

        # ── Tier 2b: Legacy in-memory configs ──────────────────────
        if team_id:
            team_configs = self._custom_configs.get(team_id, {})
            custom = team_configs.get(event.event_type)
            if custom and custom.enabled:
                return custom.sequence

        # ── Tier 3: Sport Preset ───────────────────────────────────
        sport = LEAGUE_SPORT_MAP.get(event.league)
        if not sport:
            return None

        return get_preset(
            sport=sport,
            event_type=event.event_type,
            entity_ids=entity_ids,
            primary_color=primary_color,
            secondary_color=secondary_color,
            audio_entity=audio_entity,
            audio_url=audio_url,
        )

    async def _resolve_game_override(
        self,
        game_id: str,
        team_id: str,
        event: GameEvent,
        entity_ids: list[str],
        audio_entity: str | None,
    ) -> EffectSequence | None:
        """Check for a game-specific override for this event."""
        override = await self._db.get_game_override(game_id, team_id)
        if not override or not override.is_enabled or not override.id:
            return None

        override_events = await self._db.get_game_override_event_configs(override.id)
        for oe in override_events:
            if oe.inherit:
                continue  # Falls through to team config
            et_def = await self._lookup_event_type(oe.event_type_id)
            if et_def and self._event_matches(event, et_def.event_code):
                return self._config_to_sequence(
                    oe.light_effect_type, oe.light_color_hex,
                    oe.target_light_entities or entity_ids,
                    oe.duration_seconds, audio_entity,
                    oe.sound_asset_id,
                )
        return None

    async def _resolve_team_config(
        self,
        team_id: str,
        event: GameEvent,
        entity_ids: list[str],
        audio_entity: str | None,
    ) -> EffectSequence | None:
        """Check for a team-level event configuration."""
        configs = await self._db.get_team_event_configs(team_id)
        for cfg in configs:
            et_def = await self._lookup_event_type(cfg.event_type_id)
            if et_def and self._event_matches(event, et_def.event_code):
                return self._config_to_sequence(
                    cfg.light_effect_type, cfg.light_color_hex,
                    cfg.target_light_entities or entity_ids,
                    cfg.duration_seconds, audio_entity,
                    cfg.sound_asset_id,
                )
        return None

    async def _lookup_event_type(self, event_type_id: int):
        """Look up an EventTypeDefinition by ID."""
        event_types = await self._db.get_event_type_definitions()
        for etd in event_types:
            if etd.id == event_type_id:
                return etd
        return None

    @staticmethod
    def _event_matches(event: GameEvent, event_code: str) -> bool:
        """Check if a GameEvent matches an event_code from the definition."""
        event_type_val = event.event_type.value

        # Direct match
        if event_type_val == event_code:
            return True

        # score_change maps to specific scoring events via details
        if event_type_val == "score_change":
            details = event.details or {}
            scoring_type = details.get("scoring_type", "")
            if scoring_type == event_code:
                return True
            # Generic fallback for events without specific type
            if not scoring_type and event_code in ("goal", "run"):
                return True

        return False

    @staticmethod
    def _config_to_sequence(
        effect_type: str,
        color_hex: str,
        entity_ids: list[str],
        duration_seconds: float,
        audio_entity: str | None,
        sound_asset_id: int | None,
    ) -> EffectSequence:
        """Convert a configuration row into an EffectSequence."""
        valid_primitives = [e.value for e in EffectPrimitive]
        primitive = (
            EffectPrimitive(effect_type)
            if effect_type in valid_primitives
            else EffectPrimitive.FLASH
        )

        targets = [LightTarget(entity_ids=entity_ids)]
        duration_ms = int(duration_seconds * 1000)

        params: dict = {"color_hex": color_hex, "brightness": 255}
        if primitive == EffectPrimitive.FLASH:
            params.update({"on_ms": 200, "off_ms": 100, "count": max(1, duration_ms // 300)})
        elif primitive == EffectPrimitive.PULSE:
            params.update({"period_ms": 400, "count": max(1, duration_ms // 400)})
        elif primitive in (EffectPrimitive.SOLID, EffectPrimitive.FADE):
            params["duration_ms"] = duration_ms
        elif primitive == EffectPrimitive.COLOR_CYCLE:
            params.update({
                "colors": [color_hex, "#FFFFFF"],
                "step_ms": 500,
                "cycles": max(1, duration_ms // 1000),
            })

        steps = [EffectStep(primitive=primitive, targets=targets, params=params)]

        audio = None
        if audio_entity and sound_asset_id:
            audio = AudioTarget(
                entity_id=audio_entity,
                media_url=f"/api/sounds/{sound_asset_id}/file",
            )

        return EffectSequence(
            name=f"{effect_type}_{color_hex}",
            steps=steps,
            audio=audio,
            restore_after=True,
        )
