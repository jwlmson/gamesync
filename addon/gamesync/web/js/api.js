/**
 * GameSync API client — fetch wrapper for the backend REST API.
 */
const API = {
    baseUrl: '/api',

    async _fetch(path, options = {}) {
        const url = `${this.baseUrl}${path}`;
        const resp = await fetch(url, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options,
        });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || `HTTP ${resp.status}`);
        }
        return resp.json();
    },

    // Health
    health() { return this._fetch('/health'); },

    // Games
    getGames(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._fetch(`/games${qs ? '?' + qs : ''}`);
    },
    getLiveGames() { return this._fetch('/games/live'); },
    getAllGames(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._fetch(`/games/all${qs ? '?' + qs : ''}`);
    },
    getCalendar(days = 30) { return this._fetch(`/games/calendar?days=${days}`); },

    // Teams
    getTeams(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._fetch(`/teams${qs ? '?' + qs : ''}`);
    },
    getFollowedTeams() { return this._fetch('/teams/followed'); },
    followTeam(teamId, league, delay = 0) {
        return this._fetch('/teams/follow', {
            method: 'POST',
            body: JSON.stringify({ team_id: teamId, league, delay_seconds: delay }),
        });
    },
    unfollowTeam(teamId) {
        return this._fetch(`/teams/follow/${encodeURIComponent(teamId)}`, { method: 'DELETE' });
    },
    updateTeamFollow(teamId, data) {
        return this._fetch(`/teams/follow/${encodeURIComponent(teamId)}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    // Effects
    getPresets() { return this._fetch('/effects/presets'); },
    triggerEffect(data) {
        return this._fetch('/effects/trigger', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // Lights
    getLightEntities() { return this._fetch('/lights/entities'); },
    getLightGroups() { return this._fetch('/lights/groups'); },
    createLightGroup(data) {
        return this._fetch('/lights/groups', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },
    updateLightGroup(id, data) {
        return this._fetch(`/lights/groups/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },
    deleteLightGroup(id) {
        return this._fetch(`/lights/groups/${id}`, { method: 'DELETE' });
    },

    // Config
    getConfig() { return this._fetch('/config'); },
    updateConfig(data) {
        return this._fetch('/config', {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    // Events
    getEventHistory(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._fetch(`/events/history${qs ? '?' + qs : ''}`);
    },

    // SSE stream
    createEventStream() {
        return new EventSource(`${this.baseUrl}/events/stream`);
    },
};
