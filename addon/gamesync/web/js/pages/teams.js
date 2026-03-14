/**
 * Teams page — browse, follow/unfollow, set delay.
 */
const TeamsPage = {
    followedIds: new Set(),
    followedTeams: [],

    async render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-header">
                <h1>Teams</h1>
                <p>Follow teams to track their games and trigger effects</p>
            </div>
            <div class="settings-section">
                <h2>Followed Teams</h2>
                <div id="followed-teams">Loading...</div>
            </div>
            <div class="settings-section">
                <h2>Browse Teams</h2>
                <div class="form-group" style="max-width: 300px; margin-bottom: 16px">
                    <select id="league-filter" onchange="TeamsPage.loadTeams()">
                        <option value="">All Leagues</option>
                        <option value="nfl">NFL</option>
                        <option value="nba">NBA</option>
                        <option value="nhl">NHL</option>
                        <option value="mlb">MLB</option>
                        <option value="eng.1">Premier League</option>
                        <option value="usa.1">MLS</option>
                        <option value="uefa.champions">Champions League</option>
                        <option value="esp.1">La Liga</option>
                        <option value="ger.1">Bundesliga</option>
                        <option value="f1">Formula 1</option>
                    </select>
                </div>
                <div id="all-teams">Loading...</div>
            </div>`;

        await this.loadFollowed();
        await this.loadTeams();
    },

    async loadFollowed() {
        try {
            const data = await API.getFollowedTeams();
            this.followedTeams = data.teams || [];
            this.followedIds = new Set(this.followedTeams.map(t => t.team_id));

            const container = document.getElementById('followed-teams');
            if (!this.followedTeams.length) {
                container.innerHTML = '<p style="color: var(--text-muted)">No teams followed yet. Browse teams below and click to follow.</p>';
                return;
            }

            container.innerHTML = this.followedTeams.map(t => `
                <div class="card" style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; padding: 12px 16px">
                    <div>
                        <strong>${t.team_id}</strong>
                        <span style="color: var(--text-muted); margin-left: 8px">${t.league}</span>
                    </div>
                    <div style="display: flex; gap: 12px; align-items: center">
                        <label style="font-size: 12px; color: var(--text-secondary)">
                            Delay: <input type="range" min="0" max="120" value="${t.delay_seconds}"
                                style="width: 100px; vertical-align: middle"
                                onchange="TeamsPage.updateDelay('${t.team_id}', this.value)">
                            <span>${t.delay_seconds}s</span>
                        </label>
                        <button class="btn btn-sm btn-danger" onclick="TeamsPage.unfollow('${t.team_id}')">
                            Unfollow
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            document.getElementById('followed-teams').innerHTML = `<p>Error: ${e.message}</p>`;
        }
    },

    async loadTeams() {
        const league = document.getElementById('league-filter')?.value || '';
        const container = document.getElementById('all-teams');

        try {
            const data = await API.getTeams(league ? { league } : {});
            const byLeague = data.teams || {};

            if (Object.keys(byLeague).length === 0) {
                container.innerHTML = '<p style="color: var(--text-muted)">No teams found.</p>';
                return;
            }

            let html = '';
            for (const [leagueName, teams] of Object.entries(byLeague)) {
                html += `<h3 style="margin: 16px 0 8px; color: var(--text-secondary)">${leagueName.toUpperCase()}</h3>`;
                html += '<div class="team-list">';
                for (const t of teams) {
                    const isFollowed = this.followedIds.has(t.id);
                    html += `
                        <div class="team-item ${isFollowed ? 'followed' : ''}"
                             onclick="TeamsPage.toggleFollow('${t.id}', '${t.league}')">
                            <div class="team-color-dot" style="background: ${t.primary_color || '#666'}"></div>
                            <div>
                                <div style="font-weight: 500">${t.display_name}</div>
                                <div style="font-size: 12px; color: var(--text-muted)">${t.abbreviation}</div>
                            </div>
                        </div>`;
                }
                html += '</div>';
            }
            container.innerHTML = html;
        } catch (e) {
            container.innerHTML = `<p>Error loading teams: ${e.message}</p>`;
        }
    },

    async toggleFollow(teamId, league) {
        if (this.followedIds.has(teamId)) {
            await this.unfollow(teamId);
        } else {
            try {
                await API.followTeam(teamId, league);
                App.showToast('Team followed!', 'success');
                await this.loadFollowed();
                await this.loadTeams();
            } catch (e) {
                App.showToast(`Error: ${e.message}`, 'error');
            }
        }
    },

    async unfollow(teamId) {
        try {
            await API.unfollowTeam(teamId);
            App.showToast('Team unfollowed', 'success');
            await this.loadFollowed();
            await this.loadTeams();
        } catch (e) {
            App.showToast(`Error: ${e.message}`, 'error');
        }
    },

    async updateDelay(teamId, seconds) {
        try {
            await API.updateTeamFollow(teamId, { delay_seconds: parseInt(seconds) });
        } catch (e) {
            App.showToast(`Error: ${e.message}`, 'error');
        }
    },
};
