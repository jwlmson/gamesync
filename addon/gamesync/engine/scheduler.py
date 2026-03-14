"""Polling scheduler — orchestrates score polling at adaptive intervals."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from gamesync.engine.delay_buffer import DelayBuffer
from gamesync.engine.event_emitter import EventEmitter
from gamesync.engine.poller import GamePoller
from gamesync.sports.base import SportProvider
from gamesync.sports.models import GameStatus, LeagueId
from gamesync.sports.registry import ProviderRegistry

logger = logging.getLogger(__name__)


class PollScheduler:
    """Adaptive polling scheduler.

    Three tiers:
    - Idle: no games today → poll schedule every 5 min
    - Game Day: game today not started → poll every 60s
    - Live: game in progress → poll every 10-15s
    """

    def __init__(
        self,
        registry: ProviderRegistry,
        emitter: EventEmitter,
        delay_buffer: DelayBuffer,
        poll_interval_live: int = 15,
        poll_interval_gameday: int = 60,
        poll_interval_idle: int = 300,
    ) -> None:
        self._registry = registry
        self._emitter = emitter
        self._delay_buffer = delay_buffer
        self._poller = GamePoller()
        self._poll_interval_live = poll_interval_live
        self._poll_interval_gameday = poll_interval_gameday
        self._poll_interval_idle = poll_interval_idle

        self._followed_teams: dict[str, LeagueId] = {}  # team_id -> league
        self._tasks: dict[LeagueId, asyncio.Task] = {}
        self._running = False

        # Track state per league
        self._league_has_live: dict[LeagueId, bool] = {}
        self._league_has_today: dict[LeagueId, bool] = {}
        self._last_poll: dict[LeagueId, datetime] = {}

    def set_followed_teams(self, teams: dict[str, LeagueId]) -> None:
        """Update the set of followed teams."""
        self._followed_teams = dict(teams)

    def get_active_leagues(self) -> set[LeagueId]:
        """Return leagues that have at least one followed team."""
        return set(self._followed_teams.values())

    async def start(self) -> None:
        """Start polling loops for each active league."""
        self._running = True
        for league in self.get_active_leagues():
            if league not in self._tasks:
                self._tasks[league] = asyncio.create_task(
                    self._poll_loop(league), name=f"poll-{league.value}"
                )
        logger.info(
            "Scheduler started: %d leagues, %d followed teams",
            len(self._tasks),
            len(self._followed_teams),
        )

    async def stop(self) -> None:
        """Stop all polling loops."""
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        for task in self._tasks.values():
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()
        logger.info("Scheduler stopped")

    async def refresh_leagues(self) -> None:
        """Re-evaluate which leagues need polling."""
        active = self.get_active_leagues()

        # Start new leagues
        for league in active:
            if league not in self._tasks or self._tasks[league].done():
                self._tasks[league] = asyncio.create_task(
                    self._poll_loop(league), name=f"poll-{league.value}"
                )

        # Stop removed leagues
        removed = set(self._tasks.keys()) - active
        for league in removed:
            self._tasks[league].cancel()
            del self._tasks[league]

    async def _poll_loop(self, league: LeagueId) -> None:
        """Main poll loop for a single league."""
        provider = self._registry.get(league)
        if not provider:
            logger.error("No provider for league %s", league.value)
            return

        team_ids = [
            tid for tid, lid in self._followed_teams.items() if lid == league
        ]

        while self._running:
            try:
                interval = await self._poll_once(provider, league, team_ids)
            except Exception:
                logger.exception("Poll error for %s", league.value)
                interval = self._poll_interval_idle

            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break

    async def _poll_once(
        self, provider: SportProvider, league: LeagueId, team_ids: list[str]
    ) -> int:
        """Execute one poll cycle. Returns the next interval in seconds."""
        games = await provider.get_scoreboard()
        self._last_poll[league] = datetime.now(timezone.utc)

        # Filter to followed teams
        relevant = [
            g for g in games
            if g.home_team.id in team_ids or g.away_team.id in team_ids
        ]

        # Check for live games
        has_live = any(
            g.status in (GameStatus.LIVE, GameStatus.HALFTIME) for g in relevant
        )
        has_today = any(
            g.status in (GameStatus.SCHEDULED, GameStatus.PREGAME) for g in relevant
        )
        self._league_has_live[league] = has_live
        self._league_has_today[league] = has_today

        # Detect events
        events = self._poller.update_and_detect(provider, relevant)

        # Push events through delay buffer
        for event in events:
            await self._delay_buffer.enqueue(event)

        # Determine next interval
        if has_live:
            return self._poll_interval_live
        elif has_today:
            return self._poll_interval_gameday
        else:
            self._poller.clear_finished()
            return self._poll_interval_idle

    @property
    def poller(self) -> GamePoller:
        return self._poller

    def get_status(self) -> dict:
        """Return scheduler status for health endpoint."""
        return {
            "running": self._running,
            "active_leagues": [l.value for l in self._tasks.keys()],
            "followed_teams": len(self._followed_teams),
            "live_leagues": [
                l.value for l, v in self._league_has_live.items() if v
            ],
            "last_poll": {
                l.value: t.isoformat() for l, t in self._last_poll.items()
            },
            "pending_delayed_events": self._delay_buffer.pending_count,
            "tracked_games": len(self._poller.get_all_snapshots()),
        }
