"""SQLite storage layer — Mowgli v7 schema (13 tables)."""

from __future__ import annotations

import json
import logging
from typing import Any

import aiosqlite

from gamesync.storage.models import (
    ActiveGameSession,
    AppConfig,
    EventTypeDefinition,
    FollowedTeam,
    GameOverrideConfiguration,
    GameOverrideEventConfiguration,
    League,
    LightGroup,
    ScoreEvent,
    SoundAsset,
    SoundCategory,
    TeamEventConfiguration,
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 2

SCHEMA_SQL = """
-- Version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

-- ── Core (kept from v1, extended) ──────────────────────────────────

CREATE TABLE IF NOT EXISTS followed_teams (
    team_id TEXT PRIMARY KEY,
    league TEXT NOT NULL,
    delay_seconds INTEGER DEFAULT 0,
    effects_enabled INTEGER DEFAULT 1,
    auto_sync_enabled INTEGER DEFAULT 0,
    priority_rank INTEGER DEFAULT 100
);

CREATE TABLE IF NOT EXISTS light_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    entity_ids TEXT NOT NULL,  -- JSON array
    team_ids TEXT NOT NULL     -- JSON array
);

CREATE TABLE IF NOT EXISTS effect_configs (
    team_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    config TEXT NOT NULL,  -- JSON
    enabled INTEGER DEFAULT 1,
    PRIMARY KEY (team_id, event_type)
);

CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event_log (
    id TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    team_id TEXT,
    league TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    data TEXT,  -- JSON
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_event_log_timestamp ON event_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_event_log_team ON event_log(team_id);

-- ── New tables (Mowgli v7) ────────────────────────────────────────

CREATE TABLE IF NOT EXISTS leagues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    sport_type TEXT NOT NULL,
    polling_interval_minutes INTEGER DEFAULT 15,
    enabled INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS event_type_definitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id INTEGER NOT NULL,
    event_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    points_value INTEGER DEFAULT 0,
    default_effect_type TEXT DEFAULT 'flash',
    FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE,
    UNIQUE (league_id, event_code)
);

CREATE TABLE IF NOT EXISTS team_event_configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    followed_team_id TEXT NOT NULL,
    event_type_id INTEGER NOT NULL,
    light_effect_type TEXT DEFAULT 'flash',
    light_color_hex TEXT DEFAULT '#FFFFFF',
    target_light_entities TEXT DEFAULT '[]',  -- JSON array
    sound_asset_id INTEGER,
    target_media_players TEXT DEFAULT '[]',   -- JSON array
    fire_ha_event INTEGER DEFAULT 1,
    duration_seconds REAL DEFAULT 5.0,
    FOREIGN KEY (followed_team_id) REFERENCES followed_teams(team_id) ON DELETE CASCADE,
    FOREIGN KEY (event_type_id) REFERENCES event_type_definitions(id) ON DELETE CASCADE,
    FOREIGN KEY (sound_asset_id) REFERENCES sound_assets(id) ON DELETE SET NULL,
    UNIQUE (followed_team_id, event_type_id)
);

CREATE TABLE IF NOT EXISTS game_override_configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    followed_team_id TEXT NOT NULL,
    is_enabled INTEGER DEFAULT 1,
    note TEXT DEFAULT '',
    FOREIGN KEY (followed_team_id) REFERENCES followed_teams(team_id) ON DELETE CASCADE,
    UNIQUE (game_id, followed_team_id)
);

CREATE TABLE IF NOT EXISTS game_override_event_configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_override_id INTEGER NOT NULL,
    event_type_id INTEGER NOT NULL,
    inherit INTEGER DEFAULT 1,
    light_effect_type TEXT DEFAULT 'flash',
    light_color_hex TEXT DEFAULT '#FFFFFF',
    target_light_entities TEXT DEFAULT '[]',
    sound_asset_id INTEGER,
    target_media_players TEXT DEFAULT '[]',
    fire_ha_event INTEGER DEFAULT 1,
    duration_seconds REAL DEFAULT 5.0,
    FOREIGN KEY (game_override_id) REFERENCES game_override_configurations(id) ON DELETE CASCADE,
    FOREIGN KEY (event_type_id) REFERENCES event_type_definitions(id) ON DELETE CASCADE,
    FOREIGN KEY (sound_asset_id) REFERENCES sound_assets(id) ON DELETE SET NULL,
    UNIQUE (game_override_id, event_type_id)
);

CREATE TABLE IF NOT EXISTS sound_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT DEFAULT 'built_in',
    file_path TEXT NOT NULL,
    duration_seconds REAL DEFAULT 0.0,
    file_size_bytes INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS active_game_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    followed_team_id TEXT NOT NULL,
    is_primary INTEGER DEFAULT 0,
    effects_enabled INTEGER DEFAULT 1,
    last_score_home INTEGER DEFAULT 0,
    last_score_away INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (followed_team_id) REFERENCES followed_teams(team_id) ON DELETE CASCADE,
    UNIQUE (game_id, followed_team_id)
);

CREATE TABLE IF NOT EXISTS score_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    event_type_id INTEGER,
    scoring_team_id TEXT,
    points_scored INTEGER DEFAULT 0,
    game_time TEXT DEFAULT '',
    processed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (event_type_id) REFERENCES event_type_definitions(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_score_events_game ON score_events(game_id);
CREATE INDEX IF NOT EXISTS idx_score_events_processed ON score_events(processed);
"""


class Database:
    """Async SQLite database for GameSync persistent storage."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Open database and create schema."""
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA foreign_keys = ON")
        await self._db.executescript(SCHEMA_SQL)
        await self._db.execute(
            "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
            (SCHEMA_VERSION,),
        )
        await self._db.commit()
        logger.info("Database initialized at %s (schema v%d)", self._db_path, SCHEMA_VERSION)

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    # ─────────────────────────────────────────────────────────────────
    #  Followed Teams
    # ─────────────────────────────────────────────────────────────────

    async def get_followed_teams(self) -> list[FollowedTeam]:
        async with self._db.execute("SELECT * FROM followed_teams ORDER BY priority_rank") as cur:
            rows = await cur.fetchall()
            return [
                FollowedTeam(
                    team_id=r["team_id"],
                    league=r["league"],
                    delay_seconds=r["delay_seconds"],
                    effects_enabled=bool(r["effects_enabled"]),
                    auto_sync_enabled=bool(r["auto_sync_enabled"]),
                    priority_rank=r["priority_rank"],
                )
                for r in rows
            ]

    async def get_followed_team(self, team_id: str) -> FollowedTeam | None:
        async with self._db.execute(
            "SELECT * FROM followed_teams WHERE team_id = ?", (team_id,)
        ) as cur:
            r = await cur.fetchone()
            if not r:
                return None
            return FollowedTeam(
                team_id=r["team_id"],
                league=r["league"],
                delay_seconds=r["delay_seconds"],
                effects_enabled=bool(r["effects_enabled"]),
                auto_sync_enabled=bool(r["auto_sync_enabled"]),
                priority_rank=r["priority_rank"],
            )

    async def follow_team(self, team: FollowedTeam) -> None:
        await self._db.execute(
            """INSERT OR REPLACE INTO followed_teams
               (team_id, league, delay_seconds, effects_enabled, auto_sync_enabled, priority_rank)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                team.team_id,
                team.league,
                team.delay_seconds,
                int(team.effects_enabled),
                int(team.auto_sync_enabled),
                team.priority_rank,
            ),
        )
        await self._db.commit()

    async def unfollow_team(self, team_id: str) -> None:
        await self._db.execute("DELETE FROM followed_teams WHERE team_id = ?", (team_id,))
        await self._db.commit()

    async def update_followed_team(self, team_id: str, **kwargs: Any) -> None:
        """Update arbitrary fields on a followed team."""
        if not kwargs:
            return
        set_clauses = []
        params = []
        for key, value in kwargs.items():
            if key in ("delay_seconds", "effects_enabled", "auto_sync_enabled", "priority_rank"):
                if isinstance(value, bool):
                    value = int(value)
                set_clauses.append(f"{key} = ?")
                params.append(value)
        if set_clauses:
            params.append(team_id)
            await self._db.execute(
                f"UPDATE followed_teams SET {', '.join(set_clauses)} WHERE team_id = ?",
                params,
            )
            await self._db.commit()

    # ─────────────────────────────────────────────────────────────────
    #  Light Groups
    # ─────────────────────────────────────────────────────────────────

    async def get_light_groups(self) -> list[LightGroup]:
        async with self._db.execute("SELECT * FROM light_groups") as cur:
            rows = await cur.fetchall()
            return [
                LightGroup(
                    id=r["id"],
                    name=r["name"],
                    entity_ids=json.loads(r["entity_ids"]),
                    team_ids=json.loads(r["team_ids"]),
                )
                for r in rows
            ]

    async def save_light_group(self, group: LightGroup) -> None:
        await self._db.execute(
            """INSERT OR REPLACE INTO light_groups (id, name, entity_ids, team_ids)
               VALUES (?, ?, ?, ?)""",
            (group.id, group.name, json.dumps(group.entity_ids), json.dumps(group.team_ids)),
        )
        await self._db.commit()

    async def delete_light_group(self, group_id: str) -> None:
        await self._db.execute("DELETE FROM light_groups WHERE id = ?", (group_id,))
        await self._db.commit()

    # ─────────────────────────────────────────────────────────────────
    #  App Config
    # ─────────────────────────────────────────────────────────────────

    async def get_app_config(self) -> AppConfig:
        config_dict: dict[str, Any] = {}
        async with self._db.execute("SELECT key, value FROM app_config") as cur:
            rows = await cur.fetchall()
            for r in rows:
                try:
                    config_dict[r["key"]] = json.loads(r["value"])
                except json.JSONDecodeError:
                    config_dict[r["key"]] = r["value"]
        return AppConfig(**config_dict) if config_dict else AppConfig()

    async def save_app_config(self, config: AppConfig) -> None:
        for key, value in config.model_dump().items():
            await self._db.execute(
                "INSERT OR REPLACE INTO app_config (key, value) VALUES (?, ?)",
                (key, json.dumps(value)),
            )
        await self._db.commit()

    # ─────────────────────────────────────────────────────────────────
    #  Event Log (kept from v1)
    # ─────────────────────────────────────────────────────────────────

    async def log_event(
        self,
        event_id: str,
        game_id: str,
        event_type: str,
        team_id: str | None,
        league: str,
        timestamp: str,
        data: dict | None = None,
    ) -> None:
        await self._db.execute(
            """INSERT OR IGNORE INTO event_log
               (id, game_id, event_type, team_id, league, timestamp, data)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (event_id, game_id, event_type, team_id, league, timestamp,
             json.dumps(data) if data else None),
        )
        await self._db.commit()

    async def get_event_log(
        self,
        limit: int = 100,
        team_id: str | None = None,
        event_type: str | None = None,
    ) -> list[dict]:
        query = "SELECT * FROM event_log"
        params: list[Any] = []
        conditions: list[str] = []
        if team_id:
            conditions.append("team_id = ?")
            params.append(team_id)
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with self._db.execute(query, params) as cur:
            rows = await cur.fetchall()
            return [
                {
                    "id": r["id"],
                    "game_id": r["game_id"],
                    "event_type": r["event_type"],
                    "team_id": r["team_id"],
                    "league": r["league"],
                    "timestamp": r["timestamp"],
                    "data": json.loads(r["data"]) if r["data"] else None,
                }
                for r in rows
            ]

    # ─────────────────────────────────────────────────────────────────
    #  Leagues
    # ─────────────────────────────────────────────────────────────────

    async def get_leagues(self, enabled_only: bool = False) -> list[League]:
        query = "SELECT * FROM leagues"
        if enabled_only:
            query += " WHERE enabled = 1"
        query += " ORDER BY name"
        async with self._db.execute(query) as cur:
            rows = await cur.fetchall()
            return [
                League(
                    id=r["id"],
                    code=r["code"],
                    name=r["name"],
                    sport_type=r["sport_type"],
                    polling_interval_minutes=r["polling_interval_minutes"],
                    enabled=bool(r["enabled"]),
                )
                for r in rows
            ]

    async def get_league_by_code(self, code: str) -> League | None:
        async with self._db.execute("SELECT * FROM leagues WHERE code = ?", (code,)) as cur:
            r = await cur.fetchone()
            if not r:
                return None
            return League(
                id=r["id"], code=r["code"], name=r["name"],
                sport_type=r["sport_type"],
                polling_interval_minutes=r["polling_interval_minutes"],
                enabled=bool(r["enabled"]),
            )

    async def upsert_league(self, league: League) -> int:
        """Insert or update a league, return its id."""
        await self._db.execute(
            """INSERT INTO leagues (code, name, sport_type, polling_interval_minutes, enabled)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(code) DO UPDATE SET
                 name=excluded.name,
                 sport_type=excluded.sport_type,
                 polling_interval_minutes=excluded.polling_interval_minutes,
                 enabled=excluded.enabled""",
            (league.code, league.name, league.sport_type,
             league.polling_interval_minutes, int(league.enabled)),
        )
        await self._db.commit()
        async with self._db.execute("SELECT id FROM leagues WHERE code = ?", (league.code,)) as cur:
            row = await cur.fetchone()
            return row["id"]

    async def update_league_enabled(self, league_id: int, enabled: bool) -> None:
        await self._db.execute(
            "UPDATE leagues SET enabled = ? WHERE id = ?", (int(enabled), league_id)
        )
        await self._db.commit()

    # ─────────────────────────────────────────────────────────────────
    #  Event Type Definitions
    # ─────────────────────────────────────────────────────────────────

    async def get_event_type_definitions(
        self, league_id: int | None = None
    ) -> list[EventTypeDefinition]:
        if league_id is not None:
            query = "SELECT * FROM event_type_definitions WHERE league_id = ? ORDER BY event_code"
            params: tuple = (league_id,)
        else:
            query = "SELECT * FROM event_type_definitions ORDER BY league_id, event_code"
            params = ()
        async with self._db.execute(query, params) as cur:
            rows = await cur.fetchall()
            return [
                EventTypeDefinition(
                    id=r["id"],
                    league_id=r["league_id"],
                    event_code=r["event_code"],
                    display_name=r["display_name"],
                    points_value=r["points_value"],
                    default_effect_type=r["default_effect_type"],
                )
                for r in rows
            ]

    async def get_event_type_by_code(self, league_id: int, event_code: str) -> EventTypeDefinition | None:
        async with self._db.execute(
            "SELECT * FROM event_type_definitions WHERE league_id = ? AND event_code = ?",
            (league_id, event_code),
        ) as cur:
            r = await cur.fetchone()
            if not r:
                return None
            return EventTypeDefinition(
                id=r["id"], league_id=r["league_id"],
                event_code=r["event_code"], display_name=r["display_name"],
                points_value=r["points_value"], default_effect_type=r["default_effect_type"],
            )

    async def upsert_event_type(self, et: EventTypeDefinition) -> int:
        await self._db.execute(
            """INSERT INTO event_type_definitions
               (league_id, event_code, display_name, points_value, default_effect_type)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(league_id, event_code) DO UPDATE SET
                 display_name=excluded.display_name,
                 points_value=excluded.points_value,
                 default_effect_type=excluded.default_effect_type""",
            (et.league_id, et.event_code, et.display_name,
             et.points_value, et.default_effect_type),
        )
        await self._db.commit()
        async with self._db.execute(
            "SELECT id FROM event_type_definitions WHERE league_id = ? AND event_code = ?",
            (et.league_id, et.event_code),
        ) as cur:
            row = await cur.fetchone()
            return row["id"]

    # ─────────────────────────────────────────────────────────────────
    #  Team Event Configurations
    # ─────────────────────────────────────────────────────────────────

    async def get_team_event_configs(self, team_id: str) -> list[TeamEventConfiguration]:
        async with self._db.execute(
            "SELECT * FROM team_event_configurations WHERE followed_team_id = ?",
            (team_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [self._row_to_team_event_config(r) for r in rows]

    async def get_team_event_config(
        self, team_id: str, event_type_id: int
    ) -> TeamEventConfiguration | None:
        async with self._db.execute(
            """SELECT * FROM team_event_configurations
               WHERE followed_team_id = ? AND event_type_id = ?""",
            (team_id, event_type_id),
        ) as cur:
            r = await cur.fetchone()
            return self._row_to_team_event_config(r) if r else None

    async def upsert_team_event_config(self, cfg: TeamEventConfiguration) -> int:
        await self._db.execute(
            """INSERT INTO team_event_configurations
               (followed_team_id, event_type_id, light_effect_type, light_color_hex,
                target_light_entities, sound_asset_id, target_media_players,
                fire_ha_event, duration_seconds)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(followed_team_id, event_type_id) DO UPDATE SET
                 light_effect_type=excluded.light_effect_type,
                 light_color_hex=excluded.light_color_hex,
                 target_light_entities=excluded.target_light_entities,
                 sound_asset_id=excluded.sound_asset_id,
                 target_media_players=excluded.target_media_players,
                 fire_ha_event=excluded.fire_ha_event,
                 duration_seconds=excluded.duration_seconds""",
            (
                cfg.followed_team_id, cfg.event_type_id, cfg.light_effect_type,
                cfg.light_color_hex, json.dumps(cfg.target_light_entities),
                cfg.sound_asset_id, json.dumps(cfg.target_media_players),
                int(cfg.fire_ha_event), cfg.duration_seconds,
            ),
        )
        await self._db.commit()
        async with self._db.execute(
            """SELECT id FROM team_event_configurations
               WHERE followed_team_id = ? AND event_type_id = ?""",
            (cfg.followed_team_id, cfg.event_type_id),
        ) as cur:
            row = await cur.fetchone()
            return row["id"]

    async def bulk_upsert_team_event_configs(self, configs: list[TeamEventConfiguration]) -> None:
        for cfg in configs:
            await self.upsert_team_event_config(cfg)

    async def copy_team_event_configs(self, from_team_id: str, to_team_id: str) -> int:
        """Copy all event configs from one team to another. Returns count copied."""
        source = await self.get_team_event_configs(from_team_id)
        count = 0
        for cfg in source:
            cfg.followed_team_id = to_team_id
            cfg.id = None
            await self.upsert_team_event_config(cfg)
            count += 1
        return count

    def _row_to_team_event_config(self, r: aiosqlite.Row) -> TeamEventConfiguration:
        return TeamEventConfiguration(
            id=r["id"],
            followed_team_id=r["followed_team_id"],
            event_type_id=r["event_type_id"],
            light_effect_type=r["light_effect_type"],
            light_color_hex=r["light_color_hex"],
            target_light_entities=json.loads(r["target_light_entities"]),
            sound_asset_id=r["sound_asset_id"],
            target_media_players=json.loads(r["target_media_players"]),
            fire_ha_event=bool(r["fire_ha_event"]),
            duration_seconds=r["duration_seconds"],
        )

    # ─────────────────────────────────────────────────────────────────
    #  Game Override Configurations
    # ─────────────────────────────────────────────────────────────────

    async def get_game_override(
        self, game_id: str, team_id: str
    ) -> GameOverrideConfiguration | None:
        async with self._db.execute(
            """SELECT * FROM game_override_configurations
               WHERE game_id = ? AND followed_team_id = ?""",
            (game_id, team_id),
        ) as cur:
            r = await cur.fetchone()
            if not r:
                return None
            return GameOverrideConfiguration(
                id=r["id"], game_id=r["game_id"],
                followed_team_id=r["followed_team_id"],
                is_enabled=bool(r["is_enabled"]), note=r["note"],
            )

    async def get_game_overrides_for_game(self, game_id: str) -> list[GameOverrideConfiguration]:
        async with self._db.execute(
            "SELECT * FROM game_override_configurations WHERE game_id = ?", (game_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [
                GameOverrideConfiguration(
                    id=r["id"], game_id=r["game_id"],
                    followed_team_id=r["followed_team_id"],
                    is_enabled=bool(r["is_enabled"]), note=r["note"],
                )
                for r in rows
            ]

    async def upsert_game_override(self, override: GameOverrideConfiguration) -> int:
        await self._db.execute(
            """INSERT INTO game_override_configurations
               (game_id, followed_team_id, is_enabled, note)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(game_id, followed_team_id) DO UPDATE SET
                 is_enabled=excluded.is_enabled, note=excluded.note""",
            (override.game_id, override.followed_team_id,
             int(override.is_enabled), override.note),
        )
        await self._db.commit()
        async with self._db.execute(
            """SELECT id FROM game_override_configurations
               WHERE game_id = ? AND followed_team_id = ?""",
            (override.game_id, override.followed_team_id),
        ) as cur:
            row = await cur.fetchone()
            return row["id"]

    async def delete_game_override(self, game_id: str, team_id: str) -> None:
        await self._db.execute(
            """DELETE FROM game_override_configurations
               WHERE game_id = ? AND followed_team_id = ?""",
            (game_id, team_id),
        )
        await self._db.commit()

    # ── Game Override Event Configs ──

    async def get_game_override_event_configs(
        self, override_id: int
    ) -> list[GameOverrideEventConfiguration]:
        async with self._db.execute(
            "SELECT * FROM game_override_event_configurations WHERE game_override_id = ?",
            (override_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [self._row_to_override_event_config(r) for r in rows]

    async def upsert_game_override_event_config(
        self, cfg: GameOverrideEventConfiguration
    ) -> int:
        await self._db.execute(
            """INSERT INTO game_override_event_configurations
               (game_override_id, event_type_id, inherit, light_effect_type, light_color_hex,
                target_light_entities, sound_asset_id, target_media_players,
                fire_ha_event, duration_seconds)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(game_override_id, event_type_id) DO UPDATE SET
                 inherit=excluded.inherit,
                 light_effect_type=excluded.light_effect_type,
                 light_color_hex=excluded.light_color_hex,
                 target_light_entities=excluded.target_light_entities,
                 sound_asset_id=excluded.sound_asset_id,
                 target_media_players=excluded.target_media_players,
                 fire_ha_event=excluded.fire_ha_event,
                 duration_seconds=excluded.duration_seconds""",
            (
                cfg.game_override_id, cfg.event_type_id, int(cfg.inherit),
                cfg.light_effect_type, cfg.light_color_hex,
                json.dumps(cfg.target_light_entities), cfg.sound_asset_id,
                json.dumps(cfg.target_media_players),
                int(cfg.fire_ha_event), cfg.duration_seconds,
            ),
        )
        await self._db.commit()
        async with self._db.execute(
            """SELECT id FROM game_override_event_configurations
               WHERE game_override_id = ? AND event_type_id = ?""",
            (cfg.game_override_id, cfg.event_type_id),
        ) as cur:
            row = await cur.fetchone()
            return row["id"]

    def _row_to_override_event_config(
        self, r: aiosqlite.Row
    ) -> GameOverrideEventConfiguration:
        return GameOverrideEventConfiguration(
            id=r["id"],
            game_override_id=r["game_override_id"],
            event_type_id=r["event_type_id"],
            inherit=bool(r["inherit"]),
            light_effect_type=r["light_effect_type"],
            light_color_hex=r["light_color_hex"],
            target_light_entities=json.loads(r["target_light_entities"]),
            sound_asset_id=r["sound_asset_id"],
            target_media_players=json.loads(r["target_media_players"]),
            fire_ha_event=bool(r["fire_ha_event"]),
            duration_seconds=r["duration_seconds"],
        )

    # ─────────────────────────────────────────────────────────────────
    #  Sound Assets
    # ─────────────────────────────────────────────────────────────────

    async def get_sound_assets(
        self, category: SoundCategory | None = None
    ) -> list[SoundAsset]:
        if category:
            query = "SELECT * FROM sound_assets WHERE category = ? ORDER BY name"
            params: tuple = (category.value,)
        else:
            query = "SELECT * FROM sound_assets ORDER BY category, name"
            params = ()
        async with self._db.execute(query, params) as cur:
            rows = await cur.fetchall()
            return [
                SoundAsset(
                    id=r["id"], name=r["name"],
                    category=SoundCategory(r["category"]),
                    file_path=r["file_path"],
                    duration_seconds=r["duration_seconds"],
                    file_size_bytes=r["file_size_bytes"],
                )
                for r in rows
            ]

    async def get_sound_asset(self, sound_id: int) -> SoundAsset | None:
        async with self._db.execute(
            "SELECT * FROM sound_assets WHERE id = ?", (sound_id,)
        ) as cur:
            r = await cur.fetchone()
            if not r:
                return None
            return SoundAsset(
                id=r["id"], name=r["name"],
                category=SoundCategory(r["category"]),
                file_path=r["file_path"],
                duration_seconds=r["duration_seconds"],
                file_size_bytes=r["file_size_bytes"],
            )

    async def create_sound_asset(self, asset: SoundAsset) -> int:
        async with self._db.execute(
            """INSERT INTO sound_assets (name, category, file_path, duration_seconds, file_size_bytes)
               VALUES (?, ?, ?, ?, ?)""",
            (asset.name, asset.category.value, asset.file_path,
             asset.duration_seconds, asset.file_size_bytes),
        ) as cur:
            sound_id = cur.lastrowid
        await self._db.commit()
        return sound_id

    async def delete_sound_asset(self, sound_id: int) -> bool:
        """Delete a sound asset. Returns True if found and deleted."""
        async with self._db.execute(
            "DELETE FROM sound_assets WHERE id = ?", (sound_id,)
        ) as cur:
            deleted = cur.rowcount > 0
        await self._db.commit()
        return deleted

    # ─────────────────────────────────────────────────────────────────
    #  Active Game Sessions
    # ─────────────────────────────────────────────────────────────────

    async def get_active_sessions(self) -> list[ActiveGameSession]:
        async with self._db.execute(
            "SELECT * FROM active_game_sessions ORDER BY is_primary DESC, created_at"
        ) as cur:
            rows = await cur.fetchall()
            return [self._row_to_session(r) for r in rows]

    async def get_session(self, session_id: int) -> ActiveGameSession | None:
        async with self._db.execute(
            "SELECT * FROM active_game_sessions WHERE id = ?", (session_id,)
        ) as cur:
            r = await cur.fetchone()
            return self._row_to_session(r) if r else None

    async def get_session_by_game(
        self, game_id: str, team_id: str
    ) -> ActiveGameSession | None:
        async with self._db.execute(
            """SELECT * FROM active_game_sessions
               WHERE game_id = ? AND followed_team_id = ?""",
            (game_id, team_id),
        ) as cur:
            r = await cur.fetchone()
            return self._row_to_session(r) if r else None

    async def create_session(self, session: ActiveGameSession) -> int:
        async with self._db.execute(
            """INSERT INTO active_game_sessions
               (game_id, followed_team_id, is_primary, effects_enabled,
                last_score_home, last_score_away)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(game_id, followed_team_id) DO UPDATE SET
                 is_primary=excluded.is_primary,
                 effects_enabled=excluded.effects_enabled""",
            (
                session.game_id, session.followed_team_id,
                int(session.is_primary), int(session.effects_enabled),
                session.last_score_home, session.last_score_away,
            ),
        ) as cur:
            session_id = cur.lastrowid
        await self._db.commit()
        return session_id

    async def update_session_scores(
        self, session_id: int, home: int, away: int
    ) -> None:
        await self._db.execute(
            """UPDATE active_game_sessions
               SET last_score_home = ?, last_score_away = ?
               WHERE id = ?""",
            (home, away, session_id),
        )
        await self._db.commit()

    async def set_primary_session(self, session_id: int) -> None:
        """Make one session primary and all others secondary."""
        await self._db.execute(
            "UPDATE active_game_sessions SET is_primary = 0"
        )
        await self._db.execute(
            "UPDATE active_game_sessions SET is_primary = 1 WHERE id = ?",
            (session_id,),
        )
        await self._db.commit()

    async def delete_session(self, session_id: int) -> None:
        await self._db.execute(
            "DELETE FROM active_game_sessions WHERE id = ?", (session_id,)
        )
        await self._db.commit()

    async def clear_all_sessions(self) -> None:
        await self._db.execute("DELETE FROM active_game_sessions")
        await self._db.commit()

    def _row_to_session(self, r: aiosqlite.Row) -> ActiveGameSession:
        return ActiveGameSession(
            id=r["id"], game_id=r["game_id"],
            followed_team_id=r["followed_team_id"],
            is_primary=bool(r["is_primary"]),
            effects_enabled=bool(r["effects_enabled"]),
            last_score_home=r["last_score_home"],
            last_score_away=r["last_score_away"],
            created_at=r["created_at"] or "",
        )

    # ─────────────────────────────────────────────────────────────────
    #  Score Events
    # ─────────────────────────────────────────────────────────────────

    async def create_score_event(self, event: ScoreEvent) -> int:
        async with self._db.execute(
            """INSERT INTO score_events
               (game_id, event_type_id, scoring_team_id, points_scored, game_time, processed)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                event.game_id, event.event_type_id, event.scoring_team_id,
                event.points_scored, event.game_time, int(event.processed),
            ),
        ) as cur:
            event_id = cur.lastrowid
        await self._db.commit()
        return event_id

    async def get_score_events(
        self, game_id: str | None = None, limit: int = 100
    ) -> list[ScoreEvent]:
        if game_id:
            query = "SELECT * FROM score_events WHERE game_id = ? ORDER BY created_at DESC LIMIT ?"
            params: tuple = (game_id, limit)
        else:
            query = "SELECT * FROM score_events ORDER BY created_at DESC LIMIT ?"
            params = (limit,)
        async with self._db.execute(query, params) as cur:
            rows = await cur.fetchall()
            return [
                ScoreEvent(
                    id=r["id"], game_id=r["game_id"],
                    event_type_id=r["event_type_id"],
                    scoring_team_id=r["scoring_team_id"],
                    points_scored=r["points_scored"],
                    game_time=r["game_time"],
                    processed=bool(r["processed"]),
                    created_at=r["created_at"] or "",
                )
                for r in rows
            ]

    async def mark_score_event_processed(self, event_id: int) -> None:
        await self._db.execute(
            "UPDATE score_events SET processed = 1 WHERE id = ?", (event_id,)
        )
        await self._db.commit()

    # ─────────────────────────────────────────────────────────────────
    #  Effect Configs (legacy, kept for backward compat)
    # ─────────────────────────────────────────────────────────────────

    async def get_effect_configs(self) -> list[dict]:
        async with self._db.execute("SELECT * FROM effect_configs") as cur:
            rows = await cur.fetchall()
            return [
                {
                    "team_id": r["team_id"],
                    "event_type": r["event_type"],
                    "config": json.loads(r["config"]),
                    "enabled": bool(r["enabled"]),
                }
                for r in rows
            ]

    async def save_effect_config(
        self, team_id: str, event_type: str, config: dict, enabled: bool = True
    ) -> None:
        await self._db.execute(
            """INSERT OR REPLACE INTO effect_configs (team_id, event_type, config, enabled)
               VALUES (?, ?, ?, ?)""",
            (team_id, event_type, json.dumps(config), int(enabled)),
        )
        await self._db.commit()
