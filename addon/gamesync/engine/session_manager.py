"""Active game session management with Primary/Secondary conflict resolution."""

from __future__ import annotations

import logging

from gamesync.storage.db import Database
from gamesync.storage.models import ActiveGameSession

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages active game sessions and resolves Primary/Secondary conflicts.

    Rules:
    - Only one session can be Primary at a time
    - Primary session's effects fire; Secondary sessions log but suppress effects
    - Priority is determined by the followed team's priority_rank (lower = higher)
    - When Primary ends, auto-promote highest-priority Secondary
    - User can manually switch Primary via set_primary()
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    async def start_session(
        self, game_id: str, team_id: str
    ) -> ActiveGameSession:
        """Start or get a session for a game+team. Handles priority resolution."""
        existing = await self._db.get_session_by_game(game_id, team_id)
        if existing:
            return existing

        # Determine if this should be primary
        current_sessions = await self._db.get_active_sessions()
        team = await self._db.get_followed_team(team_id)
        team_priority = team.priority_rank if team else 100

        should_be_primary = True
        if current_sessions:
            # Check if any current primary has higher priority (lower rank)
            for s in current_sessions:
                if s.is_primary:
                    existing_team = await self._db.get_followed_team(s.followed_team_id)
                    existing_priority = existing_team.priority_rank if existing_team else 100
                    if existing_priority <= team_priority:
                        should_be_primary = False
                    else:
                        # New team has higher priority — demote existing primary
                        await self._db.set_primary_session(-1)  # clear all
                    break

        session = ActiveGameSession(
            game_id=game_id,
            followed_team_id=team_id,
            is_primary=should_be_primary,
            effects_enabled=True,
        )
        session_id = await self._db.create_session(session)
        session.id = session_id

        if should_be_primary:
            await self._db.set_primary_session(session_id)
            logger.info(
                "Started PRIMARY session for game %s / team %s",
                game_id, team_id,
            )
        else:
            logger.info(
                "Started SECONDARY session for game %s / team %s",
                game_id, team_id,
            )

        return session

    async def end_session(self, session_id: int) -> None:
        """End a session. If it was Primary, auto-promote next highest-priority."""
        session = await self._db.get_session(session_id)
        if not session:
            return

        was_primary = session.is_primary
        await self._db.delete_session(session_id)
        logger.info("Ended session %d (game %s)", session_id, session.game_id)

        if was_primary:
            await self._auto_promote_primary()

    async def set_primary(self, session_id: int) -> None:
        """Manually switch the primary session."""
        session = await self._db.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        await self._db.set_primary_session(session_id)
        logger.info("Manually set session %d as PRIMARY", session_id)

    async def is_primary(self, session_id: int) -> bool:
        """Check if a session is currently the primary."""
        session = await self._db.get_session(session_id)
        return session.is_primary if session else False

    async def get_primary_session(self) -> ActiveGameSession | None:
        """Get the current primary session, if any."""
        sessions = await self._db.get_active_sessions()
        for s in sessions:
            if s.is_primary:
                return s
        return None

    async def _auto_promote_primary(self) -> None:
        """Promote the highest-priority remaining session to Primary."""
        sessions = await self._db.get_active_sessions()
        if not sessions:
            return

        # Find highest priority (lowest rank)
        best_session = None
        best_rank = float("inf")
        for s in sessions:
            team = await self._db.get_followed_team(s.followed_team_id)
            rank = team.priority_rank if team else 100
            if rank < best_rank:
                best_rank = rank
                best_session = s

        if best_session and best_session.id:
            await self._db.set_primary_session(best_session.id)
            logger.info(
                "Auto-promoted session %d to PRIMARY (team %s, rank %s)",
                best_session.id, best_session.followed_team_id, best_rank,
            )
