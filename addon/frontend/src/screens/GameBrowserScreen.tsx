import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Filter, Ticket, AlertTriangle } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { getAllGames, getFollowedTeams, type Game, type FollowedTeam } from '../api/client';

function statusBadge(status: string) {
  const s = status.toUpperCase();
  if (s === 'LIVE' || s === 'IN_PROGRESS')
    return (
      <span className="inline-block px-2 py-0.5 text-xs font-archivo font-bold uppercase tracking-wider bg-green-status text-cream border border-green-700 rounded-sm">
        Live
      </span>
    );
  if (s === 'FINAL' || s === 'COMPLETED')
    return (
      <span className="inline-block px-2 py-0.5 text-xs font-archivo font-bold uppercase tracking-wider bg-navy text-cream border border-navy rounded-sm">
        Final
      </span>
    );
  return (
    <span className="inline-block px-2 py-0.5 text-xs font-archivo font-bold uppercase tracking-wider bg-gray-300 text-navy border border-gray-400 rounded-sm">
      Scheduled
    </span>
  );
}

function formatTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' });
}

export default function GameBrowserScreen() {
  const { data: gamesData, loading, error, refetch } = useApi(() => getAllGames(), []);
  const { data: followedData } = useApi(() => getFollowedTeams(), []);

  const [leagueFilter, setLeagueFilter] = useState<string | null>(null);

  const games = gamesData?.games ?? [];
  const followedTeams = followedData?.teams ?? [];
  const followedIds = useMemo(() => new Set(followedTeams.map((t: FollowedTeam) => t.team_id)), [followedTeams]);

  // Extract unique leagues
  const leagues = useMemo(() => {
    const set = new Set(games.map((g: Game) => g.league));
    return Array.from(set).sort();
  }, [games]);

  // Filter by league
  const filtered = useMemo(
    () => (leagueFilter ? games.filter((g: Game) => g.league === leagueFilter) : games),
    [games, leagueFilter],
  );

  // Group by date
  const grouped = useMemo(() => {
    const map = new Map<string, Game[]>();
    for (const g of filtered) {
      const key = new Date(g.start_time).toDateString();
      const list = map.get(key) ?? [];
      list.push(g);
      map.set(key, list);
    }
    // Sort groups by date ascending
    return Array.from(map.entries()).sort(
      (a, b) => new Date(a[0]).getTime() - new Date(b[0]).getTime(),
    );
  }, [filtered]);

  // Check if a game has an override (any followed team in the game)
  const hasOverride = (g: Game) =>
    followedIds.has(g.home_team.id) || followedIds.has(g.away_team.id);

  const isLive = (s: string) => {
    const u = s.toUpperCase();
    return u === 'LIVE' || u === 'IN_PROGRESS';
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-12 text-center">
        <div className="animate-pulse font-archivo text-sm uppercase tracking-wider text-muted">
          Loading games...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-12">
        <div className="card-hard p-6 flex items-center gap-4">
          <AlertTriangle className="w-6 h-6 text-accent flex-shrink-0" />
          <div>
            <p className="font-archivo font-bold text-sm uppercase tracking-wider">
              Failed to load games
            </p>
            <p className="font-archivo text-sm text-muted mt-1">{error}</p>
          </div>
          <button onClick={refetch} className="btn-secondary ml-auto text-xs">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Ticket className="w-7 h-7 text-accent" />
        <h2 className="font-rokkitt text-2xl font-bold uppercase tracking-wider">
          Game Browser
        </h2>
      </div>

      {/* League filter bar */}
      <div className="flex items-center gap-3 mb-8 flex-wrap">
        <Filter className="w-4 h-4 text-muted" />
        <button
          onClick={() => setLeagueFilter(null)}
          className={`font-archivo text-xs font-bold uppercase tracking-wider px-4 py-2 border-2 border-navy transition-colors ${
            leagueFilter === null ? 'bg-navy text-cream' : 'bg-cream text-navy hover:bg-navy hover:text-cream'
          }`}
        >
          All
        </button>
        {leagues.map((league) => (
          <button
            key={league}
            onClick={() => setLeagueFilter(league === leagueFilter ? null : league)}
            className={`font-archivo text-xs font-bold uppercase tracking-wider px-4 py-2 border-2 border-navy transition-colors ${
              leagueFilter === league ? 'bg-navy text-cream' : 'bg-cream text-navy hover:bg-navy hover:text-cream'
            }`}
          >
            {league}
          </button>
        ))}
      </div>

      {/* Games grouped by date */}
      {grouped.length === 0 && (
        <div className="card-hard p-8 text-center">
          <Calendar className="w-10 h-10 text-muted mx-auto mb-3" />
          <p className="font-archivo text-sm uppercase tracking-wider text-muted">
            No games found
          </p>
        </div>
      )}

      {grouped.map(([dateStr, dateGames]) => (
        <div key={dateStr} className="mb-10">
          {/* Date heading */}
          <div className="flex items-center gap-3 mb-4">
            <Calendar className="w-5 h-5 text-muted" />
            <h3 className="section-heading text-base">{formatDate(dateGames[0].start_time)}</h3>
            <span className="font-archivo text-xs text-muted uppercase tracking-wider">
              {dateGames.length} game{dateGames.length !== 1 ? 's' : ''}
            </span>
          </div>

          <div className="grid gap-4">
            {dateGames.map((game) => (
              <div
                key={game.id}
                className="card-hard p-0 overflow-hidden"
              >
                {/* Ticket-style card */}
                <div className="flex items-stretch">
                  {/* Left accent bar */}
                  <div
                    className={`w-2 flex-shrink-0 ${
                      isLive(game.status) ? 'bg-green-status' : 'bg-navy'
                    }`}
                  />

                  {/* Main content */}
                  <div className="flex-1 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="font-archivo text-xs font-bold uppercase tracking-wider text-muted">
                          {game.league}
                        </span>
                        {statusBadge(game.status)}
                        {hasOverride(game) && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-archivo font-bold uppercase tracking-wider bg-accent/10 text-accent border border-accent rounded-sm">
                            <AlertTriangle className="w-3 h-3" />
                            Override
                          </span>
                        )}
                      </div>
                      <span className="font-archivo text-xs text-muted">
                        {formatTime(game.start_time)}
                      </span>
                    </div>

                    {/* Teams and score */}
                    <div className="flex items-center gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <span
                            className={`font-rokkitt text-lg font-bold uppercase tracking-wide truncate ${
                              followedIds.has(game.home_team.id) ? 'text-accent' : 'text-navy'
                            }`}
                          >
                            {game.home_team.display_name || game.home_team.name}
                          </span>
                          {game.score && (
                            <span className="font-rokkitt text-xl font-bold text-navy ml-3">
                              {game.score.home}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center justify-between">
                          <span
                            className={`font-rokkitt text-lg font-bold uppercase tracking-wide truncate ${
                              followedIds.has(game.away_team.id) ? 'text-accent' : 'text-navy'
                            }`}
                          >
                            {game.away_team.display_name || game.away_team.name}
                          </span>
                          {game.score && (
                            <span className="font-rokkitt text-xl font-bold text-navy ml-3">
                              {game.score.away}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Clock / period if live */}
                    {isLive(game.status) && game.score?.clock && (
                      <p className="font-archivo text-xs text-muted mt-2 uppercase tracking-wider">
                        {game.score.period && `${game.score.period} · `}
                        {game.score.clock}
                      </p>
                    )}

                    {/* Venue */}
                    {game.venue && (
                      <p className="font-archivo text-xs text-muted mt-1 truncate">
                        {game.venue}
                      </p>
                    )}
                  </div>

                  {/* Right action area — dashed ticket stub */}
                  <div className="flex-shrink-0 w-36 border-l-2 border-dashed border-navy flex flex-col items-center justify-center gap-2 px-4 bg-cream">
                    <Ticket className="w-5 h-5 text-muted" />
                    <Link
                      to={`/games/${game.id}/override`}
                      className="btn-secondary text-xs py-1.5 px-3 whitespace-nowrap"
                    >
                      Override
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
