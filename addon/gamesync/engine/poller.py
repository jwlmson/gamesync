"""Score poller — detects changes by comparing game snapshots."""

from __future__ import annotations

import logging

from gamesync.sports.base import SportProvider
from gamesync.sports.models import Game, GameEvent

logger = logging.getLogger(__name__)


class GamePoller:
    """Tracks game state and detects score/status changes."""

    def __init__(self) -> None:
        # game_id -> last known Game snapshot
        self._snapshots: dict[str, Game] = {}

    def update_and_detect(
        self, provider: SportProvider, games: list[Game]
    ) -> list[GameEvent]:
        """Update snapshots and return any detected events."""
        all_events: list[GameEvent] = []

        for game in games:
            old = self._snapshots.get(game.id)
            if old is not None:
                events = provider.detect_events(old, game)
                if events:
                    logger.info(
                        "Detected %d events for game %s", len(events), game.id
                    )
                    all_events.extend(events)

            self._snapshots[game.id] = game

        return all_events

    def get_snapshot(self, game_id: str) -> Game | None:
        return self._snapshots.get(game_id)

    def get_all_snapshots(self) -> dict[str, Game]:
        return dict(self._snapshots)

    def clear_finished(self) -> None:
        """Remove snapshots for finished games to prevent memory buildup."""
        from gamesync.sports.models import GameStatus

        finished = [
            gid
            for gid, g in self._snapshots.items()
            if g.status in (GameStatus.FINAL, GameStatus.CANCELLED, GameStatus.POSTPONED)
        ]
        for gid in finished:
            del self._snapshots[gid]
