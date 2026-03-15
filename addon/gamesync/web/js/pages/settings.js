/**
 * Settings page — app configuration.
 */
const SettingsPage = {
    config: null,

    async render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-header">
                <h1>Settings</h1>
                <p>Configure GameSync behavior</p>
            </div>
            <div id="settings-content">
                <div class="empty-state"><div class="spinner"></div></div>
            </div>`;

        await this.loadConfig();
        await this.loadHealth();
    },

    async loadConfig() {
        try {
            this.config = await API.getConfig();
            this.renderForm();
        } catch (e) {
            document.getElementById('settings-content').innerHTML = `<p>Error: ${e.message}</p>`;
        }
    },

    renderForm() {
        const c = this.config;
        document.getElementById('settings-content').innerHTML = `
            <div class="settings-section">
                <h2>Polling Intervals</h2>
                <div class="card" style="max-width: 500px">
                    <div class="form-group">
                        <label>Live Game Poll Interval (seconds)</label>
                        <input id="cfg-live" type="number" min="5" max="60" value="${c.poll_interval_live}">
                    </div>
                    <div class="form-group">
                        <label>Game Day Poll Interval (seconds)</label>
                        <input id="cfg-gameday" type="number" min="30" max="300" value="${c.poll_interval_gameday}">
                    </div>
                    <div class="form-group">
                        <label>Idle Poll Interval (seconds)</label>
                        <input id="cfg-idle" type="number" min="60" max="900" value="${c.poll_interval_idle}">
                    </div>
                </div>
            </div>

            <div class="settings-section">
                <h2>Default Delay</h2>
                <div class="card" style="max-width: 500px">
                    <div class="form-group">
                        <label>Default Anti-Spoiler Delay: <strong id="delay-display">${c.default_delay_seconds}s</strong></label>
                        <input id="cfg-delay" type="range" min="0" max="120" value="${c.default_delay_seconds}"
                            oninput="document.getElementById('delay-display').textContent = this.value + 's'">
                    </div>
                </div>
            </div>

            <div class="settings-section">
                <h2>Audio & TTS</h2>
                <div class="card" style="max-width: 500px">
                    <div class="form-group">
                        <label>Default Audio Entity</label>
                        <input id="cfg-audio" placeholder="media_player.living_room" value="${c.default_audio_entity || ''}">
                    </div>
                    <div class="form-group">
                        <label>TTS Entity</label>
                        <input id="cfg-tts" placeholder="media_player.google_home" value="${c.tts_entity || ''}">
                    </div>
                    <div class="form-group">
                        <label>TTS Language</label>
                        <input id="cfg-lang" value="${c.tts_language || 'en'}">
                    </div>
                </div>
            </div>

            <div class="settings-section">
                <h2>API Keys</h2>
                <div class="card" style="max-width: 500px">
                    <div class="form-group">
                        <label>API-Football Key (optional — for additional soccer data)</label>
                        <input id="cfg-apifootball" type="password" value="${c.api_football_key || ''}" placeholder="Optional">
                    </div>
                </div>
            </div>

            <button class="btn btn-primary" onclick="SettingsPage.save()">Save Settings</button>

            <div class="settings-section" style="margin-top: 32px">
                <h2>Effect Controls</h2>
                <div class="card" style="max-width: 500px; display: flex; flex-direction: column; gap: 12px">
                    <div style="display: flex; justify-content: space-between; align-items: center">
                        <div>
                            <strong>Global Mute</strong>
                            <div style="font-size: 12px; color: var(--text-muted)">Suppress all light and audio effects</div>
                        </div>
                        <button id="mute-btn" class="btn ${c.global_mute ? 'btn-warning' : ''}"
                                onclick="SettingsPage.toggleMute()">
                            ${c.global_mute ? 'Unmute Effects' : 'Mute Effects'}
                        </button>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 8px; border-top: 1px solid var(--border)">
                        <div>
                            <strong>Emergency Stop</strong>
                            <div style="font-size: 12px; color: var(--text-muted)">Immediately cancel all running effects</div>
                        </div>
                        <button class="btn btn-danger" onclick="SettingsPage.emergencyStop()">Stop All Effects</button>
                    </div>
                </div>
            </div>

            <div class="settings-section" style="margin-top: 32px">
                <h2>System Health</h2>
                <div id="health-info" class="card">Loading...</div>
            </div>`;
    },

    async save() {
        try {
            await API.updateConfig({
                poll_interval_live: parseInt(document.getElementById('cfg-live').value),
                poll_interval_gameday: parseInt(document.getElementById('cfg-gameday').value),
                poll_interval_idle: parseInt(document.getElementById('cfg-idle').value),
                default_delay_seconds: parseInt(document.getElementById('cfg-delay').value),
                default_audio_entity: document.getElementById('cfg-audio').value || null,
                tts_entity: document.getElementById('cfg-tts').value || null,
                tts_language: document.getElementById('cfg-lang').value || 'en',
                api_football_key: document.getElementById('cfg-apifootball').value || null,
            });
            App.showToast('Settings saved!', 'success');
        } catch (e) {
            App.showToast(`Error: ${e.message}`, 'error');
        }
    },

    async toggleMute() {
        try {
            const result = await API.toggleMute();
            this.config.global_mute = result.muted;
            const btn = document.getElementById('mute-btn');
            if (btn) {
                btn.textContent = result.muted ? 'Unmute Effects' : 'Mute Effects';
                btn.className = `btn${result.muted ? ' btn-warning' : ''}`;
            }
            App.showToast(result.muted ? 'Effects muted' : 'Effects unmuted', 'success');
        } catch (e) {
            App.showToast(`Error: ${e.message}`, 'error');
        }
    },

    async emergencyStop() {
        try {
            const result = await API.emergencyStop();
            App.showToast(`Stopped ${result.stopped_count} effect(s)`, 'success');
        } catch (e) {
            App.showToast(`Error: ${e.message}`, 'error');
        }
    },

    async loadHealth() {
        try {
            const health = await API.health();
            const container = document.getElementById('health-info');
            if (!container) return;

            const sched = health.scheduler || {};
            container.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px">
                    <div>Status</div><div><strong>${health.status}</strong></div>
                    <div>Version</div><div>${health.version}</div>
                    <div>Scheduler</div><div>${sched.running ? 'Running' : 'Stopped'}</div>
                    <div>Active Leagues</div><div>${(sched.active_leagues || []).join(', ') || 'None'}</div>
                    <div>Live Leagues</div><div>${(sched.live_leagues || []).join(', ') || 'None'}</div>
                    <div>Followed Teams</div><div>${sched.followed_teams || 0}</div>
                    <div>Tracked Games</div><div>${sched.tracked_games || 0}</div>
                    <div>Pending Delayed Events</div><div>${health.pending_delayed_events || 0}</div>
                </div>`;
        } catch (e) {
            const container = document.getElementById('health-info');
            if (container) container.innerHTML = `<p>Error: ${e.message}</p>`;
        }
    },
};
