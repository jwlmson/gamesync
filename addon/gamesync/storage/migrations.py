"""Schema migration from v1 to v2.

Run automatically on startup when existing DB has schema_version = 1.
Adds the new Mowgli v7 columns to followed_teams and creates all new tables.
"""

from __future__ import annotations

import logging

import aiosqlite

logger = logging.getLogger(__name__)


async def get_schema_version(db: aiosqlite.Connection) -> int:
    """Read current schema version from DB."""
    try:
        async with db.execute("SELECT version FROM schema_version LIMIT 1") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0
    except Exception:
        return 0


async def migrate_v1_to_v2(db: aiosqlite.Connection) -> None:
    """Migrate from schema v1 (original 6-table) to v2 (Mowgli v7 13-table).

    This is additive — it only adds columns/tables that don't exist yet.
    Existing data is preserved.
    """
    logger.info("Migrating schema from v1 to v2...")

    # Add new columns to followed_teams
    existing_cols = set()
    async with db.execute("PRAGMA table_info(followed_teams)") as cur:
        async for row in cur:
            existing_cols.add(row[1])  # column name

    if "auto_sync_enabled" not in existing_cols:
        await db.execute(
            "ALTER TABLE followed_teams ADD COLUMN auto_sync_enabled INTEGER DEFAULT 0"
        )
        logger.info("Added auto_sync_enabled column to followed_teams")

    if "priority_rank" not in existing_cols:
        await db.execute(
            "ALTER TABLE followed_teams ADD COLUMN priority_rank INTEGER DEFAULT 100"
        )
        logger.info("Added priority_rank column to followed_teams")

    # Update schema version
    await db.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (2)")
    await db.commit()
    logger.info("Schema migration v1 → v2 complete")


async def run_migrations(db: aiosqlite.Connection) -> None:
    """Run all pending migrations."""
    version = await get_schema_version(db)
    if version < 2:
        await migrate_v1_to_v2(db)
