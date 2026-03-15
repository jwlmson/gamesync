import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Users, Plus, Settings, Trash2, GripVertical } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import {
  getFollowedTeams,
  getTeams,
  unfollowTeam,
  updateFollowedTeam,
  type FollowedTeam,
  type TeamInfo,
} from '../api/client';
import Toggle from '../components/Toggle';
import Modal from '../components/Modal';

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

export default function TeamManagementScreen() {
  const followed = useApi(() => getFollowedTeams(), []);
  const allTeams = useApi(() => getTeams(), []);

  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const followedTeams: FollowedTeam[] = followed.data?.teams ?? [];
  const teamInfoMap: Record<string, TeamInfo> = {};
  if (allTeams.data?.teams) {
    for (const league of Object.values(allTeams.data.teams)) {
      for (const team of league) {
        teamInfoMap[team.id] = team;
      }
    }
  }

  const handleToggleAutoSync = async (teamId: string, current: boolean) => {
    try {
      await updateFollowedTeam(teamId, { auto_sync_enabled: !current });
      followed.refetch();
    } catch {
      // silent
    }
  };

  const handleDelayChange = async (teamId: string, delay: number) => {
    try {
      await updateFollowedTeam(teamId, { delay_seconds: delay });
    } catch {
      // silent
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await unfollowTeam(deleteTarget);
      setDeleteTarget(null);
      followed.refetch();
    } catch {
      // silent
    } finally {
      setDeleting(false);
    }
  };

  const deleteTeamInfo = deleteTarget ? teamInfoMap[deleteTarget] : null;

  return (
    <div className="max-w-[1920px] mx-auto px-6 py-8">
      {/* Page Title */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 border-2 border-navy bg-accent flex items-center justify-center">
            <Users className="w-5 h-5 text-cream" />
          </div>
          <h2 className="font-rokkitt text-3xl font-bold uppercase tracking-wider">Team Roster</h2>
        </div>
        <Link to="/teams/discover" className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Scout New Talent
        </Link>
      </div>

      {followed.loading || allTeams.loading ? (
        <LoadingPulse />
      ) : followed.error ? (
        <ErrorBox message={followed.error} />
      ) : followedTeams.length === 0 ? (
        <div className="card-hard p-8 text-center">
          <Users className="w-12 h-12 mx-auto mb-4 text-muted" />
          <h3 className="font-rokkitt text-xl font-bold uppercase tracking-wider mb-2">
            Empty Roster
          </h3>
          <p className="font-archivo text-sm text-muted mb-6">
            You haven't followed any teams yet. Start scouting to build your roster.
          </p>
          <Link to="/teams/discover" className="btn-primary inline-block">
            Scout New Talent
          </Link>
        </div>
      ) : (
        <div className="card-hard overflow-hidden">
          {/* Table Header */}
          <div className="hidden md:grid grid-cols-[40px_1fr_100px_80px_120px_100px_80px_80px] gap-4 px-4 py-3 bg-navy text-cream">
            <span />
            <span className="font-archivo text-xs font-bold uppercase tracking-wider">Team</span>
            <span className="font-archivo text-xs font-bold uppercase tracking-wider">League</span>
            <span className="font-archivo text-xs font-bold uppercase tracking-wider">Rank</span>
            <span className="font-archivo text-xs font-bold uppercase tracking-wider">Auto-Sync</span>
            <span className="font-archivo text-xs font-bold uppercase tracking-wider">Delay (s)</span>
            <span className="font-archivo text-xs font-bold uppercase tracking-wider">Config</span>
            <span className="font-archivo text-xs font-bold uppercase tracking-wider">Remove</span>
          </div>

          {/* Team Rows */}
          <div className="divide-y divide-navy/10">
            {followedTeams
              .sort((a, b) => a.priority_rank - b.priority_rank)
              .map((ft) => {
                const info = teamInfoMap[ft.team_id];
                return (
                  <div
                    key={ft.team_id}
                    className="grid grid-cols-1 md:grid-cols-[40px_1fr_100px_80px_120px_100px_80px_80px] gap-4 px-4 py-3 items-center hover:bg-navy/5 transition-colors"
                  >
                    {/* Grip */}
                    <div className="hidden md:flex justify-center">
                      <GripVertical className="w-4 h-4 text-muted cursor-grab" />
                    </div>

                    {/* Team Name */}
                    <div className="flex items-center gap-3">
                      {info?.primary_color && (
                        <div
                          className="w-6 h-6 border-2 border-navy shrink-0"
                          style={{ backgroundColor: info.primary_color }}
                        />
                      )}
                      <span className="font-archivo font-bold text-sm">
                        {info?.display_name ?? ft.team_id}
                      </span>
                    </div>

                    {/* League Badge */}
                    <div>
                      <span className="font-archivo text-xs font-bold uppercase tracking-wider bg-navy/10 px-2 py-1 border border-navy/20">
                        {ft.league}
                      </span>
                    </div>

                    {/* Priority Rank */}
                    <div>
                      <span className="font-rokkitt font-bold text-lg">#{ft.priority_rank}</span>
                    </div>

                    {/* Auto-Sync Toggle */}
                    <div>
                      <Toggle
                        checked={ft.auto_sync_enabled}
                        onChange={() => handleToggleAutoSync(ft.team_id, ft.auto_sync_enabled)}
                      />
                    </div>

                    {/* Delay */}
                    <div>
                      <input
                        type="number"
                        min={0}
                        defaultValue={ft.delay_seconds}
                        onBlur={(e) => {
                          const val = parseInt(e.target.value, 10);
                          if (!isNaN(val) && val !== ft.delay_seconds) {
                            handleDelayChange(ft.team_id, val);
                          }
                        }}
                        className="w-20 px-2 py-1 border-2 border-navy bg-cream font-archivo text-sm text-center focus:outline-none focus:border-accent"
                      />
                    </div>

                    {/* Configure */}
                    <div>
                      <Link
                        to={`/teams/${ft.team_id}/config`}
                        className="inline-flex items-center justify-center w-8 h-8 border-2 border-navy hover:bg-navy hover:text-cream transition-colors"
                        title="Configure effects"
                      >
                        <Settings className="w-4 h-4" />
                      </Link>
                    </div>

                    {/* Delete */}
                    <div>
                      <button
                        onClick={() => setDeleteTarget(ft.team_id)}
                        className="inline-flex items-center justify-center w-8 h-8 border-2 border-navy hover:bg-red-700 hover:border-red-700 hover:text-cream transition-colors"
                        title="Remove team"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        title="Confirm Removal"
      >
        <p className="font-archivo text-sm mb-6">
          Are you sure you want to remove{' '}
          <strong>{deleteTeamInfo?.display_name ?? deleteTarget}</strong> from your roster?
          All effect configurations for this team will be lost.
        </p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={() => setDeleteTarget(null)}
            className="btn-secondary text-sm"
            disabled={deleting}
          >
            Cancel
          </button>
          <button
            onClick={handleDelete}
            className="btn-danger text-sm"
            disabled={deleting}
          >
            {deleting ? 'Removing...' : 'Remove Team'}
          </button>
        </div>
      </Modal>
    </div>
  );
}
