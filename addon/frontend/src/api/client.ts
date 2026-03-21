/**
 * Typed API client for the GameSync backend.
 */

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

// ── Health ──
export const getHealth = () => request<{ status: string }>('/health');

// ── Teams ──
export interface TeamInfo {
  id: string; name: string; abbreviation: string; display_name: string;
  logo_url: string | null; primary_color: string | null; secondary_color: string | null;
  league: string; sport: string;
}
export interface FollowedTeam {
  team_id: string; league: string; delay_seconds: number; effects_enabled: boolean;
  auto_sync_enabled: boolean; priority_rank: number;
  pregame_alert_enabled: boolean; pregame_alert_minutes: number;
}

export const getTeams = (league?: string, search?: string) => {
  const params = new URLSearchParams();
  if (league) params.set('league', league);
  if (search) params.set('search', search);
  return request<{ teams: Record<string, TeamInfo[]> }>(`/teams?${params}`);
};
export const getFollowedTeams = () =>
  request<{ teams: FollowedTeam[] }>('/teams/followed');
export const followTeam = (team_id: string, league: string, delay_seconds = 0) =>
  request('/teams/follow', { method: 'POST', body: JSON.stringify({ team_id, league, delay_seconds }) });
export const unfollowTeam = (team_id: string) =>
  request(`/teams/follow/${encodeURIComponent(team_id)}`, { method: 'DELETE' });
export const updateFollowedTeam = (team_id: string, data: Partial<FollowedTeam>) =>
  request(`/teams/follow/${encodeURIComponent(team_id)}`, { method: 'PUT', body: JSON.stringify(data) });

// ── Team Event Configs ──
export interface TeamEventConfig {
  id?: number; followed_team_id: string; event_type_id: number;
  light_effect_type: string; light_color_hex: string; target_light_entities: string[];
  sound_asset_id: number | null; target_media_players: string[];
  fire_ha_event: boolean; duration_seconds: number;
}
export const getTeamEventConfigs = (team_id: string) =>
  request<{ configs: TeamEventConfig[] }>(`/teams/${encodeURIComponent(team_id)}/events`);
export const updateTeamEventConfigs = (team_id: string, configs: Omit<TeamEventConfig, 'id' | 'followed_team_id'>[]) =>
  request(`/teams/${encodeURIComponent(team_id)}/events`, { method: 'PUT', body: JSON.stringify({ configs }) });
export const copyTeamEventConfigs = (to_team_id: string, from_team_id: string) =>
  request(`/teams/${encodeURIComponent(to_team_id)}/events/copy-from/${encodeURIComponent(from_team_id)}`, { method: 'POST' });

// ── Games ──
export interface Game {
  id: string; league: string; sport: string; status: string;
  home_team: TeamInfo; away_team: TeamInfo;
  score: { home: number; away: number; clock?: string; period?: string } | null;
  start_time: string; venue: string | null; broadcast: string | null;
}
export const getGames = () => request<{ games: Game[] }>('/games');
export const getLiveGames = () => request<{ games: Game[] }>('/games/live');
export const getAllGames = () => request<{ games: Game[] }>('/games/all');

// ── Game Overrides ──
export interface GameOverrideEventConfig {
  id?: number; event_type_id: number; inherit: boolean;
  light_effect_type: string; light_color_hex: string; target_light_entities: string[];
  sound_asset_id: number | null; target_media_players: string[];
  fire_ha_event: boolean; duration_seconds: number;
}
export interface GameOverride {
  id?: number; game_id: string; followed_team_id: string;
  is_enabled: boolean; note: string;
  event_configs: GameOverrideEventConfig[];
}
export const getGameOverride = (game_id: string, team_id?: string) => {
  const params = team_id ? `?team_id=${encodeURIComponent(team_id)}` : '';
  return request<GameOverride | null>(`/games/${encodeURIComponent(game_id)}/override${params}`);
};
export const saveGameOverride = (game_id: string, data: Omit<GameOverride, 'id' | 'game_id'>) =>
  request<GameOverride>(`/games/${encodeURIComponent(game_id)}/override`, { method: 'POST', body: JSON.stringify(data) });
