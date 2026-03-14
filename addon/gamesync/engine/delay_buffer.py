"""Anti-spoiler delay buffer.

Events are held for a configurable per-team delay before being published
to the event emitter. This prevents spoilers when watching delayed streams.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from gamesync.sports.models import GameEvent

logger = logging.getLogger(__name__)


@dataclass(order=True)
class DelayedEvent:
    release_time: datetime
    event: GameEvent = field(compare=False)


class DelayBuffer:
    """Per-team delay queue with asyncio drain loop."""

    def __init__(self) -> None:
        self._delays: dict[str, int] = {}  # team_id -> seconds
        self._default_delay: int = 0
        self._queue: list[DelayedEvent] = []
        self._queue_lock = asyncio.Lock()
        self._wake_event = asyncio.Event()
        self._drain_task: asyncio.Task | None = None
        self._publish_callback = None
        self._running = False

    def set_delay(self, team_id: str, seconds: int) -> None:
        """Set delay for a specific team (0-120)."""
        self._delays[team_id] = max(0, min(120, seconds))
        logger.info("Delay set: team=%s delay=%ds", team_id, self._delays[team_id])

    def get_delay(self, team_id: str) -> int:
        return self._delays.get(team_id, self._default_delay)

    def set_default_delay(self, seconds: int) -> None:
        self._default_delay = max(0, min(120, seconds))

    def load_delays(self, delays: dict[str, int]) -> None:
        """Bulk load delays (e.g., from database on startup)."""
        for team_id, seconds in delays.items():
            self.set_delay(team_id, seconds)

    async def start(self, publish_callback) -> None:
        """Start the drain loop."""
        self._publish_callback = publish_callback
        self._running = True
        self._drain_task = asyncio.create_task(self._drain_loop())
        logger.info("Delay buffer started")

    async def stop(self) -> None:
        """Stop the drain loop."""
        self._running = False
        self._wake_event.set()
        if self._drain_task:
            self._drain_task.cancel()
            try:
                await self._drain_task
            except asyncio.CancelledError:
                pass
        logger.info("Delay buffer stopped")

    async def enqueue(self, event: GameEvent) -> None:
        """Add an event to the delay queue."""
        delay_seconds = self.get_delay(event.team_id) if event.team_id else self._default_delay
        release_time = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

        async with self._queue_lock:
            self._queue.append(DelayedEvent(release_time=release_time, event=event))
            self._queue.sort()

        if delay_seconds > 0:
            logger.debug(
                "Event buffered: %s (delay=%ds, release=%s)",
                event.event_type.value,
                delay_seconds,
                release_time.isoformat(),
            )
        self._wake_event.set()

    async def _drain_loop(self) -> None:
        """Continuously drain events whose release time has passed."""
        while self._running:
            self._wake_event.clear()

            now = datetime.now(timezone.utc)
            to_publish: list[GameEvent] = []

            async with self._queue_lock:
                while self._queue and self._queue[0].release_time <= now:
                    item = self._queue.pop(0)
                    to_publish.append(item.event)

            for event in to_publish:
                if self._publish_callback:
                    try:
                        await self._publish_callback(event)
                    except Exception:
                        logger.exception("Error publishing delayed event")

            # Sleep until next event or wake signal
            sleep_time = 0.1  # default poll interval
            async with self._queue_lock:
                if self._queue:
                    next_release = self._queue[0].release_time
                    delta = (next_release - datetime.now(timezone.utc)).total_seconds()
                    sleep_time = max(0.05, min(delta, 1.0))

            try:
                await asyncio.wait_for(self._wake_event.wait(), timeout=sleep_time)
            except asyncio.TimeoutError:
                pass

    @property
    def pending_count(self) -> int:
        return len(self._queue)
