import { Link } from 'react-router-dom';
import { Trophy, Calendar, Activity, Zap } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import {
  getGames,
  getLiveGames,
  getSessions,
  getEventHistory,
  getFollowedTeams,
  type Game,
  type ActiveSession,
  type FollowedTeam,
} from '../api/client';

function LoadingPulse() {
  return (
    <div className="flex items-center gap-2 py-8 justify-center">
      <div className="w-3 h-3 bg-accent border border-navy animate-bounce" style={{ animationDelay: '0ms' }} />
      <div className="w-3 h-3 bg-accent border border-navy animate-bounce" style={{ animationDelay: '150ms' }} />
      <div className="w-3 h-3 bg-accent border border-navy animate-bounce" style={{ animationDelay: '300ms' }} />
      <span className="font-archivo text-sm text-muted uppercase tracking-wider ml-2">Loading...</span>
    </div>
  );
}

function ErrorBox({ message }: { message: string }) {
  return (
    <div className="card-hard p-4 border-accent">
      <p className="font-archivo text-sm text-accent font-bold uppercase">Error: {message}</p>
    </div>
  );
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

function isToday(iso: string): boolean {
  const d = new Date(iso);
  const now = new Date();
  return d.toDateString() === now.toDateString();
}

export default function DashboardScreen() {
  const followed = useApi(() => getFollowedTeams(), []);
  const games = useApi(() => getGames(), []);
  const live = useApi(() => getLiveGames(), []);
  const sessions = useApi(() => getSessions(), []);
  const history = useApi(() => getEventHistory(20), []);

  const followedTeams: FollowedTeam[] = followed.data?.teams ?? [];
  const todaysGames: Game[] = (games.data?.games ?? []).filter((g) => isToday(g.start_time));
  const liveGames: Game[] = live.data?.games ?? [];
  const activeSessions: ActiveSession[] = sessions.data ?? [];
  const events: any[] = history.data?.events ?? [];

  // If nothing is loading and no teams followed, show onboarding
  const noTeams = !followed.loading && followedTeams.length === 0;

  return (
    <div className="max-w-[1920px] mx-auto px-6 py-8">
      {/* Page Title */}
      <div className="flex items-center gap-4 mb-8">
        <div className="w-10 h-10 border-2 border-navy bg-accent flex items-center justify-center">
          <Trophy className="w-5 h-5 text-cream" />
        </div>
        <h2 className="font-rokkitt text-3xl font-bold uppercase tracking-wider">Dashboard</h2>
      </div>

      {noTeams && (
        <div className="card-hard p-8 text-center mb-8">
          <Trophy className="w-12 h-12 mx-auto mb-4 text-muted" />
          <h3 className="font-rokkitt text-xl font-bold uppercase tracking-wider mb-2">
            No Teams on Your Roster
          </h3>
          <p className="font-archivo text-sm text-muted mb-6">
            Scout some talent to get started. Follow your favorite teams and GameSync will light up your home on game day.
          </p>
          <Link to="/teams/discover" className="btn-primary inline-block">
            Scout New Talent
          </Link>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Today's Schedule */}
        <div className="lg:col-span-2">
          <div className="flex items-center gap-3 mb-4">
            <Calendar className="w-5 h-5 text-accent" />
            <h3 className="section-heading">Today's Schedule</h3>
          </div>

          {games.loading ? (
            <LoadingPulse />
          ) : games.error ? (
            <ErrorBox message={games.error} />
          ) : todaysGames.length === 0 ? (
            <div className="card-hard p-6 text-center">
              <p className="font-archivo text-sm text-muted">No games scheduled for today.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {todaysGames.map((game) => (
                <div key={game.id} className="card-hard p-4 flex items-center justify-between">
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <span className="font-archivo text-xs font-bold uppercase tracking-wider text-muted bg-navy/10 px-2 py-1 border border-navy/20">
                      {game.league}
                    </span>
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <span className="font-archivo font-bold text-sm truncate">
                        {game.away_team.display_name}
                      </span>
                      <span className="font-rokkitt text-xs text-muted">@</span>
                      <span className="font-archivo font-bold text-sm truncate">
                        {game.home_team.display_name}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 shrink-0 ml-4">
                    {game.venue && (
                      <span className="font-archivo text-xs text-muted hidden sm:block">
                        {game.venue}
                      </span>
                    )}
                    <span className="font-rokkitt font-bold text-sm bg-navy text-cream px-3 py-1 border border-navy">
                      {formatTime(game.start_time)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Active Games */}
          <div className="flex items-center gap-3 mb-4 mt-8">
            <Zap className="w-5 h-5 text-accent" />
            <h3 className="section-heading">Active Games</h3>
          </div>

          {live.loading || sessions.loading ? (
            <LoadingPulse />
          ) : live.error ? (
            <ErrorBox message={live.error} />
          ) : liveGames.length === 0 ? (
            <div className="card-hard p-6 text-center">
              <p className="font-archivo text-sm text-muted">No live games right now.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {liveGames.map((game) => {
                const session = activeSessions.find((s) => s.game_id === game.id);
                return (
                  <div key={game.id} className="card-hard p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="stamp-live text-xs">LIVE</span>
                        <span className="font-archivo text-xs font-bold uppercase tracking-wider text-muted">
                          {game.league}
                        </span>
                      </div>
                      {session && (
                        <span
                          className={`stamp text-xs ${
                            session.is_primary ? 'border-accent text-accent' : 'border-muted text-muted'
                          }`}
                        >
                          {session.is_primary ? 'Primary' : 'Secondary'}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="text-center">
                          <p className="font-archivo font-bold text-sm">{game.away_team.abbreviation}</p>
                          <p className="font-rokkitt text-2xl font-bold">{game.score?.away ?? 0}</p>
                        </div>
                        <span className="font-rokkitt text-muted text-sm">vs</span>
                        <div className="text-center">
                          <p className="font-archivo font-bold text-sm">{game.home_team.abbreviation}</p>
                          <p className="font-rokkitt text-2xl font-bold">{game.score?.home ?? 0}</p>
                        </div>
                      </div>
                      {game.score?.period && (
                        <span className="font-archivo text-xs font-bold text-muted uppercase">
                          {game.score.period} {game.score.clock && `- ${game.score.clock}`}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <Activity className="w-5 h-5 text-accent" />
            <h3 className="section-heading">Recent Activity</h3>
          </div>

          {history.loading ? (
            <LoadingPulse />
          ) : history.error ? (
            <ErrorBox message={history.error} />
          ) : events.length === 0 ? (
            <div className="card-hard p-6 text-center">
              <p className="font-archivo text-sm text-muted">No recent activity.</p>
            </div>
          ) : (
            <div className="card-hard divide-y divide-navy/10">
              {events.map((event, i) => (
                <div key={i} className="p-3 flex items-start gap-3">
                  <div className="w-2 h-2 mt-1.5 bg-accent border border-navy shrink-0" />
                  <div className="min-w-0">
                    <p className="font-archivo text-xs font-bold truncate">
                      {event.event_type ?? event.type ?? 'Event'}
                    </p>
                    <p className="font-archivo text-xs text-muted truncate">
                      {event.description ?? event.team_id ?? ''}
                    </p>
                    {event.created_at && (
                      <p className="font-archivo text-[10px] text-muted/60 mt-0.5">
                        {new Date(event.created_at).toLocaleTimeString([], {
                          hour: 'numeric',
                          minute: '2-digit',
                        })}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
