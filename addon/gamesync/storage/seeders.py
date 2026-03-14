"""Seed league definitions and event types into the database."""

from __future__ import annotations

import logging

from gamesync.storage.db import Database
from gamesync.storage.models import EventTypeDefinition, League

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
#  League Definitions
# ──────────────────────────────────────────────────────────────────────

LEAGUES: list[dict] = [
    {"code": "nfl", "name": "NFL", "sport_type": "nfl", "polling_interval_minutes": 15},
    {"code": "nba", "name": "NBA", "sport_type": "nba", "polling_interval_minutes": 15},
    {"code": "nhl", "name": "NHL", "sport_type": "nhl", "polling_interval_minutes": 15},
    {"code": "mlb", "name": "MLB", "sport_type": "mlb", "polling_interval_minutes": 15},
    {"code": "eng.1", "name": "Premier League", "sport_type": "soccer", "polling_interval_minutes": 15},
    {"code": "usa.1", "name": "MLS", "sport_type": "soccer", "polling_interval_minutes": 15},
    {"code": "uefa.champions", "name": "Champions League", "sport_type": "soccer", "polling_interval_minutes": 15},
    {"code": "esp.1", "name": "La Liga", "sport_type": "soccer", "polling_interval_minutes": 15},
    {"code": "ger.1", "name": "Bundesliga", "sport_type": "soccer", "polling_interval_minutes": 15},
    {"code": "f1", "name": "Formula 1", "sport_type": "f1", "polling_interval_minutes": 15},
]


# ──────────────────────────────────────────────────────────────────────
#  Event Type Definitions (per league)
# ──────────────────────────────────────────────────────────────────────

# Format: (event_code, display_name, points_value, default_effect_type)
EVENT_TYPES: dict[str, list[tuple[str, str, int, str]]] = {
    "nfl": [
        ("touchdown", "Touchdown", 6, "flash"),
        ("field_goal", "Field Goal", 3, "flash"),
        ("extra_point", "Extra Point", 1, "pulse"),
        ("two_point_conversion", "Two-Point Conversion", 2, "flash"),
        ("safety", "Safety", 2, "flash"),
        ("game_start", "Game Start", 0, "solid"),
        ("game_end", "Game End", 0, "color_cycle"),
        ("halftime", "Halftime", 0, "pulse"),
    ],
    "nba": [
        ("two_pointer", "Two-Pointer", 2, "pulse"),
        ("three_pointer", "Three-Pointer", 3, "flash"),
        ("free_throw", "Free Throw", 1, "pulse"),
        ("game_start", "Game Start", 0, "solid"),
        ("game_end", "Game End", 0, "color_cycle"),
        ("halftime", "Halftime", 0, "pulse"),
    ],
    "nhl": [
        ("goal", "Goal", 1, "flash"),
        ("game_start", "Game Start", 0, "solid"),
        ("game_end", "Game End", 0, "color_cycle"),
        ("halftime", "Intermission", 0, "pulse"),
    ],
    "mlb": [
        ("run", "Run", 1, "flash"),
        ("home_run", "Home Run", 1, "flash"),
        ("grand_slam", "Grand Slam", 4, "color_cycle"),
        ("game_start", "Game Start", 0, "solid"),
        ("game_end", "Game End", 0, "color_cycle"),
        ("halftime", "7th Inning Stretch", 0, "pulse"),
    ],
    # Soccer leagues all share the same event types
    **{
        league: [
            ("goal", "Goal", 1, "flash"),
            ("penalty_goal", "Penalty Goal", 1, "flash"),
            ("own_goal", "Own Goal", 1, "pulse"),
            ("yellow_card", "Yellow Card", 0, "solid"),
            ("red_card", "Red Card", 0, "flash"),
            ("game_start", "Kick-Off", 0, "solid"),
            ("game_end", "Full Time", 0, "color_cycle"),
            ("halftime", "Halftime", 0, "pulse"),
        ]
        for league in ["eng.1", "usa.1", "uefa.champions", "esp.1", "ger.1"]
    },
    "f1": [
        ("race_win", "Race Win", 0, "color_cycle"),
        ("podium", "Podium Finish", 0, "flash"),
        ("fastest_lap", "Fastest Lap", 0, "pulse"),
        ("safety_car", "Safety Car", 0, "solid"),
        ("overtake", "Overtake", 0, "pulse"),
        ("game_start", "Race Start", 0, "flash"),
        ("game_end", "Race End", 0, "color_cycle"),
    ],
}


async def seed_leagues_and_event_types(db: Database) -> None:
    """Seed all league definitions and their event types.

    Uses upserts so it's safe to call on every startup — existing data
    is updated rather than duplicated.
    """
    logger.info("Seeding leagues and event types...")

    for league_data in LEAGUES:
        league = League(**league_data)
        league_id = await db.upsert_league(league)

        event_types = EVENT_TYPES.get(league_data["code"], [])
        for event_code, display_name, points_value, default_effect in event_types:
            et = EventTypeDefinition(
                league_id=league_id,
                event_code=event_code,
                display_name=display_name,
                points_value=points_value,
                default_effect_type=default_effect,
            )
            await db.upsert_event_type(et)

    leagues = await db.get_leagues()
    total_events = 0
    for lg in leagues:
        ets = await db.get_event_type_definitions(league_id=lg.id)
        total_events += len(ets)
    logger.info(
        "Seeded %d leagues with %d event types", len(leagues), total_events
    )
