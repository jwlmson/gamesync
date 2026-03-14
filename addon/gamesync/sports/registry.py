"""Provider registry — maps leagues to provider instances."""

from __future__ import annotations

import logging

from gamesync.sports.base import SportProvider
from gamesync.sports.espn import ESPNClient
from gamesync.sports.espn_mlb import ESPNMLBProvider
from gamesync.sports.espn_nba import ESPNNBAProvider
from gamesync.sports.espn_nfl import ESPNNFLProvider
from gamesync.sports.espn_nhl import ESPNNHLProvider
from gamesync.sports.espn_soccer import ESPNSoccerProvider
from gamesync.sports.models import LeagueId
from gamesync.sports.openf1 import OpenF1Provider

logger = logging.getLogger(__name__)

# Soccer leagues served by ESPN
SOCCER_LEAGUES = [
    LeagueId.EPL,
    LeagueId.MLS,
    LeagueId.CHAMPIONS_LEAGUE,
    LeagueId.LA_LIGA,
    LeagueId.BUNDESLIGA,
]


class ProviderRegistry:
    """Central registry of all active sport providers."""

    def __init__(self) -> None:
        self._providers: dict[LeagueId, SportProvider] = {}
        self._espn_client: ESPNClient | None = None
        self._openf1_provider: OpenF1Provider | None = None

    async def initialize(self) -> None:
        """Create and register all providers."""
        self._espn_client = ESPNClient()

        # ESPN-backed providers
        self._providers[LeagueId.NFL] = ESPNNFLProvider(self._espn_client)
        self._providers[LeagueId.NBA] = ESPNNBAProvider(self._espn_client)
        self._providers[LeagueId.NHL] = ESPNNHLProvider(self._espn_client)
        self._providers[LeagueId.MLB] = ESPNMLBProvider(self._espn_client)

        # Soccer leagues
        for league in SOCCER_LEAGUES:
            self._providers[league] = ESPNSoccerProvider(self._espn_client, league)

        # F1
        self._openf1_provider = OpenF1Provider()
        self._providers[LeagueId.F1] = self._openf1_provider

        logger.info("Initialized %d sport providers", len(self._providers))

    async def shutdown(self) -> None:
        """Close all provider clients."""
        if self._espn_client:
            await self._espn_client.close()
        if self._openf1_provider:
            await self._openf1_provider.close()

    def get(self, league: LeagueId) -> SportProvider | None:
        return self._providers.get(league)

    def get_all(self) -> dict[LeagueId, SportProvider]:
        return dict(self._providers)

    def get_leagues(self) -> list[LeagueId]:
        return list(self._providers.keys())

    def get_providers_for_leagues(
        self, leagues: list[LeagueId]
    ) -> dict[LeagueId, SportProvider]:
        return {l: p for l, p in self._providers.items() if l in leagues}
