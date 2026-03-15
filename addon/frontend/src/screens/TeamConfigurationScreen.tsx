import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { ChevronDown, ChevronRight, Lightbulb, Volume2, Zap, Copy } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import {
  getTeamEventConfigs,
  updateTeamEventConfigs,
  copyTeamEventConfigs,
  getEventTypes,
  getFollowedTeams,
  getTeams,
  triggerEffect,
  getSounds,
  type TeamEventConfig,
  type EventTypeDefinition,
  type FollowedTeam,
  type TeamInfo,
  type SoundAsset,
} from '../api/client';
import Modal from '../components/Modal';
import Toggle from '../components/Toggle';

const EFFECT_TYPES = ['flash', 'pulse', 'solid', 'rainbow', 'strobe', 'none'] as const;

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

interface EventRowConfig {
  event_type_id: number;
  light_effect_type: string;
  light_color_hex: string;
  sound_asset_id: number | null;
  fire_ha_event: boolean;
  duration_seconds: number;
  target_light_entities: string[];
  target_media_players: string[];
}

export default function TeamConfigurationScreen() {
  const { teamId } = useParams<{ teamId: string }>();

  const followed = useApi(() => getFollowedTeams(), []);
  const allTeams = useApi(() => getTeams(), []);
  const configs = useApi(() => getTeamEventConfigs(teamId!), [teamId]);
  const sounds = useApi(() => getSounds(), []);

  const [eventTypes, setEventTypes] = useState<EventTypeDefinition[]>([]);
  const [eventTypesLoading, setEventTypesLoading] = useState(true);
  const [localConfigs, setLocalConfigs] = useState<Record<number, EventRowConfig>>({});
  const [expandedEvents, setExpandedEvents] = useState<Set<number>>(new Set());
  const [copyModalOpen, setCopyModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [testingEvent, setTestingEvent] = useState<string | null>(null);

  // Resolve team info
  const teamInfoMap: Record<string, TeamInfo> = {};
  if (allTeams.data?.teams) {
    for (const league of Object.values(allTeams.data.teams)) {
      for (const team of league) {
        teamInfoMap[team.id] = team;
      }
    }
  }
  const teamInfo = teamId ? teamInfoMap[teamId] : null;
  const followedTeam = (followed.data?.teams ?? []).find((ft: FollowedTeam) => ft.team_id === teamId);
  const league = followedTeam?.league ?? teamInfo?.league;

  // Load event types when league is known
  useEffect(() => {
    if (!league) return;
    setEventTypesLoading(true);
    getEventTypes(league)
      .then((types) => setEventTypes(types))
      .catch(() => setEventTypes([]))
      .finally(() => setEventTypesLoading(false));
  }, [league]);

  // Initialize local configs from API data
  useEffect(() => {
    if (!configs.data?.configs || eventTypes.length === 0) return;
    const map: Record<number, EventRowConfig> = {};

    for (const et of eventTypes) {
      const existing = configs.data.configs.find((c: TeamEventConfig) => c.event_type_id === et.id);
      map[et.id] = existing
        ? {
            event_type_id: et.id,
            light_effect_type: existing.light_effect_type,
            light_color_hex: existing.light_color_hex,
            sound_asset_id: existing.sound_asset_id,
            fire_ha_event: existing.fire_ha_event,
            duration_seconds: existing.duration_seconds,
            target_light_entities: existing.target_light_entities,
            target_media_players: existing.target_media_players,
          }
        : {
            event_type_id: et.id,
            light_effect_type: et.default_effect_type || 'flash',
            light_color_hex: teamInfo?.primary_color ?? '#D94833',
            sound_asset_id: null,
            fire_ha_event: false,
            duration_seconds: 5,
            target_light_entities: [],
            target_media_players: [],
          };
    }
    setLocalConfigs(map);
  }, [configs.data, eventTypes, teamInfo]);

  const toggleExpand = (id: number) => {
    setExpandedEvents((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const updateLocalConfig = (eventTypeId: number, patch: Partial<EventRowConfig>) => {
    setLocalConfigs((prev) => ({
      ...prev,
      [eventTypeId]: { ...prev[eventTypeId], ...patch },
    }));
  };

  const handleSave = async () => {
    if (!teamId) return;
    setSaving(true);
    setSaveMessage(null);
    try {
      const payload = Object.values(localConfigs).map(({ event_type_id, ...rest }) => ({
        event_type_id,
        ...rest,
      }));
      await updateTeamEventConfigs(teamId, payload);
      setSaveMessage('Saved successfully.');
      configs.refetch();
    } catch (e: any) {
      setSaveMessage(`Save failed: ${e.message}`);
    } finally {
      setSaving(false);
      setTimeout(() => setSaveMessage(null), 3000);
    }
  };

  const handleCopyFrom = async (fromTeamId: string) => {
    if (!teamId) return;
    try {
      await copyTeamEventConfigs(teamId, fromTeamId);
      configs.refetch();
      setCopyModalOpen(false);
    } catch {
      // silent
    }
  };

  const handleTest = async (eventCode: string) => {
    if (!teamId) return;
    setTestingEvent(eventCode);
    try {
      await triggerEffect(teamId, eventCode);
    } catch {
      // silent
    } finally {
      setTimeout(() => setTestingEvent(null), 1000);
    }
  };

  const otherFollowed = (followed.data?.teams ?? []).filter(
    (ft: FollowedTeam) => ft.team_id !== teamId
  );
  const soundList: SoundAsset[] = sounds.data ?? [];

  const isLoading = followed.loading || allTeams.loading || configs.loading || eventTypesLoading;
  const error = followed.error || allTeams.error || configs.error;

  return (
    <div className="max-w-[1920px] mx-auto px-6 py-8">
      {/* Page Title */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          {teamInfo?.primary_color && (
            <div
              className="w-10 h-10 border-2 border-navy flex items-center justify-center"
              style={{ backgroundColor: teamInfo.primary_color }}
            >
              <span className="font-rokkitt font-bold text-cream text-xs">
                {teamInfo.abbreviation}
              </span>
            </div>
          )}
          <div>
            <h2 className="font-rokkitt text-3xl font-bold uppercase tracking-wider">
              {teamInfo?.display_name ?? teamId}
            </h2>
            {league && (
              <span className="font-archivo text-xs font-bold uppercase tracking-wider text-muted bg-navy/10 px-2 py-0.5 border border-navy/20">
                {league}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setCopyModalOpen(true)}
            className="btn-secondary flex items-center gap-2 text-sm"
            disabled={otherFollowed.length === 0}
          >
            <Copy className="w-4 h-4" />
            Copy Config From...
          </button>
          <button onClick={handleSave} className="btn-primary text-sm" disabled={saving}>
            {saving ? 'Saving...' : 'Save All'}
          </button>
        </div>
      </div>

      {saveMessage && (
        <div
          className={`card-hard p-3 mb-6 ${
            saveMessage.startsWith('Save failed') ? 'border-accent' : 'border-green-status'
          }`}
        >
          <p className="font-archivo text-sm font-bold uppercase">{saveMessage}</p>
        </div>
      )}

      {isLoading ? (
        <LoadingPulse />
      ) : error ? (
        <ErrorBox message={error} />
      ) : eventTypes.length === 0 ? (
        <div className="card-hard p-8 text-center">
          <p className="font-archivo text-sm text-muted">No event types defined for this league.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {eventTypes.map((et) => {
            const isExpanded = expandedEvents.has(et.id);
            const config = localConfigs[et.id];
            if (!config) return null;

            return (
              <div key={et.id} className="card-hard">
                {/* Collapsible Header */}
                <button
                  onClick={() => toggleExpand(et.id)}
                  className="w-full flex items-center justify-between px-4 py-3 hover:bg-navy/5 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-muted" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-muted" />
                    )}
                    <span className="font-archivo font-bold text-sm uppercase tracking-wider">
                      {et.display_name}
                    </span>
                    {et.points_value > 0 && (
                      <span className="font-archivo text-xs text-muted">
                        ({et.points_value} pts)
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className="w-4 h-4 border border-navy"
                      style={{ backgroundColor: config.light_color_hex }}
                    />
                    <span className="font-archivo text-xs text-muted uppercase">
                      {config.light_effect_type}
                    </span>
                  </div>
                </button>

                {/* Expanded Config */}
                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-navy/10 pt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {/* Light Effect Type */}
                      <div>
                        <label className="flex items-center gap-2 mb-2">
                          <Lightbulb className="w-4 h-4 text-accent" />
                          <span className="font-archivo text-xs font-bold uppercase tracking-wider">
                            Light Effect
                          </span>
                        </label>
                        <select
                          value={config.light_effect_type}
                          onChange={(e) =>
                            updateLocalConfig(et.id, { light_effect_type: e.target.value })
                          }
                          className="w-full px-3 py-2 border-2 border-navy bg-cream font-archivo text-sm focus:outline-none focus:border-accent"
                        >
                          {EFFECT_TYPES.map((t) => (
                            <option key={t} value={t}>
                              {t.charAt(0).toUpperCase() + t.slice(1)}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Color Picker */}
                      <div>
                        <label className="flex items-center gap-2 mb-2">
                          <span className="font-archivo text-xs font-bold uppercase tracking-wider">
                            Color
                          </span>
                        </label>
                        <div className="flex items-center gap-3">
                          <input
                            type="color"
                            value={config.light_color_hex}
                            onChange={(e) =>
                              updateLocalConfig(et.id, { light_color_hex: e.target.value })
                            }
                            className="w-10 h-10 border-2 border-navy cursor-pointer"
                          />
                          <input
                            type="text"
                            value={config.light_color_hex}
                            onChange={(e) =>
                              updateLocalConfig(et.id, { light_color_hex: e.target.value })
                            }
                            className="flex-1 px-3 py-2 border-2 border-navy bg-cream font-archivo text-sm font-mono focus:outline-none focus:border-accent"
                          />
                        </div>
                      </div>

                      {/* Sound Selector */}
                      <div>
                        <label className="flex items-center gap-2 mb-2">
                          <Volume2 className="w-4 h-4 text-accent" />
                          <span className="font-archivo text-xs font-bold uppercase tracking-wider">
                            Sound
                          </span>
                        </label>
                        <select
                          value={config.sound_asset_id ?? ''}
                          onChange={(e) =>
                            updateLocalConfig(et.id, {
                              sound_asset_id: e.target.value ? Number(e.target.value) : null,
                            })
                          }
                          className="w-full px-3 py-2 border-2 border-navy bg-cream font-archivo text-sm focus:outline-none focus:border-accent"
                        >
                          <option value="">None</option>
                          {soundList.map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.name}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Duration Slider */}
                      <div>
                        <label className="flex items-center gap-2 mb-2">
                          <Zap className="w-4 h-4 text-accent" />
                          <span className="font-archivo text-xs font-bold uppercase tracking-wider">
                            Duration: {config.duration_seconds}s
                          </span>
                        </label>
                        <input
                          type="range"
                          min={1}
                          max={30}
                          value={config.duration_seconds}
                          onChange={(e) =>
                            updateLocalConfig(et.id, { duration_seconds: Number(e.target.value) })
                          }
                          className="w-full accent-accent"
                        />
                        <div className="flex justify-between font-archivo text-[10px] text-muted">
                          <span>1s</span>
                          <span>30s</span>
                        </div>
                      </div>

                      {/* Fire HA Event Toggle */}
                      <div className="flex items-end">
                        <Toggle
                          checked={config.fire_ha_event}
                          onChange={(checked) =>
                            updateLocalConfig(et.id, { fire_ha_event: checked })
                          }
                          label="Fire HA Event"
                        />
                      </div>

                      {/* Test Button */}
                      <div className="flex items-end">
                        <button
                          onClick={() => handleTest(et.event_code)}
                          disabled={testingEvent === et.event_code}
                          className={`btn-secondary text-sm flex items-center gap-2 ${
                            testingEvent === et.event_code ? 'opacity-50' : ''
                          }`}
                        >
                          <Zap className="w-4 h-4" />
                          {testingEvent === et.event_code ? 'Testing...' : 'Test'}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Copy From Modal */}
      <Modal open={copyModalOpen} onClose={() => setCopyModalOpen(false)} title="Copy Config From">
        <p className="font-archivo text-sm text-muted mb-4">
          Select a team to copy all event configurations from. This will overwrite the current config.
        </p>
        {otherFollowed.length === 0 ? (
          <p className="font-archivo text-sm text-muted">No other followed teams available.</p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {otherFollowed.map((ft: FollowedTeam) => {
              const info = teamInfoMap[ft.team_id];
              return (
                <button
                  key={ft.team_id}
                  onClick={() => handleCopyFrom(ft.team_id)}
                  className="w-full flex items-center gap-3 p-3 border-2 border-navy hover:bg-navy hover:text-cream transition-colors text-left"
                >
                  {info?.primary_color && (
                    <div
                      className="w-8 h-8 border-2 border-navy shrink-0 flex items-center justify-center"
                      style={{ backgroundColor: info.primary_color }}
                    >
                      <span className="font-rokkitt font-bold text-cream text-[10px]">
                        {info.abbreviation}
                      </span>
                    </div>
                  )}
                  <div>
                    <p className="font-archivo font-bold text-sm">
                      {info?.display_name ?? ft.team_id}
                    </p>
                    <p className="font-archivo text-xs text-muted">{ft.league}</p>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </Modal>
    </div>
  );
}
