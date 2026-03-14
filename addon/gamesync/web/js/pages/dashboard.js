/**
 * Dashboard page — live games and recent events.
 */
const DashboardPage = {
    _refreshTimer: null,

    async render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-header">
                <h1>Dashboard</h1>
                <p>Live games and recent activity</p>
            </div>
            <div id="live-games" class="card-grid">
                <div class="empty-state"><div class="spinner"></div></div>
            </div>
            <div style="margin-top: 32px">
                <h2 style="margin-bottom: 12px">Recent Events</h2>
                <div id="event-log" class="card">Loading...</div>
            </div>`;

        await this.refreshGames();
        await this.loadEventLog();

        // Auto-refresh every 15s
        clearInterval(this._refreshTimer);
        this._refreshTimer = setInterval(() => this.refreshGames(), 15000);
    },

    async refreshGames() {
        try {
            const [liveData, followedData] = await Promise.all([
                API.getLiveGames(),
                API.getGames(),
            ]);

            const games = liveData.games.length > 0 ? liveData.games : followedData.games;
            const container = document.getElementById('live-games');
            if (!container) return;

            if (!games || games.length === 0) {
                container.innerHTML = `
                    <div class="empty-state" style="grid-column: 1/-1">
                        <h3>No games right now</h3>
                        <p>Follow teams in the Teams tab to see their games here.</p>
                    </div>`;
                return;
            }

            container.innerHTML = games.map(g => this.renderGameCard(g)).join('');
        } catch (e) {
            const container = document.getElementById('live-games');
            if (container) {
                container.innerHTML = `<div class="empty-state"><p>Failed to load games: ${e.message}</p></div>`;
            }
        }
    },

    renderGameCard(game) {
        const isLive = game.status === 'live' || game.status === 'halftime';
        const home = game.home_team;
        const away = game.away_team;
        const score = game.score || { home: 0, away: 0 };
        const statusClass = game.status;

        const detail = score.period || '';
        const clock = score.clock || '';
        const startTime = new Date(game.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        return `
            <div class="game-card ${isLive ? 'live' : ''}">
                <div class="game-status">
                    <span class="status-badge ${statusClass}">${game.status}</span>
                    <span>${game.league} ${game.broadcast ? '· ' + game.broadcast : ''}</span>
                </div>
                <div class="teams">
                    <div class="team">
                        ${home.logo_url ? `<img class="team-logo" src="${home.logo_url}" alt="${home.abbreviation}">` : `<div class="team-logo" style="background:${home.primary_color || '#333'}"></div>`}
                        <span class="team-name">${home.display_name}</span>
                        <span class="team-abbr">${home.abbreviation}</span>
                    </div>
                    <div class="score">
                        ${game.status === 'scheduled' ? `<span class="vs">${startTime}</span>` : `${score.away} - ${score.home}`}
                    </div>
                    <div class="team">
                        ${away.logo_url ? `<img class="team-logo" src="${away.logo_url}" alt="${away.abbreviation}">` : `<div class="team-logo" style="background:${away.primary_color || '#333'}"></div>`}
                        <span class="team-name">${away.display_name}</span>
                        <span class="team-abbr">${away.abbreviation}</span>
                    </div>
                </div>
                ${detail ? `<div class="game-detail">${detail} ${clock ? '· ' + clock : ''}</div>` : ''}
                <div class="actions">
                    <button class="btn btn-sm" onclick="DashboardPage.triggerEffect('${home.id}', '${game.league}')">
                        Trigger ${home.abbreviation}
                    </button>
                    <button class="btn btn-sm" onclick="DashboardPage.triggerEffect('${away.id}', '${game.league}')">
                        Trigger ${away.abbreviation}
                    </button>
                </div>
            </div>`;
    },

    async triggerEffect(teamId, league) {
        try {
            const result = await API.triggerEffect({ team_id: teamId, league });
            App.showToast(`Effect triggered: ${result.effect}`, 'success');
        } catch (e) {
            App.showToast(`Error: ${e.message}`, 'error');
        }
    },

    async loadEventLog() {
        try {
            const data = await API.getEventHistory({ limit: 20 });
            const container = document.getElementById('event-log');
            if (!container) return;

            if (!data.events || data.events.length === 0) {
                container.innerHTML = '<p style="color: var(--text-muted)">No events yet.</p>';
                return;
            }

            container.innerHTML = `<div style="display: flex; flex-direction: column; gap: 8px">
                ${data.events.map(e => `
                    <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid var(--border)">
                        <span>${e.event_type} ${e.team_id ? '· ' + e.team_id : ''}</span>
                        <span style="color: var(--text-muted); font-size: 12px">${new Date(e.timestamp).toLocaleTimeString()}</span>
                    </div>
                `).join('')}
            </div>`;
        } catch (e) {
            // Silent fail
        }
    },
};
