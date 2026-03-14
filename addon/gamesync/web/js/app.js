/**
 * GameSync SPA — Router and state management.
 */

const App = {
    currentPage: 'dashboard',
    eventSource: null,

    pages: {
        dashboard: DashboardPage,
        teams: TeamsPage,
        lights: LightsPage,
        effects: EffectsPage,
        calendar: CalendarPage,
        settings: SettingsPage,
    },

    init() {
        window.addEventListener('hashchange', () => this.route());
        this.route();
        this.connectSSE();
    },

    route() {
        const hash = window.location.hash || '#/';
        const page = hash.replace('#/', '').split('/')[0] || 'dashboard';

        // Update nav
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.page === page);
        });

        this.currentPage = page;
        const pageHandler = this.pages[page];
        if (pageHandler) {
            pageHandler.render();
        } else {
            document.getElementById('app').innerHTML = `
                <div class="empty-state">
                    <h3>Page not found</h3>
                    <p>The page "${page}" does not exist.</p>
                </div>`;
        }
    },

    connectSSE() {
        try {
            this.eventSource = API.createEventStream();
            this.eventSource.onmessage = (e) => {
                const data = JSON.parse(e.data);
                this.onEvent(data);
            };
            this.eventSource.addEventListener('score_change', (e) => {
                const data = JSON.parse(e.data);
                this.onEvent(data);
                this.showToast(`Score! ${data.team_name || data.team_id}`, 'success');
            });
            this.eventSource.onerror = () => {
                setTimeout(() => this.connectSSE(), 5000);
            };
        } catch (e) {
            // SSE not available — fall back to polling
        }
    },

    onEvent(event) {
        // Refresh dashboard if on dashboard page
        if (this.currentPage === 'dashboard' && DashboardPage._refreshTimer) {
            DashboardPage.refreshGames();
        }
    },

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    },
};

// Boot
document.addEventListener('DOMContentLoaded', () => App.init());
