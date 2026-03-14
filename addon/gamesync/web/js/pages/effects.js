/**
 * Effects page — view presets and manually trigger effects.
 */
const EffectsPage = {
    async render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-header">
                <h1>Effects</h1>
                <p>View available effect presets and test them</p>
            </div>
            <div class="settings-section">
                <h2>Manual Trigger</h2>
                <div class="card" style="max-width: 500px">
                    <div class="form-group">
                        <label>Team</label>
                        <select id="effect-team"><option value="">All lights</option></select>
                    </div>
                    <div class="form-group">
                        <label>Event Type</label>
                        <select id="effect-type">
                            <option value="score_change">Score Change</option>
                            <option value="game_start">Game Start</option>
                            <option value="game_end">Game End</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" onclick="EffectsPage.trigger()">
                        Trigger Effect
                    </button>
                </div>
            </div>
            <div class="settings-section">
                <h2>Available Presets</h2>
                <div id="preset-list">Loading...</div>
            </div>`;

        await this.loadTeams();
        await this.loadPresets();
    },

    async loadTeams() {
        try {
            const data = await API.getFollowedTeams();
            const select = document.getElementById('effect-team');
            (data.teams || []).forEach(t => {
                const opt = document.createElement('option');
                opt.value = t.team_id;
                opt.textContent = t.team_id;
                select.appendChild(opt);
            });
        } catch (e) { /* ignore */ }
    },

    async loadPresets() {
        try {
            const data = await API.getPresets();
            const container = document.getElementById('preset-list');
            const presets = data.presets || [];

            if (!presets.length) {
                container.innerHTML = '<p style="color: var(--text-muted)">No presets loaded.</p>';
                return;
            }

            // Group by sport
            const bySport = {};
            presets.forEach(p => {
                bySport[p.sport] = bySport[p.sport] || [];
                bySport[p.sport].push(p);
            });

            let html = '';
            for (const [sport, items] of Object.entries(bySport)) {
                html += `<h3 style="margin: 16px 0 8px; color: var(--text-secondary)">${sport.toUpperCase()}</h3>`;
                html += '<div style="display: flex; flex-wrap: wrap; gap: 8px">';
                for (const p of items) {
                    html += `<div class="card" style="padding: 10px 16px; min-width: 200px">
                        <strong>${p.event_type}</strong>
                    </div>`;
                }
                html += '</div>';
            }
            container.innerHTML = html;
        } catch (e) {
            document.getElementById('preset-list').innerHTML = `<p>Error: ${e.message}</p>`;
        }
    },

    async trigger() {
        const teamId = document.getElementById('effect-team').value;
        const eventType = document.getElementById('effect-type').value;

        try {
            const result = await API.triggerEffect({
                team_id: teamId || undefined,
                event_type: eventType,
            });
            App.showToast(`Effect triggered: ${result.effect} on ${result.lights} lights`, 'success');
        } catch (e) {
            App.showToast(`Error: ${e.message}`, 'error');
        }
    },
};
