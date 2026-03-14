/**
 * Calendar page — upcoming games for followed teams.
 */
const CalendarPage = {
    async render() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="page-header">
                <h1>Calendar</h1>
                <p>Upcoming games for your followed teams</p>
            </div>
            <div id="calendar-content">
                <div class="empty-state"><div class="spinner"></div></div>
            </div>`;

        await this.loadCalendar();
    },

    async loadCalendar() {
        try {
            const data = await API.getCalendar(30);
            const container = document.getElementById('calendar-content');
            const calendar = data.calendar || {};

            if (Object.keys(calendar).length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>No upcoming games</h3>
                        <p>Follow teams to see their schedule here.</p>
                    </div>`;
                return;
            }

            let html = '';
            for (const [dateStr, games] of Object.entries(calendar)) {
                const date = new Date(dateStr + 'T12:00:00');
                const dayLabel = date.toLocaleDateString(undefined, {
                    weekday: 'long',
                    month: 'long',
                    day: 'numeric',
                });

                html += `<div class="calendar-day">
                    <h3>${dayLabel}</h3>
                    <div class="card-grid">
                        ${games.map(g => this.renderCalendarGame(g)).join('')}
                    </div>
                </div>`;
            }
            container.innerHTML = html;
        } catch (e) {
            document.getElementById('calendar-content').innerHTML = `
                <div class="empty-state"><p>Failed to load calendar: ${e.message}</p></div>`;
        }
    },

    renderCalendarGame(game) {
        const home = game.home_team;
        const away = game.away_team;
        const time = new Date(game.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        return `
            <div class="card" style="padding: 12px 16px">
                <div style="display: flex; justify-content: space-between; align-items: center">
                    <div>
                        <strong>${away.display_name}</strong>
                        <span style="color: var(--text-muted)"> @ </span>
                        <strong>${home.display_name}</strong>
                    </div>
                    <div style="text-align: right">
                        <div style="font-weight: 600">${time}</div>
                        <div style="font-size: 12px; color: var(--text-muted)">${game.venue || ''}</div>
                    </div>
                </div>
                ${game.broadcast ? `<div style="font-size: 12px; color: var(--text-muted); margin-top: 4px">${game.broadcast}</div>` : ''}
            </div>`;
    },
};
