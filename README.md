# 🏆 GameSync

**Transform your smart home into an immersive sports arena.**

GameSync is a free, self-hosted Home Assistant add-on that polls live scores from NFL, NBA, MLB, NHL, Soccer, and Formula 1 via free public APIs, triggering synchronized light shows and sound effects the moment your team scores.

> No subscription. No cloud dependency. Just you, your team, and lights that go crazy on every touchdown.

---

## ✨ Features

| Feature | Details |
|---|---|
| **6 Sports** | NFL, NBA, NHL, MLB, EPL, MLS, Champions League, La Liga, Bundesliga, Formula 1 |
| **Any HA Lights** | Hue, Govee, LIFX, WLED, Tuya, Z-Wave — anything HA knows |
| **Anti-Spoiler Delay** | Per-team 0–120 second delay to sync with stream lag |
| **Sound Effects** | Plays audio via any `media_player.*` entity; built-in library + upload your own |
| **Per-Event Config** | Different effects per event type (touchdown vs field goal vs safety) |
| **Game Overrides** | Custom effects for specific matchups (playoff game? dial it up) |
| **Multi-Game Handling** | Two games live at once? Set priority — Primary fires effects, Secondary tracks silently |
| **HA Integration** | Sensors, binary sensors, services, and bus events for full automation support |
| **HACS Installation** | Install the companion integration from HACS |
| **Free APIs** | ESPN hidden scoreboard + OpenF1 — no API keys required |

---

## 📸 Screenshots

> The UI uses a vintage sports / stadium aesthetic — slab serif fonts, hard drop shadows, cream + navy + red, ticket-stub cards.

| Dashboard | Teams | Effect Tester |
|---|---|---|
| Live games, schedule, activity | Roster, priority, auto-sync | Diagnostic bench + SSE terminal |

---

## 🗂️ Repository Structure

```
gamesync/
├── addon/                  # HA Add-on (Docker container)
│   ├── gamesync/           # Python FastAPI backend
│   │   ├── api/            # 13 REST routers
│   │   ├── effects/        # Effect composer (3-tier resolution)
│   │   ├── engine/         # Poller, scheduler, session manager
│   │   ├── ha_client/      # HA Supervisor API client
│   │   ├── sports/         # ESPN + OpenF1 providers
│   │   └── storage/        # SQLite (13 tables), seeders, migrations
│   ├── frontend/           # React + Tailwind + Vite UI (9 screens)
│   ├── Dockerfile          # Multi-stage: Node build + Python runtime
│   └── requirements.txt
│
├── integration/            # HACS Custom Integration
│   └── custom_components/gamesync/
│       ├── coordinator.py  # DataUpdateCoordinator
│       ├── sensor.py       # Score + state sensors
│       ├── binary_sensor.py # Live + winning sensors
│       └── services.py     # 6 callable services
│
└── SPEC.md                 # Full Mowgli v7 specification
```

---

## 🚀 Installation

### Prerequisites
- Home Assistant OS or Supervised
- HACS installed (for the companion integration)

### Step 1 — Add the Add-on Repository

In Home Assistant, go to **Settings → Add-ons → Add-on Store → ⋮ → Repositories** and add:

```
https://github.com/jwlmson/gamesync
```

### Step 2 — Install the GameSync Add-on

Find **GameSync** in the add-on store and click **Install**. The add-on runs a FastAPI server on port **8099** with an ingress UI.

### Step 3 — Install the HACS Integration

In HACS, go to **Integrations → ⋮ → Custom repositories** and add:

```
https://github.com/jwlmson/gamesync
```

Select **Integration** as the category, then search for **GameSync** and install.

Restart Home Assistant, then go to **Settings → Integrations → Add Integration → GameSync**.

---

## ⚙️ Configuration

All configuration is done through the web UI at `http://homeassistant.local:8099` (or via HA ingress).

### Following a Team

1. Navigate to **Teams → Scout New Talent**
2. Browse by league or search by name
3. Click **Follow** on your team
4. Configure effects on the **Team Configuration** screen

### Setting Up Effects

Each followed team has per-event-type configuration:

| Setting | Description |
|---|---|
| Light Effect | flash, pulse, color_cycle, solid, fade |
| Color | Hex color for the effect |
| Target Lights | Specific `light.*` entities (or leave blank for all) |
| Sound | Select from built-in library or upload custom MP3 |
| Duration | How long the effect runs (1–30s) |
| Fire HA Event | Whether to emit `gamesync_score` on the HA event bus |

### Anti-Spoiler Delay

Set a per-team delay (0–120 seconds) to match your streaming lag. On the Team Management screen, tap the delay field next to any team.

### Multi-Game Priority

When two followed teams have games live simultaneously:
- The team with the **lower priority rank** is designated **Primary** — its effects fire
- The **Secondary** team still tracks score but suppresses execution
- Switch primary via the Sessions panel or the `gamesync.set_primary_session` service

---

## 🔧 Home Assistant Integration

### Sensors (per followed team)

