"""In-process pub/sub event bus for GameEvents."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from gamesync.sports.models import GameEvent

logger = logging.getLogger(__name__)

# Subscriber type: async callable that takes a GameEvent
Subscriber = Callable[[GameEvent], Coroutine[Any, Any, None]]


class EventEmitter:
    """Simple async pub/sub for GameEvents."""

    def __init__(self) -> None:
        self._subscribers: list[Subscriber] = []
        self._history: list[GameEvent] = []
        self._max_history: int = 500

    def subscribe(self, callback: Subscriber) -> None:
        """Register an async callback for all events."""
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Subscriber) -> None:
        self._subscribers = [s for s in self._subscribers if s is not callback]

    async def publish(self, event: GameEvent) -> None:
        """Publish an event to all subscribers."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        logger.info(
            "Event: %s | game=%s team=%s",
            event.event_type.value,
            event.game_id,
            event.team_name or event.team_id,
        )

        for subscriber in self._subscribers:
            try:
                await subscriber(event)
            except Exception:
                logger.exception("Error in event subscriber %s", subscriber)

    def get_history(
        self,
        limit: int = 100,
        team_id: str | None = None,
        event_type: str | None = None,
    ) -> list[GameEvent]:
        """Return recent event history with optional filters."""
        events = self._history
        if team_id:
            events = [e for e in events if e.team_id == team_id]
        if event_type:
            events = [e for e in events if e.event_type.value == event_type]
        return events[-limit:]

    # SSE support: asyncio queue per connected client
    _sse_queues: list[asyncio.Queue[GameEvent]]

    def create_sse_queue(self) -> asyncio.Queue[GameEvent]:
        """Create a queue for SSE streaming."""
        if not hasattr(self, "_sse_queues"):
            self._sse_queues = []
        q: asyncio.Queue[GameEvent] = asyncio.Queue(maxsize=100)
        self._sse_queues.append(q)
        return q

    def remove_sse_queue(self, q: asyncio.Queue[GameEvent]) -> None:
        if hasattr(self, "_sse_queues"):
            self._sse_queues = [x for x in self._sse_queues if x is not q]

    async def _broadcast_to_sse(self, event: GameEvent) -> None:
        """Push event to all SSE queues."""
        if not hasattr(self, "_sse_queues"):
            return
        for q in self._sse_queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest and add new
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                q.put_nowait(event)
