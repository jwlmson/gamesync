/**
 * Lights page — manage light groups.
 */
const LightsPage = {
    entities: [],
    groups: [],

    async render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-header">
                <h1>Lights</h1>
                <p>Configure which lights react to game events</p>
            </div>
            <div class="settings-section">
                <h2>Light Groups</h2>
                <div id="light-groups">Loading...</div>
                <button class="btn btn-primary" style="margin-top: 12px" onclick="LightsPage.showCreateForm()">
                    + New Group
                </button>
            </div>
            <div id="group-form" style="display: none" class="card" style="margin-top: 16px">
                <h3 id="form-title">New Light Group</h3>
                <div class="form-group">
                    <label>Group Name</label>
                    <input id="group-name" placeholder="e.g. Living Room">
                </div>
                <div class="form-group">
                    <label>Select Lights</label>
                    <div id="entity-list">Loading entities...</div>
                </div>
                <div class="form-group">
                    <label>Assign to Teams</label>
                    <div id="team-assign">Loading teams...</div>
                </div>
                <div style="display: flex; gap: 8px; margin-top: 12px">
                    <button class="btn btn-primary" onclick="LightsPage.saveGroup()">Save</button>
                    <button class="btn" onclick="LightsPage.hideForm()">Cancel</button>
                </div>
            </div>`;

        await this.loadGroups();
    },

    async loadGroups() {
        try {
            const data = await API.getLightGroups();
            this.groups = data.groups || [];
            const container = document.getElementById('light-groups');

            if (!this.groups.length) {
                container.innerHTML = '<p style="color: var(--text-muted)">No light groups configured.</p>';
                return;
            }

            container.innerHTML = this.groups.map(g => `
                <div class="card" style="margin-bottom: 8px; padding: 12px 16px">
                    <div style="display: flex; justify-content: space-between; align-items: center">
                        <div>
                            <strong>${g.name}</strong>
                            <div style="margin-top: 4px">
                                ${g.entity_ids.map(e => `<span class="entity-chip selected">${e}</span>`).join(' ')}
                            </div>
                            ${g.team_ids.length ? `<div style="margin-top: 4px; font-size: 12px; color: var(--text-secondary)">Teams: ${g.team_ids.join(', ')}</div>` : ''}
                        </div>
                        <button class="btn btn-sm btn-danger" onclick="LightsPage.deleteGroup('${g.id}')">Delete</button>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            document.getElementById('light-groups').innerHTML = `<p>Error: ${e.message}</p>`;
        }
    },

    _editingId: null,
    _selectedEntities: new Set(),
    _selectedTeams: new Set(),

    async showCreateForm() {
        this._editingId = null;
        this._selectedEntities = new Set();
        this._selectedTeams = new Set();

        document.getElementById('group-form').style.display = 'block';
        document.getElementById('form-title').textContent = 'New Light Group';
        document.getElementById('group-name').value = '';

        // Load entities
        try {
            const data = await API.getLightEntities();
            this.entities = data.lights || [];
            document.getElementById('entity-list').innerHTML = this.entities.map(e => `
                <span class="entity-chip" onclick="LightsPage.toggleEntity('${e.entity_id}', this)" data-id="${e.entity_id}">
                    ${e.name}
                </span>
            `).join(' ');
        } catch (e) {
            document.getElementById('entity-list').innerHTML = `<p>Failed to load lights from HA: ${e.message}</p>`;
        }

        // Load teams
        try {
            const data = await API.getFollowedTeams();
            const teams = data.teams || [];
            document.getElementById('team-assign').innerHTML = teams.map(t => `
                <span class="entity-chip" onclick="LightsPage.toggleTeam('${t.team_id}', this)" data-id="${t.team_id}">
                    ${t.team_id}
                </span>
            `).join(' ') || '<p style="color: var(--text-muted)">Follow teams first</p>';
        } catch (e) {
            document.getElementById('team-assign').innerHTML = '<p>Error loading teams</p>';
        }
    },

    hideForm() {
        document.getElementById('group-form').style.display = 'none';
    },

    toggleEntity(id, el) {
        if (this._selectedEntities.has(id)) {
            this._selectedEntities.delete(id);
            el.classList.remove('selected');
        } else {
            this._selectedEntities.add(id);
            el.classList.add('selected');
        }
    },

    toggleTeam(id, el) {
        if (this._selectedTeams.has(id)) {
            this._selectedTeams.delete(id);
            el.classList.remove('selected');
        } else {
            this._selectedTeams.add(id);
            el.classList.add('selected');
        }
    },

    async saveGroup() {
        const name = document.getElementById('group-name').value.trim();
        if (!name) return App.showToast('Group name required', 'error');
        if (!this._selectedEntities.size) return App.showToast('Select at least one light', 'error');

        try {
            await API.createLightGroup({
                name,
                entity_ids: [...this._selectedEntities],
                team_ids: [...this._selectedTeams],
            });
            App.showToast('Light group created!', 'success');
            this.hideForm();
            await this.loadGroups();
        } catch (e) {
            App.showToast(`Error: ${e.message}`, 'error');
        }
    },

    async deleteGroup(id) {
        try {
            await API.deleteLightGroup(id);
            App.showToast('Group deleted', 'success');
            await this.loadGroups();
        } catch (e) {
            App.showToast(`Error: ${e.message}`, 'error');
        }
    },
};