| Entity | Value | Attributes |
|---|---|---|
| `sensor.gamesync_<team>_score` | `"21 - 14"` | home_score, away_score, my_score, period, clock, game_id |
| `sensor.gamesync_<team>_game_state` | `"live"` | team_id, league, sport, opponent, is_home |
| `binary_sensor.gamesync_<team>_live` | `on/off` | ON when game is in progress |
| `binary_sensor.gamesync_<team>_winning` | `on/off` | ON when team is currently ahead |

### Services

| Service | Description | Parameters |
|---|---|---|
| `gamesync.trigger_effect` | Manually trigger an effect | `team_id`, `event_type` |
| `gamesync.set_delay` | Set anti-spoiler delay | `team_id`, `delay_seconds` (0–120) |
| `gamesync.emergency_stop` | Kill all active effects immediately | — |
| `gamesync.mute_toggle` | Toggle global effect mute | — |
| `gamesync.set_primary_session` | Switch the primary active game | `session_id` |
| `gamesync.refresh` | Force immediate data refresh | — |

### HA Events (event bus)

| Event | When fired | Payload |
|---|---|---|
| `gamesync_score` | Team scores | team_id, game_id, league, details |
| `gamesync_game_start` | Game goes live | team_id, game_id, league |
| `gamesync_game_end` | Game finishes | team_id, game_id, final_score |
| `gamesync_period_change` | Period/half change | team_id, game_id, period |
| `gamesync_special` | Special event (red zone, safety car, etc.) | team_id, details |
| `gamesync_mute_changed` | Mute toggled | muted (bool) |
| `gamesync_session_changed` | Primary session switched | primary_session_id |

### Example Automations

```yaml
# Flash Hue lights on touchdown
automation:
  - alias: "GameSync — Touchdown Flash"
    trigger:
      - platform: event
        event_type: gamesync_score
        event_data:
          details:
            scoring_type: touchdown
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          flash: short

# Announce score on Google Home
automation:
  - alias: "GameSync — Score Announcement"
    trigger:
      - platform: event
        event_type: gamesync_score
    action:
      - service: tts.google_translate_say
        data:
          entity_id: media_player.google_home
          message: "Score update! {{ trigger.event.data.details.team_name }} scores!"
```

---

## 🏗️ Architecture

```
ESPN APIs ──────────────────────────────┐
OpenF1 API ─────────────────────────────┤
                                         ▼
                              ProviderRegistry
                                    │ poll every 15s
                              GamePoller (detect score changes)
                                    │
                              DelayBuffer (per-team 0-120s delay)
                                    │
                              EventEmitter (pub/sub)
                                 /        \
                    HAEventFirer          SSE Stream
                (fire HA bus events)   (frontend realtime)
                                 \
                            EffectComposer
                     (3-tier: Override → Team → Preset)
                                 │
                            EffectExecutor
                     (check mute, cancel previous,
                      capture/restore light state)
                                 │
                       HA Supervisor API
                    (light.turn_on / play_media)
```

### Effect Resolution Chain

When a score event fires, the composer resolves in this order:

1. **Game Override** — if a per-game override exists for this game + team and the event's `inherit=false`
2. **Team Config** — the per-event configuration set in the Team Configuration screen
3. **Sport Preset** — built-in fallback preset matching sport + event type

---

## 🛠️ Development

### Backend (Python)

```bash
cd addon
pip install -r requirements.txt
GAMESYNC_DATA_PATH=./data python -m uvicorn gamesync.main:app --reload --port 8099
```

### Frontend (React)

```bash
cd addon/frontend
npm install
npm run dev          # Vite dev server with proxy to :8099
npm run build        # Production build → dist/
```

### Full build

The Dockerfile uses a multi-stage build:
1. Node 20 Alpine builds the React frontend
2. The HA add-on base image (Python) installs requirements and copies the built dist

```bash
docker build --build-arg BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.12-alpine3.19 -t gamesync-addon .
```

---

## 📊 Data Model

GameSync uses SQLite with 13 tables:

| Table | Purpose |
|---|---|
| `followed_teams` | Teams being tracked (+ delay, priority, auto-sync) |
| `leagues` | League definitions (10 leagues seeded on first run) |
| `event_type_definitions` | Per-league scoring events (71 definitions) |
| `team_event_configurations` | Per-team per-event effect settings |
| `game_override_configurations` | Per-game override headers |
| `game_override_event_configurations` | Per-event override details |
| `sound_assets` | Audio file library (built-in + custom) |
| `active_game_sessions` | Runtime game monitoring state |
| `score_events` | Deduplication + history |
| `light_groups` | Named groups of light entities |
| `effect_configs` | Legacy effect config storage |
| `app_config` | Key-value app settings |
| `event_log` | All fired events (for the activity log) |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add your feature"`
4. Push and open a PR

---

## 📄 License

MIT License — see [LICENSE](addon/LICENSE) for details.

---

*Built with ❤️ for sports fans who also happen to be home automation nerds.*
