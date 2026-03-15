import { useState, useMemo } from 'react';
import { Search, UserPlus, UserMinus } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import {
  getTeams,
  getFollowedTeams,
  followTeam,
  unfollowTeam,
  type TeamInfo,
  type FollowedTeam,
} from '../api/client';

const LEAGUES = ['ALL', 'NFL', 'NBA', 'NHL', 'MLB', 'Soccer', 'F1'] as const;

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

export default function TeamDiscoveryScreen() {
  const teams = useApi(() => getTeams(), []);
  const followed = useApi(() => getFollowedTeams(), []);

  const [activeLeague, setActiveLeague] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const followedIds = new Set((followed.data?.teams ?? []).map((ft: FollowedTeam) => ft.team_id));

  const groupedTeams: Record<string, TeamInfo[]> = teams.data?.teams ?? {};

  const filteredGroups = useMemo(() => {
    const result: Record<string, TeamInfo[]> = {};
    const query = searchQuery.toLowerCase();

    for (const [league, leagueTeams] of Object.entries(groupedTeams)) {
      if (activeLeague !== 'ALL' && league.toUpperCase() !== activeLeague.toUpperCase()) continue;

      const filtered = leagueTeams.filter(
        (t) =>
          !query ||
          t.name.toLowerCase().includes(query) ||
          t.display_name.toLowerCase().includes(query) ||
          t.abbreviation.toLowerCase().includes(query)
      );

      if (filtered.length > 0) {
        result[league] = filtered;
      }
    }

    return result;
  }, [groupedTeams, activeLeague, searchQuery]);

  const handleFollow = async (team: TeamInfo) => {
    setActionLoading(team.id);
    try {
      await followTeam(team.id, team.league);
      followed.refetch();
    } catch {
      // silent
    } finally {
      setActionLoading(null);
    }
  };

  const handleUnfollow = async (teamId: string) => {
    setActionLoading(teamId);
    try {
      await unfollowTeam(teamId);
      followed.refetch();
    } catch {
      // silent
    } finally {
      setActionLoading(null);
    }
  };

  const totalFiltered = Object.values(filteredGroups).reduce((sum, arr) => sum + arr.length, 0);

  return (
    <div className="max-w-[1920px] mx-auto px-6 py-8">
      {/* Page Title */}
      <div className="flex items-center gap-4 mb-8">
        <div className="w-10 h-10 border-2 border-navy bg-accent flex items-center justify-center">
          <Search className="w-5 h-5 text-cream" />
        </div>
        <div>
          <h2 className="font-rokkitt text-3xl font-bold uppercase tracking-wider">Scout New Talent</h2>
          <p className="font-archivo text-sm text-muted">Browse all available teams and add them to your roster.</p>
        </div>
      </div>

      {/* League Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {LEAGUES.map((league) => (
          <button
            key={league}
            onClick={() => setActiveLeague(league)}
            className={`font-archivo text-xs font-bold uppercase tracking-wider px-4 py-2 border-2 border-navy transition-colors ${
              activeLeague === league
                ? 'bg-navy text-cream'
                : 'bg-cream text-navy hover:bg-navy/10'
            }`}
          >
            {league}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative mb-8">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" />
        <input
          type="text"
          placeholder="Search teams by name or abbreviation..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-3 border-2 border-navy bg-cream font-archivo text-sm focus:outline-none focus:border-accent placeholder:text-muted/50"
        />
      </div>

      {teams.loading ? (
        <LoadingPulse />
      ) : teams.error ? (
        <ErrorBox message={teams.error} />
      ) : totalFiltered === 0 ? (
        <div className="card-hard p-8 text-center">
          <p className="font-archivo text-sm text-muted">
            No teams found matching your search.
          </p>
        </div>
      ) : (
        Object.entries(filteredGroups).map(([league, leagueTeams]) => (
          <div key={league} className="mb-10">
            <h3 className="section-heading mb-4 pb-2 border-b-2 border-navy">
              {league}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {leagueTeams.map((team) => {
                const isFollowed = followedIds.has(team.id);
                const isLoading = actionLoading === team.id;

                return (
                  <div
                    key={team.id}
                    className="card-hard p-4 flex items-center gap-4 hover:translate-x-[1px] hover:translate-y-[1px] transition-transform"
                  >
                    {/* Team Color Swatch */}
                    <div
                      className="w-12 h-12 border-2 border-navy shrink-0 flex items-center justify-center"
                      style={{ backgroundColor: team.primary_color ?? '#3A5063' }}
                    >
                      <span className="font-rokkitt font-bold text-cream text-xs">
                        {team.abbreviation}
                      </span>
                    </div>

                    {/* Team Info */}
                    <div className="flex-1 min-w-0">
                      <p className="font-archivo font-bold text-sm truncate">{team.display_name}</p>
                      <p className="font-archivo text-xs text-muted truncate">{team.abbreviation}</p>
                    </div>

                    {/* Follow/Unfollow */}
                    <button
                      onClick={() => (isFollowed ? handleUnfollow(team.id) : handleFollow(team))}
                      disabled={isLoading}
                      className={`shrink-0 inline-flex items-center gap-1 px-3 py-2 border-2 border-navy font-archivo text-xs font-bold uppercase tracking-wider transition-colors ${
                        isFollowed
                          ? 'bg-navy text-cream hover:bg-red-700 hover:border-red-700'
                          : 'bg-cream text-navy hover:bg-accent hover:text-cream hover:border-accent'
                      } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {isFollowed ? (
                        <>
                          <UserMinus className="w-3 h-3" />
                          {isLoading ? '...' : 'Drop'}
                        </>
                      ) : (
                        <>
                          <UserPlus className="w-3 h-3" />
                          {isLoading ? '...' : 'Follow'}
                        </>
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
