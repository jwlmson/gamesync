/**
 * Sounds page — manage built-in and custom audio assets.
 */
const SoundsPage = {
    sounds: [],

    async render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-header">
                <h1>Sounds</h1>
                <p>Manage audio assets played on game events</p>
            </div>
            <div class="settings-section">
                <h2>Upload Custom Sound</h2>
                <div class="card" style="max-width: 500px">
                    <div class="form-group">
                        <label>Audio File <span style="color: var(--text-muted); font-size: 12px">(MP3, WAV, OGG)</span></label>
                        <input id="sound-file" type="file" accept=".mp3,.wav,.ogg,audio/*">
                    </div>
                    <div class="form-group">
                        <label>Display Name <span style="color: var(--text-muted); font-size: 12px">(optional)</span></label>
                        <input id="sound-name" placeholder="e.g. Goal Horn">
                    </div>
                    <button class="btn btn-primary" onclick="SoundsPage.upload()">Upload Sound</button>
                </div>
            </div>
            <div class="settings-section">
                <h2>Custom Sounds</h2>
                <div id="custom-sounds">Loading...</div>
            </div>
            <div class="settings-section">
                <h2>Built-in Sounds</h2>
                <div id="builtin-sounds">Loading...</div>
            </div>`;

        await this.loadSounds();
    },

    async loadSounds() {
        try {
            this.sounds = await API.getSounds();
            this.renderList('custom', this.sounds.filter(s => s.category === 'custom'));
            this.renderList('builtin', this.sounds.filter(s => s.category === 'built_in'));
        } catch (e) {
            document.getElementById('custom-sounds').innerHTML = `<p>Error loading sounds: ${e.message}</p>`;
        }
    },

    renderList(type, sounds) {
        const container = document.getElementById(`${type}-sounds`);
        if (!sounds.length) {
            container.innerHTML = `<p style="color: var(--text-muted)">${type === 'custom' ? 'No custom sounds uploaded yet.' : 'No built-in sounds found.'}</p>`;
            return;
        }

        container.innerHTML = sounds.map(s => `
            <div class="card" style="margin-bottom: 8px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center">
                <div>
                    <strong>${this._esc(s.name)}</strong>
                    <span style="margin-left: 8px; font-size: 12px; color: var(--text-muted)">${this._formatSize(s.file_size_bytes)}</span>
                    ${s.duration_seconds > 0 ? `<span style="margin-left: 8px; font-size: 12px; color: var(--text-muted)">${s.duration_seconds.toFixed(1)}s</span>` : ''}
                </div>
                <div style="display: flex; gap: 8px; align-items: center">
                    <button class="btn btn-sm" onclick="SoundsPage.play(${s.id})" title="Preview">▶ Play</button>
                    ${s.category === 'custom' ? `<button class="btn btn-sm btn-danger" onclick="SoundsPage.delete(${s.id})">Delete</button>` : ''}
                </div>
            </div>
        `).join('');
    },

    async upload() {
        const fileInput = document.getElementById('sound-file');
        const nameInput = document.getElementById('sound-name');
        const file = fileInput.files[0];

        if (!file) return App.showToast('Select a file first', 'error');

        try {
            const name = nameInput.value.trim() || null;
            await API.uploadSound(file, name);
            App.showToast('Sound uploaded!', 'success');
            fileInput.value = '';
            nameInput.value = '';
            await this.loadSounds();
        } catch (e) {
            App.showToast(`Upload failed: ${e.message}`, 'error');
        }
    },

    play(id) {
        const url = API.getSoundFileUrl(id);
        const audio = new Audio(url);
        audio.play().catch(e => App.showToast(`Playback error: ${e.message}`, 'error'));
    },

    async delete(id) {
        try {
            await API.deleteSound(id);
            App.showToast('Sound deleted', 'success');
            await this.loadSounds();
        } catch (e) {
            App.showToast(`Error: ${e.message}`, 'error');
        }
    },

    _formatSize(bytes) {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    },

    _esc(str) {
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    },
};
