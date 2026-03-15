import { useState, useRef, useEffect } from 'react';
import { Zap, OctagonX, Terminal, Activity } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { useSSE, type SSEEvent } from '../hooks/useSSE';
import {
  getFollowedTeams,
  getEventTypes,
  triggerEffect,
  emergencyStop,
  getConfig,
  type FollowedTeam,
  type EventTypeDefinition,
} from '../api/client';

function formatTimestamp(iso: string) {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export default function EffectTesterScreen() {
  const { data: followedData, loading: teamsLoading } = useApi(() => getFollowedTeams(), []);
  const { data: configData } = useApi(() => getConfig(), []);
  const { events, connected } = useSSE();

  const followedTeams = followedData?.teams ?? [];

  const [selectedTeamId, setSelectedTeamId] = useState<string>('');
  const [selectedEventType, setSelectedEventType] = useState<string>('');
  const [firing, setFiring] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [lastResult, setLastResult] = useState<string | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);

  const terminalRef = useRef<HTMLDivElement>(null);

  // Auto-select first team
  useEffect(() => {
    if (followedTeams.length > 0 && !selectedTeamId) {
      setSelectedTeamId(followedTeams[0].team_id);
    }
  }, [followedTeams, selectedTeamId]);

  // Determine league of selected team
  const selectedTeam = followedTeams.find((t: FollowedTeam) => t.team_id === selectedTeamId);
  const selectedLeague = selectedTeam?.league ?? null;

  // Load event types for selected league
  const { data: eventTypes, loading: eventsLoading } = useApi(
    () => (selectedLeague ? getEventTypes(selectedLeague) : Promise.resolve([])),
    [selectedLeague],
  );

  // Auto-select first event type
  useEffect(() => {
    if (eventTypes && eventTypes.length > 0 && !selectedEventType) {
      setSelectedEventType(eventTypes[0].event_code);
    }
  }, [eventTypes, selectedEventType]);

  // Reset event type when team changes
  useEffect(() => {
    setSelectedEventType('');
  }, [selectedTeamId]);

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [events]);

  const handleFire = async () => {
    if (!selectedTeamId || !selectedEventType) return;
    setFiring(true);
    setLastError(null);
    setLastResult(null);
    try {
      await triggerEffect(selectedTeamId, selectedEventType);
      setLastResult('Effect triggered successfully');
    } catch (e: any) {
      setLastError(e.message || 'Trigger failed');
    } finally {
      setFiring(false);
    }
  };

  const handleEmergencyStop = async () => {
    setStopping(true);
    setLastError(null);
    setLastResult(null);
    try {
      const res = await emergencyStop();
      setLastResult(`Emergency stop complete — ${res.stopped_count} effect(s) halted`);
    } catch (e: any) {
      setLastError(e.message || 'Emergency stop failed');
    } finally {
      setStopping(false);
    }
  };

  const brightnessLimit = configData?.effect_brightness_limit ?? 100;
  const maxDuration = configData?.effect_max_duration_seconds ?? 30;
  const globalMute = configData?.global_mute ?? false;

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Zap className="w-7 h-7 text-accent" />
        <h2 className="font-rokkitt text-2xl font-bold uppercase tracking-wider">
          Effect Tester
        </h2>
        <div className="ml-auto flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-status' : 'bg-red-500'}`} />
          <span className="font-archivo text-xs font-bold uppercase tracking-wider text-muted">
            {connected ? 'SSE Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left column — controls */}
        <div>
          {/* Team selector */}
          <div className="card-hard p-6 mb-6">
            <h3 className="section-heading text-base mb-4">Configuration</h3>

            <div className="mb-4">
              <label className="block font-archivo text-xs font-bold uppercase tracking-wider text-muted mb-2">
                Team
              </label>
              <select
                value={selectedTeamId}
                onChange={(e) => setSelectedTeamId(e.target.value)}
                disabled={teamsLoading}
                className="w-full border-2 border-navy bg-cream px-4 py-2 font-archivo text-sm focus:outline-none focus:border-accent"
              >
                <option value="">Select a team...</option>
                {followedTeams.map((t: FollowedTeam) => (
                  <option key={t.team_id} value={t.team_id}>
                    {t.team_id} ({t.league})
                  </option>
                ))}
              </select>
            </div>

            <div className="mb-4">
              <label className="block font-archivo text-xs font-bold uppercase tracking-wider text-muted mb-2">
                Event Type
              </label>
              <select
                value={selectedEventType}
                onChange={(e) => setSelectedEventType(e.target.value)}
                disabled={eventsLoading || !selectedTeamId}
                className="w-full border-2 border-navy bg-cream px-4 py-2 font-archivo text-sm focus:outline-none focus:border-accent"
              >
                <option value="">Select an event...</option>
                {(eventTypes ?? []).map((et: EventTypeDefinition) => (
                  <option key={et.id} value={et.event_code}>
                    {et.display_name} ({et.event_code})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Volume / brightness indicators */}
          <div className="card-hard p-6 mb-6">
            <h3 className="section-heading text-base mb-4">Limits</h3>
            <div className="space-y-3">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="font-archivo text-xs font-bold uppercase tracking-wider text-muted">
                    Brightness Limit
                  </span>
                  <span className="font-archivo text-xs font-bold text-navy">{brightnessLimit}%</span>
                </div>
                <div className="w-full h-3 border-2 border-navy bg-cream">
                  <div
                    className="h-full bg-accent transition-all"
                    style={{ width: `${brightnessLimit}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="font-archivo text-xs font-bold uppercase tracking-wider text-muted">
                    Max Duration
                  </span>
                  <span className="font-archivo text-xs font-bold text-navy">{maxDuration}s</span>
                </div>
                <div className="w-full h-3 border-2 border-navy bg-cream">
                  <div
                    className="h-full bg-navy transition-all"
                    style={{ width: `${Math.min((maxDuration / 60) * 100, 100)}%` }}
                  />
                </div>
              </div>
              {globalMute && (
                <div className="border-2 border-accent bg-accent/10 px-3 py-2">
                  <span className="font-archivo text-xs font-bold uppercase tracking-wider text-accent">
                    Global Mute Active
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-4">
            <button
              onClick={handleFire}
              disabled={firing || !selectedTeamId || !selectedEventType}
              className="btn-primary flex items-center gap-2 flex-1 justify-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Zap className="w-5 h-5" />
              {firing ? 'Firing...' : 'Fire Effect'}
            </button>
            <button
              onClick={handleEmergencyStop}
              disabled={stopping}
              className="btn-danger flex items-center gap-2 flex-1 justify-center"
            >
              <OctagonX className="w-5 h-5" />
              {stopping ? 'Stopping...' : 'Emergency Stop'}
            </button>
          </div>

          {/* Feedback */}
          {lastResult && (
            <div className="border-2 border-green-700 bg-green-50 p-3 mt-4">
              <p className="font-archivo text-sm font-bold text-green-700">{lastResult}</p>
            </div>
          )}
          {lastError && (
            <div className="border-2 border-red-700 bg-red-50 p-3 mt-4">
              <p className="font-archivo text-sm font-bold text-red-700">{lastError}</p>
            </div>
          )}
        </div>

        {/* Right column — execution log */}
        <div>
          <div className="card-hard overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 border-b-2 border-navy bg-navy">
              <Terminal className="w-4 h-4 text-cream" />
              <span className="font-archivo text-xs font-bold uppercase tracking-wider text-cream">
                Execution Log
              </span>
              <Activity className="w-4 h-4 text-green-400 ml-auto" />
              <span className="font-archivo text-xs text-green-400">
                {events.length} events
              </span>
            </div>

            <div
              ref={terminalRef}
              className="bg-[#0d1117] text-green-400 font-mono text-xs p-4 h-[500px] overflow-y-auto"
            >
              {events.length === 0 ? (
                <div className="text-gray-500">
                  <p>$ awaiting events...</p>
                  <p className="mt-1 animate-pulse">_</p>
                </div>
              ) : (
                events
                  .slice()
                  .reverse()
                  .map((evt: SSEEvent, i: number) => (
                    <div key={`${evt.id}-${i}`} className="mb-2 leading-relaxed">
                      <span className="text-gray-500">[{formatTimestamp(evt.timestamp)}]</span>{' '}
                      <span
                        className={
                          evt.event_type === 'effect_triggered'
                            ? 'text-yellow-400'
                            : evt.event_type === 'emergency_stop'
                              ? 'text-red-400'
                              : evt.event_type === 'score_change'
                                ? 'text-green-400'
                                : 'text-blue-400'
                        }
                      >
                        {evt.event_type}
                      </span>
                      {evt.team_id && <span className="text-gray-400"> team={evt.team_id}</span>}
                      {evt.game_id && <span className="text-gray-400"> game={evt.game_id}</span>}
                      {evt.league && <span className="text-gray-400"> league={evt.league}</span>}
                      {evt.details && (
                        <div className="text-gray-500 ml-4 mt-0.5">
                          {JSON.stringify(evt.details)}
                        </div>
                      )}
                    </div>
                  ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