export const deleteGameOverride = (game_id: string, team_id: string) =>
  request(`/games/${encodeURIComponent(game_id)}/override?team_id=${encodeURIComponent(team_id)}`, { method: 'DELETE' });

// ── Sounds ──
export interface SoundAsset {
  id: number; name: string; category: string; file_path: string;
  duration_seconds: number; file_size_bytes: number;
}
export const getSounds = (category?: string) => {
  const params = category ? `?category=${category}` : '';
  return request<SoundAsset[]>(`/sounds${params}`);
};
export const getSound = (id: number) => request<SoundAsset>(`/sounds/${id}`);
export const uploadSound = async (file: File, name?: string) => {
  const form = new FormData();
  form.append('file', file);
  if (name) form.append('name', name);
  const res = await fetch(`${BASE}/sounds/upload${name ? `?name=${encodeURIComponent(name)}` : ''}`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json() as Promise<SoundAsset>;
};
export const deleteSound = (id: number) =>
  request(`/sounds/${id}`, { method: 'DELETE' });
export const getSoundFileUrl = (id: number) => `${BASE}/sounds/${id}/file`;

// ── Event Types ──
export interface EventTypeDefinition {
  id: number; league_id: number; league_code: string;
  event_code: string; display_name: string;
  points_value: number; default_effect_type: string;
}
export const getEventTypes = (league?: string) => {
  const params = league ? `?league=${league}` : '';
  return request<EventTypeDefinition[]>(`/event-types${params}`);
};

// ── Sessions ──
export interface ActiveSession {
  id: number; game_id: string; followed_team_id: string;
  is_primary: boolean; effects_enabled: boolean;
  last_score_home: number; last_score_away: number; created_at: string;
}
export const getSessions = () => request<ActiveSession[]>('/sessions');
export const makeSessionPrimary = (id: number) =>
  request(`/sessions/${id}/make-primary`, { method: 'POST' });
export const endSession = (id: number) =>
  request(`/sessions/${id}`, { method: 'DELETE' });

// ── Effects ──
export const triggerEffect = (team_id: string, event_type: string) =>
  request('/effects/trigger', { method: 'POST', body: JSON.stringify({ team_id, event_type }) });

// ── Global Controls ──
export const toggleMute = () => request<{ muted: boolean }>('/global/mute', { method: 'POST' });
export const emergencyStop = () => request<{ stopped_count: number }>('/global/emergency-stop', { method: 'POST' });

// ── Config ──
export interface AppConfig {
  default_delay_seconds: number; poll_interval_live: number;
  poll_interval_gameday: number; poll_interval_idle: number;
  tts_entity: string | null; tts_language: string; tts_enabled: boolean;
  default_audio_entity: string | null;
  global_mute: boolean; effect_max_duration_seconds: number; effect_brightness_limit: number;
}
export const getConfig = () => request<AppConfig>('/config');
export const updateConfig = (config: Partial<AppConfig>) =>
  request('/config', { method: 'PUT', body: JSON.stringify(config) });

// ── Leagues ──
export interface LeagueInfo {
  id: number; code: string; name: string; sport_type: string;
  polling_interval_minutes: number; enabled: boolean;
}

// ── HA Entities ──
export interface HAEntity {
  entity_id: string; friendly_name: string | null; state: string | null;
}
export const getHAEntities = (domain: string) =>
  request<HAEntity[]>(`/ha/entities?domain=${domain}`);

// ── Events (SSE) ──
export const getEventsStreamUrl = () => `${BASE}/events/stream`;
export const getEventHistory = (limit = 50) =>
  request<{ events: any[] }>(`/events/history?limit=${limit}`);
