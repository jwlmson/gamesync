/**
 * Teams page — browse, follow/unfollow, set delay.
 */
const TeamsPage = {
    followedIds: new Set(),
    followedTeams: [],
    teamCache: {},  // team_id -> { display_name, logo_url, primary_color, abbreviation }

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

        // Load all teams first to populate the cache, then show followed using display names
        await this.loadTeams();
        await this.loadFollowed();
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

            container.innerHTML = this.followedTeams.map(t => {
                const info = this.teamCache[t.team_id] || {};
                const color = info.primary_color || '#555';
                const name = info.display_name || t.team_id;
                const abbr = info.abbreviation || '';
                const logo = info.logo_url
                    ? `<img src="${info.logo_url}" style="width:28px;height:28px;object-fit:contain;margin-right:8px" alt="${abbr}">`
                    : `<div style="width:28px;height:28px;border-radius:50%;background:${color};margin-right:8px;flex-shrink:0"></div>`;
                return `
                <div class="card" style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; padding: 12px 16px">
                    <div style="display: flex; align-items: center">
                        ${logo}
                        <div>
                            <strong>${name}</strong>
                            <div style="font-size: 12px; color: var(--text-muted)">${t.league}${abbr ? ' · ' + abbr : ''}</div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 12px; align-items: center">
                        <label style="font-size: 12px; color: var(--text-secondary)">
                            Delay: <input type="range" min="0" max="120" value="${t.delay_seconds}"
                                style="width: 100px; vertical-align: middle"
                                onchange="TeamsPage.updateDelay('${t.team_id}', this.value)">
                            <span id="delay-label-${t.team_id.replace(/[^a-z0-9]/gi, '_')}">${t.delay_seconds}s</span>
                        </label>
                        <button class="btn btn-sm btn-danger" onclick="TeamsPage.unfollow('${t.team_id}')">
                            Unfollow
                        </button>
                    </div>
                </div>`;
            }).join('');
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

            // Populate cache from browse results (id -> display info)
            for (const teams of Object.values(byLeague)) {
                for (const t of teams) {
                    this.teamCache[t.id] = {
                        display_name: t.display_name,
                        logo_url: t.logo_url,
                        primary_color: t.primary_color,
                        abbreviation: t.abbreviation,
                    };
                }
            }

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
            const labelId = 'delay-label-' + teamId.replace(/[^a-z0-9]/gi, '_');
            const label = document.getElementById(labelId);
            if (label) label.textContent = seconds + 's';
        } catch (e) {
            App.showToast(`Error: ${e.message}`, 'error');
        }
    },
};
