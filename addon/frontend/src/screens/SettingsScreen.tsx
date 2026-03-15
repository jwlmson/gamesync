import { useState, useEffect } from 'react';
import { Settings, Radio, Lightbulb, Speaker, Shield } from 'lucide-react';
import { getConfig, updateConfig, type AppConfig } from '../api/client';
import { useApi } from '../hooks/useApi';
import Toggle from '../components/Toggle';

const LEAGUES = [
  { code: 'NHL', label: 'NHL', sport: 'Hockey' },
  { code: 'NFL', label: 'NFL', sport: 'Football' },
  { code: 'NBA', label: 'NBA', sport: 'Basketball' },
  { code: 'MLB', label: 'MLB', sport: 'Baseball' },
  { code: 'MLS', label: 'MLS', sport: 'Soccer' },
];

export default function SettingsScreen() {
  const { data: config, loading, error, refetch } = useApi(() => getConfig(), []);

  // Local form state, synced from fetched config
  const [form, setForm] = useState<Partial<AppConfig>>({});
  const [leagueToggles, setLeagueToggles] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [stopping, setStopping] = useState(false);

  useEffect(() => {
    if (config) {
      setForm({
        poll_interval_live: config.poll_interval_live,
        poll_interval_gameday: config.poll_interval_gameday,
        poll_interval_idle: config.poll_interval_idle,
        effect_max_duration_seconds: config.effect_max_duration_seconds,
        effect_brightness_limit: config.effect_brightness_limit,
        default_audio_entity: config.default_audio_entity ?? '',
        tts_entity: config.tts_entity ?? '',
        default_delay_seconds: config.default_delay_seconds,
      });
      // Initialize league toggles (all enabled by default since config doesn't store per-league)
      const toggles: Record<string, boolean> = {};
      LEAGUES.forEach((l) => (toggles[l.code] = true));
      setLeagueToggles(toggles);
    }
  }, [config]);

  const updateField = <K extends keyof AppConfig>(key: K, value: AppConfig[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    try {
      await updateConfig(form);
      setSaveSuccess(true);
      refetch();
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e: any) {
      setSaveError(e.message || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleEmergencyStop = async () => {
    setStopping(true);
    try {
      const { emergencyStop } = await import('../api/client');
      await emergencyStop();
    } catch {
      // Emergency stop should fail silently in UI
    } finally {
      setStopping(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-[1920px] mx-auto px-6 py-8">
        <div className="card-hard p-12 text-center">
          <p className="font-archivo text-sm font-bold text-muted uppercase tracking-wider animate-pulse">
            Loading configuration...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-[1920px] mx-auto px-6 py-8">
        <div className="card-hard p-8 text-center">
          <p className="font-archivo text-sm font-bold text-red-700 uppercase tracking-wider mb-4">
            {error}
          </p>
          <button onClick={refetch} className="btn-secondary text-xs">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1920px] mx-auto px-6 py-8">
      {/* Page Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 border-2 border-navy bg-navy flex items-center justify-center">
          <Settings className="w-6 h-6 text-cream" />
        </div>
        <div>
          <h2 className="font-rokkitt text-3xl font-bold text-navy uppercase tracking-wide">
            Settings
          </h2>
          <p className="font-archivo text-sm text-muted uppercase tracking-wider">
            System configuration and preferences
          </p>
        </div>
      </div>

      <div className="space-y-8 max-w-3xl">
        {/* ── Data Sources ── */}
        <section className="card-hard p-6">
          <div className="flex items-center gap-3 mb-6">
            <Radio className="w-5 h-5 text-accent" />
            <h3 className="section-heading">Data Sources</h3>
          </div>

          {/* League Toggles */}
          <div className="mb-6">
            <p className="font-archivo text-xs font-bold text-muted uppercase tracking-wider mb-3">
              Enabled Leagues
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {LEAGUES.map((league) => (
                <div key={league.code} className="flex items-center justify-between p-3 border-2 border-navy/20">
                  <div>
                    <p className="font-archivo text-sm font-bold text-navy">{league.label}</p>
                    <p className="font-archivo text-xs text-muted">{league.sport}</p>
                  </div>
                  <Toggle
                    checked={leagueToggles[league.code] ?? true}
                    onChange={(checked) =>
                      setLeagueToggles((prev) => ({ ...prev, [league.code]: checked }))
                    }
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Polling Intervals */}
          <div>
            <p className="font-archivo text-xs font-bold text-muted uppercase tracking-wider mb-3">
              Polling Intervals (seconds)
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="font-archivo text-xs font-bold text-navy uppercase tracking-wider block mb-1">
                  Live
                </label>
                <input
                  type="number"
                  min={1}
                  max={300}
                  value={form.poll_interval_live ?? ''}
                  onChange={(e) => updateField('poll_interval_live', Number(e.target.value))}
                  className="w-full border-2 border-navy px-3 py-2 bg-cream font-archivo text-sm text-navy focus:outline-none focus:border-accent"
                />
              </div>
              <div>
                <label className="font-archivo text-xs font-bold text-navy uppercase tracking-wider block mb-1">
                  Gameday
                </label>
                <input
                  type="number"
                  min={1}
                  max={3600}
                  value={form.poll_interval_gameday ?? ''}
                  onChange={(e) => updateField('poll_interval_gameday', Number(e.target.value))}
                  className="w-full border-2 border-navy px-3 py-2 bg-cream font-archivo text-sm text-navy focus:outline-none focus:border-accent"
                />
              </div>
              <div>
                <label className="font-archivo text-xs font-bold text-navy uppercase tracking-wider block mb-1">
                  Idle
                </label>
                <input
                  type="number"
                  min={1}
                  max={7200}
                  value={form.poll_interval_idle ?? ''}
                  onChange={(e) => updateField('poll_interval_idle', Number(e.target.value))}
                  className="w-full border-2 border-navy px-3 py-2 bg-cream font-archivo text-sm text-navy focus:outline-none focus:border-accent"
                />
              </div>
            </div>
          </div>
        </section>

        {/* ── Global Effect Limits ── */}
        <section className="card-hard p-6">
          <div className="flex items-center gap-3 mb-6">
            <Lightbulb className="w-5 h-5 text-accent" />
            <h3 className="section-heading">Global Effect Limits</h3>
          </div>

          <div className="space-y-6">
            {/* Max Effect Duration */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="font-archivo text-xs font-bold text-navy uppercase tracking-wider">
                  Max Effect Duration
                </label>
                <span className="font-archivo text-sm font-bold text-accent">
                  {form.effect_max_duration_seconds ?? 0}s
                </span>
              </div>
              <input
                type="range"
                min={1}
                max={60}
                value={form.effect_max_duration_seconds ?? 10}
                onChange={(e) => updateField('effect_max_duration_seconds', Number(e.target.value))}
                className="w-full h-2 appearance-none bg-navy/20 cursor-pointer accent-accent"
              />
              <div className="flex justify-between mt-1">
                <span className="font-archivo text-xs text-muted">1s</span>
                <span className="font-archivo text-xs text-muted">60s</span>
              </div>
            </div>

            {/* Brightness Limit */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="font-archivo text-xs font-bold text-navy uppercase tracking-wider">
                  Brightness Limit
                </label>
                <span className="font-archivo text-sm font-bold text-accent">
                  {form.effect_brightness_limit ?? 0}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={255}
                value={form.effect_brightness_limit ?? 255}
                onChange={(e) => updateField('effect_brightness_limit', Number(e.target.value))}
                className="w-full h-2 appearance-none bg-navy/20 cursor-pointer accent-accent"
              />
              <div className="flex justify-between mt-1">
                <span className="font-archivo text-xs text-muted">0</span>
                <span className="font-archivo text-xs text-muted">255</span>
              </div>
            </div>
          </div>
        </section>

        {/* ── Audio ── */}
        <section className="card-hard p-6">
          <div className="flex items-center gap-3 mb-6">
            <Speaker className="w-5 h-5 text-accent" />
            <h3 className="section-heading">Audio</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="font-archivo text-xs font-bold text-navy uppercase tracking-wider block mb-1">
                Default Media Player Entity
              </label>
              <input
                type="text"
                placeholder="media_player.living_room"
                value={(form.default_audio_entity as string) ?? ''}
                onChange={(e) => updateField('default_audio_entity', e.target.value || null)}
                className="w-full border-2 border-navy px-3 py-2 bg-cream font-archivo text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:border-accent"
              />
            </div>
            <div>
              <label className="font-archivo text-xs font-bold text-navy uppercase tracking-wider block mb-1">
                TTS Entity
              </label>
              <input
                type="text"
                placeholder="tts.google_translate_say"
                value={(form.tts_entity as string) ?? ''}
                onChange={(e) => updateField('tts_entity', e.target.value || null)}
                className="w-full border-2 border-navy px-3 py-2 bg-cream font-archivo text-sm text-navy placeholder:text-muted/50 focus:outline-none focus:border-accent"
              />
            </div>
          </div>
        </section>

        {/* ── Advanced ── */}
        <section className="card-hard p-6">
          <div className="flex items-center gap-3 mb-6">
            <Shield className="w-5 h-5 text-accent" />
            <h3 className="section-heading">Advanced</h3>
          </div>

          <div className="space-y-6">
            <div>
              <label className="font-archivo text-xs font-bold text-navy uppercase tracking-wider block mb-1">
                Default Delay (seconds)
              </label>
              <input
                type="number"
                min={0}
                max={120}
                value={form.default_delay_seconds ?? ''}
                onChange={(e) => updateField('default_delay_seconds', Number(e.target.value))}
                className="w-full max-w-xs border-2 border-navy px-3 py-2 bg-cream font-archivo text-sm text-navy focus:outline-none focus:border-accent"
              />
              <p className="font-archivo text-xs text-muted mt-1">
                Delay between event detection and effect trigger to prevent spoilers.
              </p>
            </div>

            <div className="pt-2 border-t-2 border-navy/10">
              <p className="font-archivo text-xs font-bold text-navy uppercase tracking-wider mb-2">
                Emergency Stop
              </p>
              <p className="font-archivo text-xs text-muted mb-3">
                Immediately stop all active effects, lights, and audio playback.
              </p>
              <button
                onClick={handleEmergencyStop}
                disabled={stopping}
                className={`btn-danger text-xs ${stopping ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {stopping ? 'Stopping...' : 'Emergency Stop All Effects'}
              </button>
            </div>
          </div>
        </section>

        {/* Save Bar */}
        <div className="flex items-center gap-4">
          <button
            onClick={handleSave}
            disabled={saving}
            className={`btn-primary ${saving ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>

          {saveSuccess && (
            <span className="font-archivo text-sm font-bold text-green-status uppercase tracking-wider">
              Saved successfully
            </span>
          )}

          {saveError && (
            <span className="font-archivo text-sm font-bold text-red-700 uppercase tracking-wider">
              {saveError}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
