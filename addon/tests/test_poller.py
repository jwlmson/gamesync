"""Unit tests for engine/poller.py — GamePoller."""

from __future__ import annotations

from gamesync.engine.poller import GamePoller
from gamesync.sports.base import SportProvider
from gamesync.sports.models import GameEventType, GameStatus, LeagueId, SportType

from tests.conftest import make_game


# ── Minimal concrete SportProvider for tests ──────────────────────────

class _NHLProvider(SportProvider):
    """Thin provider that uses the base detect_events only."""

    @property
    def league_id(self) -> LeagueId:
        return LeagueId.NHL

    async def get_teams(self):
        return []

    async def get_schedule(self, team_id, start, end):
        return []

    async def get_live_games(self, team_ids=None):
        return []

    async def get_scoreboard(self, date=None):
        return []


PROVIDER = _NHLProvider()


# ── Tests ──────────────────────────────────────────────────────────────

def test_no_events_on_first_poll():
    """First call only stores a snapshot — no events emitted."""
    poller = GamePoller()
    game = make_game(league=LeagueId.NHL, sport=SportType.NHL)
    events = poller.update_and_detect(PROVIDER, [game])
    assert events == []


def test_detects_score_change():
    poller = GamePoller()
    g1 = make_game(home_score=0, away_score=0, league=LeagueId.NHL, sport=SportType.NHL)
    poller.update_and_detect(PROVIDER, [g1])

    g2 = make_game(home_score=1, away_score=0, league=LeagueId.NHL, sport=SportType.NHL)
    events = poller.update_and_detect(PROVIDER, [g2])

    assert len(events) == 1
    assert events[0].event_type == GameEventType.SCORE_CHANGE
    assert events[0].team_id == g2.home_team.id


def test_detects_game_start():
    poller = GamePoller()
    g1 = make_game(status=GameStatus.SCHEDULED, league=LeagueId.NHL, sport=SportType.NHL)
    poller.update_and_detect(PROVIDER, [g1])

    g2 = make_game(status=GameStatus.LIVE, league=LeagueId.NHL, sport=SportType.NHL)
    events = poller.update_and_detect(PROVIDER, [g2])

    event_types = [e.event_type for e in events]
    assert GameEventType.GAME_START in event_types


def test_detects_halftime():
    poller = GamePoller()
    g1 = make_game(status=GameStatus.LIVE, league=LeagueId.NHL, sport=SportType.NHL)
    poller.update_and_detect(PROVIDER, [g1])

    g2 = make_game(status=GameStatus.HALFTIME, league=LeagueId.NHL, sport=SportType.NHL)
    events = poller.update_and_detect(PROVIDER, [g2])

    event_types = [e.event_type for e in events]
    assert GameEventType.HALFTIME in event_types


def test_detects_game_end():
    poller = GamePoller()
    g1 = make_game(status=GameStatus.LIVE, home_score=3, away_score=1,
                   league=LeagueId.NHL, sport=SportType.NHL)
    poller.update_and_detect(PROVIDER, [g1])

    g2 = make_game(status=GameStatus.FINAL, home_score=3, away_score=1,
                   league=LeagueId.NHL, sport=SportType.NHL)
    events = poller.update_and_detect(PROVIDER, [g2])

    event_types = [e.event_type for e in events]
    assert GameEventType.GAME_END in event_types


def test_no_event_for_same_score():
    poller = GamePoller()
    g1 = make_game(home_score=2, away_score=2, league=LeagueId.NHL, sport=SportType.NHL)
    poller.update_and_detect(PROVIDER, [g1])

    g2 = make_game(home_score=2, away_score=2, league=LeagueId.NHL, sport=SportType.NHL)
    events = poller.update_and_detect(PROVIDER, [g2])

    score_events = [e for e in events if e.event_type == GameEventType.SCORE_CHANGE]
    assert score_events == []


def test_clear_finished_removes_snapshot():
    poller = GamePoller()
    g = make_game(status=GameStatus.FINAL, league=LeagueId.NHL, sport=SportType.NHL)
    poller.update_and_detect(PROVIDER, [g])

    assert poller.get_snapshot(g.id) is not None
    poller.clear_finished()
    assert poller.get_snapshot(g.id) is None
