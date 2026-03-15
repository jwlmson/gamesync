import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Save, Trash2, ArrowLeft } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import {
  getAllGames,
  getFollowedTeams,
  getGameOverride,
  saveGameOverride,
  deleteGameOverride,
  getEventTypes,
  type Game,
  type FollowedTeam,
  type GameOverrideEventConfig,
  type EventTypeDefinition,
} from '../api/client';
import Toggle from '../components/Toggle';
import Modal from '../components/Modal';

const EFFECT_TYPES = ['flash', 'pulse', 'solid', 'chase', 'rainbow', 'strobe'];

export default function GameOverrideEditorScreen() {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();

  // Load games to find the current one
  const { data: gamesData, loading: gamesLoading } = useApi(() => getAllGames(), []);
  const { data: followedData } = useApi(() => getFollowedTeams(), []);

  const games = gamesData?.games ?? [];
  const followedTeams = followedData?.teams ?? [];
  const game = games.find((g: Game) => g.id === gameId) ?? null;

  // Determine which followed team is in this game
  const followedIds = new Set(followedTeams.map((t: FollowedTeam) => t.team_id));
  const relevantTeamId =
    game && followedIds.has(game.home_team.id)
      ? game.home_team.id
      : game && followedIds.has(game.away_team.id)
        ? game.away_team.id
        : followedTeams[0]?.team_id ?? null;

  const relevantLeague = game?.league ?? followedTeams.find((t: FollowedTeam) => t.team_id === relevantTeamId)?.league ?? null;

  // Load existing override
  const {
    data: existingOverride,
    loading: overrideLoading,
    refetch: refetchOverride,
  } = useApi(
    () => (gameId && relevantTeamId ? getGameOverride(gameId, relevantTeamId) : Promise.resolve(null)),
    [gameId, relevantTeamId],
  );

  // Load event types for the league
  const { data: eventTypes } = useApi(
    () => (relevantLeague ? getEventTypes(relevantLeague) : Promise.resolve([])),
    [relevantLeague],
  );

  // Form state
  const [isEnabled, setIsEnabled] = useState(true);
  const [note, setNote] = useState('');
  const [eventConfigs, setEventConfigs] = useState<GameOverrideEventConfig[]>([]);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Initialize form from loaded override or defaults
  useEffect(() => {
    if (existingOverride) {
      setIsEnabled(existingOverride.is_enabled);
      setNote(existingOverride.note || '');
      setEventConfigs(existingOverride.event_configs ?? []);
    } else if (eventTypes && eventTypes.length > 0) {
      // Build default configs (all inherit)
      setEventConfigs(
        eventTypes.map((et: EventTypeDefinition) => ({
          event_type_id: et.id,
          inherit: true,
          light_effect_type: et.default_effect_type || 'flash',
          light_color_hex: '#D94833',
          target_light_entities: [],
          sound_asset_id: null,
          target_media_players: [],
          fire_ha_event: false,
          duration_seconds: 5,
        })),
      );
    }
  }, [existingOverride, eventTypes]);

  const updateEventConfig = useCallback(
    (eventTypeId: number, patch: Partial<GameOverrideEventConfig>) => {
      setEventConfigs((prev) =>
        prev.map((c) => (c.event_type_id === eventTypeId ? { ...c, ...patch } : c)),
      );
    },
    [],
  );

  const findEventType = (id: number) =>
    (eventTypes ?? []).find((et: EventTypeDefinition) => et.id === id);

  const handleSave = async () => {
    if (!gameId || !relevantTeamId) return;
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      await saveGameOverride(gameId, {
        followed_team_id: relevantTeamId,
        is_enabled: isEnabled,
        note,
        event_configs: eventConfigs,
      });
      setSaveSuccess(true);
      refetchOverride();
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e: any) {
      setSaveError(e.message || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!gameId || !relevantTeamId) return;
    setDeleting(true);
    try {
      await deleteGameOverride(gameId, relevantTeamId);
      setDeleteModalOpen(false);
      navigate('/games');
    } catch (e: any) {
      setSaveError(e.message || 'Delete failed');
    } finally {
      setDeleting(false);
    }
  };

  const loading = gamesLoading || overrideLoading;

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12 text-center">
        <div className="animate-pulse font-archivo text-sm uppercase tracking-wider text-muted">
          Loading override editor...
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Back link */}
      <Link
        to="/games"
        className="inline-flex items-center gap-2 font-archivo text-xs font-bold uppercase tracking-wider text-muted hover:text-accent mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Games
      </Link>

      {/* Game header */}
      {game ? (
        <div className="card-hard p-6 mb-8">
          <p className="font-archivo text-xs font-bold uppercase tracking-wider text-muted mb-2">
            {game.league} &middot; {new Date(game.start_time).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })}
          </p>
          <div className="flex items-center gap-4">
            <h2 className="font-rokkitt text-2xl font-bold uppercase tracking-wider">
              {game.home_team.display_name || game.home_team.name}
            </h2>
            <span className="font-rokkitt text-xl text-muted">vs</span>
            <h2 className="font-rokkitt text-2xl font-bold uppercase tracking-wider">
              {game.away_team.display_name || game.away_team.name}
            </h2>
          </div>
        </div>
      ) : (
        <div className="card-hard p-6 mb-8">
          <p className="font-archivo text-sm text-muted">Game not found (ID: {gameId})</p>
        </div>
      )}

      {/* Override settings */}
      <div className="card-hard p-6 mb-6">
        <h3 className="section-heading mb-4">Override Settings</h3>

        <div className="flex items-center justify-between mb-6">
          <Toggle
            checked={isEnabled}
            onChange={setIsEnabled}
            label="Enable Override"
          />
        </div>

        <div>
          <label className="block font-archivo text-xs font-bold uppercase tracking-wider text-muted mb-2">
            Note
          </label>
          <input
            type="text"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="e.g. Playoff game — extra effects"
            className="w-full border-2 border-navy bg-cream px-4 py-2 font-archivo text-sm focus:outline-none focus:border-accent"
          />
        </div>
      </div>

      {/* Event type overrides */}
      <div className="card-hard p-6 mb-6">
        <h3 className="section-heading mb-4">Event Effects</h3>

        {eventConfigs.length === 0 && (
          <p className="font-archivo text-sm text-muted">
            No event types available for this league.
          </p>
        )}

        <div className="space-y-4">
          {eventConfigs.map((config) => {
            const et = findEventType(config.event_type_id);
            return (
              <div
                key={config.event_type_id}
                className="border-2 border-navy p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-rokkitt text-base font-bold uppercase tracking-wider">
                    {et?.display_name ?? `Event #${config.event_type_id}`}
                  </h4>
                  <Toggle
                    checked={config.inherit}
                    onChange={(v) => updateEventConfig(config.event_type_id, { inherit: v })}
                    label="Inherit"
                  />
                </div>

                {config.inherit ? (
                  <p className="font-archivo text-xs text-muted uppercase tracking-wider">
                    Using team default configuration
                  </p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                    {/* Light effect type */}
                    <div>
                      <label className="block font-archivo text-xs font-bold uppercase tracking-wider text-muted mb-1">
                        Light Effect
                      </label>
                      <select
                        value={config.light_effect_type}
                        onChange={(e) =>
                          updateEventConfig(config.event_type_id, { light_effect_type: e.target.value })
                        }
                        className="w-full border-2 border-navy bg-cream px-3 py-2 font-archivo text-sm focus:outline-none focus:border-accent"
                      >
                        {EFFECT_TYPES.map((t) => (
                          <option key={t} value={t}>
                            {t.charAt(0).toUpperCase() + t.slice(1)}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Color */}
                    <div>
                      <label className="block font-archivo text-xs font-bold uppercase tracking-wider text-muted mb-1">
                        Color
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="color"
                          value={config.light_color_hex}
                          onChange={(e) =>
                            updateEventConfig(config.event_type_id, { light_color_hex: e.target.value })
                          }
                          className="w-10 h-10 border-2 border-navy cursor-pointer"
                        />
                        <input
                          type="text"
                          value={config.light_color_hex}
                          onChange={(e) =>
                            updateEventConfig(config.event_type_id, { light_color_hex: e.target.value })
                          }
                          className="flex-1 border-2 border-navy bg-cream px-3 py-2 font-archivo text-sm focus:outline-none focus:border-accent"
                        />
                      </div>
                    </div>

                    {/* Sound (placeholder ID) */}
                    <div>
                      <label className="block font-archivo text-xs font-bold uppercase tracking-wider text-muted mb-1">
                        Sound Asset ID
                      </label>
                      <input
                        type="number"
                        value={config.sound_asset_id ?? ''}
                        onChange={(e) =>
                          updateEventConfig(config.event_type_id, {
                            sound_asset_id: e.target.value ? Number(e.target.value) : null,
                          })
                        }
                        placeholder="None"
                        className="w-full border-2 border-navy bg-cream px-3 py-2 font-archivo text-sm focus:outline-none focus:border-accent"
                      />
                    </div>

                    {/* Duration */}
                    <div>
                      <label className="block font-archivo text-xs font-bold uppercase tracking-wider text-muted mb-1">
                        Duration (seconds)
                      </label>
                      <input
                        type="number"
                        min={1}
                        max={60}
                        value={config.duration_seconds}
                        onChange={(e) =>
                          updateEventConfig(config.event_type_id, { duration_seconds: Number(e.target.value) })
                        }
                        className="w-full border-2 border-navy bg-cream px-3 py-2 font-archivo text-sm focus:outline-none focus:border-accent"
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Feedback messages */}
      {saveError && (
        <div className="border-2 border-red-700 bg-red-50 p-4 mb-4">
          <p className="font-archivo text-sm font-bold text-red-700">{saveError}</p>
        </div>
      )}
      {saveSuccess && (
        <div className="border-2 border-green-700 bg-green-50 p-4 mb-4">
          <p className="font-archivo text-sm font-bold text-green-700">Override saved successfully.</p>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex items-center gap-4">
        <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : 'Save Override'}
        </button>

        {existingOverride && (
          <button onClick={() => setDeleteModalOpen(true)} className="btn-danger flex items-center gap-2">
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        )}
      </div>

      {/* Delete confirmation modal */}
      <Modal
        open={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        title="Delete Override?"
      >
        <p className="font-archivo text-sm text-muted mb-6">
          This will permanently remove the override for this game. The team's default effect
          configuration will apply instead.
        </p>
        <div className="flex items-center gap-3 justify-end">
          <button onClick={() => setDeleteModalOpen(false)} className="btn-secondary text-xs">
            Cancel
          </button>
          <button onClick={handleDelete} disabled={deleting} className="btn-danger text-xs flex items-center gap-2">
            <Trash2 className="w-4 h-4" />
            {deleting ? 'Deleting...' : 'Confirm Delete'}
          </button>
        </div>
      </Modal>
    </div>
  );
}
