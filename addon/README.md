# GameSync Add-on for Home Assistant

> **A free, self-hosted alternative to ConnectedRoom.io** — syncs your smart lights and speakers with live sports scores, running entirely on your Home Assistant server.

![GameSync Dashboard](https://img.shields.io/badge/status-beta-yellow) ![HA Add-on](https://img.shields.io/badge/home--assistant-add--on-blue) ![Python](https://img.shields.io/badge/python-3.12-blue) ![License](https://img.shields.io/badge/license-MIT-green)

---

## What is GameSync?

GameSync polls live sports scores and triggers smart home effects the moment something happens — a touchdown, a goal, a home run. Your lights flash your team's colors, your speakers play the goal horn, and Home Assistant automations fire off `gamesync_score` events so you can layer on any automation you can imagine.

**No subscription. No cloud dependency. Runs on your HA server.**

### Feature Parity with ConnectedRoom

| Feature | ConnectedRoom | GameSync |
|---|---|---|
| Live score tracking | ✅ | ✅ |
| Light effects on scores | ✅ | ✅ |
| Team color effects | ✅ | ✅ |
| Audio / goal horns | ✅ | ✅ (via HA media_player) |
| Text-to-speech | ✅ | ✅ (via HA TTS) |
| Stream delay / anti-spoiler | ✅ up to 120s | ✅ up to 120s |
| Per-team delay memory | ✅ | ✅ |
| Manual trigger buttons | ✅ | ✅ |
| Game calendar | ✅ | ✅ |
| Multi-team support | ✅ | ✅ |
| HA event bus integration | ❌ | ✅ |
| Self-hosted / free | ❌ | ✅ |

---

## Supported Sports & Leagues

| Sport | Leagues | Data Source |
|---|---|---|
| 🏈 Football | NFL | ESPN (no API key) |
| 🏀 Basketball | NBA | ESPN (no API key) |
| 🏒 Hockey | NHL | ESPN (no API key) |
| ⚾ Baseball | MLB | ESPN (no API key) |
| ⚽ Soccer | Premier League, MLS, Champions League, La Liga, Bundesliga | ESPN (no API key) |
| 🏎️ Formula 1 | F1 | OpenF1 (no API key) |

> All ESPN data is fetched from ESPN's public (unauthenticated) scoreboard API. No API keys required for any sport out of the box.

---

## Architecture

GameSync is split into two components that work together:

```
┌─────────────────────────────────────────────────────────┐
│                   Home Assistant Server                  │
│                                                         │
│  ┌─────────────────────┐    ┌──────────────────────┐   │
│  │  GameSync Add-on    │    │  GameSync HACS       │   │
│  │  (this repo)        │◄──►│  Integration         │   │
│  │                     │    │  (gamesync-ha repo)  │   │
│  │  FastAPI backend    │    │                      │   │
│  │  Score polling      │    │  Sensors / services  │   │
│  │  Effect engine      │    │  HA event bus        │   │
│  │  Web UI             │    │                      │   │
│  └─────────┬───────────┘    └──────────────────────┘   │
│            │                                            │
│            ▼                                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Home Assistant Core                 │   │
│  │   light.*  media_player.*  tts.*  event bus     │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Add-on (this repo)
- **Python 3.12 + FastAPI** backend running inside Docker
- Polls sports APIs on adaptive intervals (15s live, 60s game day, 5m idle)
- Detects score changes by diffing game snapshots
- Routes events through a per-team configurable delay buffer (anti-spoiler)
- Executes light effect sequences via HA Supervisor API
- Fires `gamesync_*` events on the HA event bus
- Serves a vanilla JS SPA web UI via HA Ingress (appears in the HA sidebar)

### HACS Integration ([gamesync-ha](https://github.com/jwlmson/gamesync-ha))
- Exposes per-team sensors (`score`, `game_state`)
- Binary sensors (`game_live`, `winning`)
- HA services (`trigger_effect`, `set_delay`, `refresh`)
- Re-fires GameSync events on the HA event bus for automation triggers

---

## Installation

### Prerequisites
- Home Assistant with the **Add-on Store** (Supervisor / OS / Supervised install)
- At least one smart light integration already configured in HA (Hue, Govee, LIFX, WLED, etc.)

### Step 1 — Install the Add-on

**Option A: Local add-on** (works immediately without publishing)

1. In your HA file system, create `/addons/gamesync/` (e.g. via the SSH add-on or Samba)
2. Copy the entire contents of this repo into that folder
3. In HA: **Settings → Add-ons → Add-on Store → ⋮ → Check for updates**
4. Find "GameSync" under **Local add-ons** and install it

**Option B: Add this repo to HA Add-on Store** (once you've forked and have a public repo)

1. In HA: **Settings → Add-ons → Add-on Store → ⋮ → Repositories**
2. Add: `https://github.com/jwlmson/gamesync-addon`
3. Find and install GameSync

### Step 2 — Start the Add-on
1. Open the GameSync add-on
2. Configure options (optional — defaults work):
   - `log_level`: `info` (or `debug` for troubleshooting)
   - `api_football_key`: Optional API-Football.com key for additional soccer data
3. Click **Start**
4. Enable **"Show in sidebar"** for easy access

### Step 3 — Install the HACS Integration (optional but recommended)

1. In HACS: **Integrations → Custom repositories**
2. Add `https://github.com/jwlmson/gamesync-ha` (category: Integration)
3. Install "GameSync"
4. Restart HA
5. In **Settings → Integrations**, add GameSync (auto-detects the add-on)

---

## Configuration

### Add-on Options

```yaml
# Configured in the Add-on UI or /data/options.json
api_football_key: ""    # Optional: API-Football.com key for backup soccer data
log_level: "info"       # debug | info | warning | error
```

### Via the Web UI (GameSync sidebar panel)

All configuration is done through the built-in web UI. No YAML required.

| Page | What you configure |
|---|---|
| **Teams** | Follow/unfollow teams, set per-team stream delay (0–120s) |
| **Lights** | Create light groups, assign HA light entities, link groups to teams |
| **Effects** | Preview and manually trigger effects per team |
| **Calendar** | View upcoming games for followed teams |
| **Settings** | Poll intervals, default delay, audio entity, TTS entity, API keys |

---

## Effect Engine

Effects are composable sequences of primitive light operations:

| Primitive | Description |
|---|---|
| `flash` | Rapid on/off cycles at team color |
| `color_cycle` | Step through a list of colors |
| `fade` | Smooth color-to-color transition using HA's `transition` |
| `solid` | Hold a color for a duration |
| `pulse` | Sinusoidal brightness oscillation |
| `restore` | Return lights to their pre-effect state |

### Built-in Presets by Sport

| Sport | Score Event | Preset |
|---|---|---|
| NFL | Touchdown (≥6 pts) | 5× flash → 3s solid → restore |
| NFL | Field goal (3 pts) | 3× flash → restore |
| NHL/Soccer | Goal | 8× flash → 4× color cycle → restore |
| NBA | Basket | 3× pulse → restore |
| MLB | Run scored | 3× flash → 2s fade → restore |
| F1 | Overtake / Safety Car | 3× flash → restore |
| Any | Game start | 3× color cycle → 2s solid → restore |
| Any | Game end (win) | 10× flash → 5× pulse → restore |
| Any | Game end (loss) | fade to dim → restore |

---

## Anti-Spoiler Delay System

Configure a delay (0–120 seconds) per team to align effects with your stream delay.

**How it works:**
- Events enter an asyncio priority queue keyed by `event_time + delay_seconds`
- A drain coroutine sleeps until the next event's release time
- Both light effects **and** the web UI score display respect the delay — no spoilers from the dashboard either
- Delay is set per team and persisted across restarts
- Changing delay mid-game only affects future events (buffered events keep their original release time)

```
Score detected   ──►   delay_buffer   ──►  effect executor
t=0:00                  (holds 30s)         t=0:30
                                       ──►  HA event bus (gamesync_score)
                                       ──►  SSE dashboard update
```

---

## Home Assistant Events

GameSync fires these events on the HA event bus, usable in any automation:

| Event | Fires when | Key data fields |
|---|---|---|
| `gamesync_score` | A team scores | `team_id`, `team_name`, `league`, `home_score`, `away_score`, `scoring_type` |
| `gamesync_game_start` | Game begins | `team_id`, `team_name`, `opponent`, `league` |
| `gamesync_game_end` | Game ends | `team_id`, `result` (win/loss/draw), `home_score`, `away_score` |
| `gamesync_period_change` | Period/quarter/half changes | `team_id`, `period`, `league` |
| `gamesync_special` | Red zone, power play, safety car, cards | `team_id`, `event_type`, `details` |

### Example Automation

```yaml
# Flash all lights red when Eagles score a touchdown
automation:
  - alias: "Eagles Touchdown"
    trigger:
      - platform: event
        event_type: gamesync_score
        event_data:
          team_id: "nfl:21"          # Philadelphia Eagles ESPN ID
          scoring_type: "touchdown"
    action:
      - service: light.turn_on
        target:
          area_id: living_room
        data:
          color_name: green
          flash: long
```

---

## REST API Reference

The add-on exposes a REST API at port 8099 (via Ingress, or `http://homeassistant.local:8099` if you expose the port):

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check + scheduler status |
| GET | `/api/games/live` | Currently live games for followed teams |
| GET | `/api/games` | All games for followed teams (today) |
| GET | `/api/games/calendar?days=30` | Upcoming game calendar |
| GET | `/api/teams` | All available teams by league |
| GET | `/api/teams/followed` | Followed teams with config |
| POST | `/api/teams/follow` | Follow a team |
| DELETE | `/api/teams/follow/{team_id}` | Unfollow a team |
| PUT | `/api/teams/follow/{team_id}` | Update delay / effects_enabled |
| GET | `/api/effects/presets` | Available effect presets |
| POST | `/api/effects/trigger` | Manually trigger an effect |
| GET | `/api/lights/entities` | All HA light entities |
| GET | `/api/lights/groups` | Configured light groups |
| POST | `/api/lights/groups` | Create a light group |
| GET | `/api/config` | App configuration |
| PUT | `/api/config` | Update configuration |
| GET | `/api/events/history` | Event log |
| GET | `/api/events/stream` | SSE real-time event stream |

---

## Project Structure

```
gamesync-addon/
├── config.yaml                 # HA add-on metadata
├── build.yaml                  # Multi-arch build (amd64, aarch64, armv7)
├── Dockerfile
├── run.sh                      # Entrypoint (reads HA options → launches uvicorn)
├── requirements.txt
├── gamesync/
│   ├── main.py                 # FastAPI app factory + lifespan
│   ├── config.py               # Settings (env vars + /data/options.json)
│   ├── api/                    # FastAPI routers (games, teams, effects, lights, events, config, health)
│   ├── sports/                 # Provider pattern
│   │   ├── base.py             # SportProvider ABC
│   │   ├── models.py           # Game, Team, Score, GameEvent data models
│   │   ├── registry.py         # Provider registry
│   │   ├── espn.py             # Shared ESPN client
│   │   ├── espn_nfl/nba/nhl/mlb/soccer.py
│   │   └── openf1.py           # Formula 1 via OpenF1
│   ├── engine/
│   │   ├── scheduler.py        # Adaptive 3-tier polling scheduler
│   │   ├── poller.py           # Score diff detection
│   │   ├── delay_buffer.py     # Anti-spoiler delay queue
│   │   └── event_emitter.py    # In-process pub/sub + SSE queues
│   ├── effects/
│   │   ├── primitives.py       # flash, pulse, fade, solid, color_cycle, restore
│   │   ├── presets.py          # Sport-specific effect presets
│   │   ├── composer.py         # Builds sequences from config or presets
│   │   └── executor.py         # Executes sequences via HA service calls
│   ├── ha_client/              # HA Supervisor API wrappers
│   │   ├── client.py           # Base HTTP client (SUPERVISOR_TOKEN auth)
│   │   ├── lights.py           # light.turn_on/off + state capture/restore
│   │   ├── media.py            # media_player.play_media
│   │   ├── tts.py              # tts.speak
│   │   └── events.py           # Fire events on HA event bus
│   ├── storage/
│   │   ├── db.py               # SQLite (aiosqlite) in /data/gamesync.db
│   │   └── models.py           # FollowedTeam, LightGroup, AppConfig
│   └── web/                    # Vanilla JS SPA served via HA Ingress
│       ├── index.html
│       ├── css/app.css
│       └── js/
│           ├── api.js           # Fetch wrapper
│           ├── app.js           # SPA router
│           └── pages/           # dashboard, teams, lights, effects, calendar, settings
└── tests/
```

---

## Development

### Run locally (outside HA, for dev/testing)

```bash
cd gamesync-addon
pip install -r requirements.txt

# Set environment variables (normally provided by HA add-on runtime)
export GAMESYNC_DATA_PATH="./data"
export SUPERVISOR_TOKEN=""          # Empty = HA calls will fail gracefully
export GAMESYNC_LOG_LEVEL="debug"

mkdir -p data
uvicorn gamesync.main:app --host 0.0.0.0 --port 8099 --reload
```

Open `http://localhost:8099` — the web UI will load. Score polling works without a Supervisor token; only light/audio effects require HA.

### Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

### Adding a New Sport Provider

1. Create `gamesync/sports/espn_yourleague.py` subclassing `SportProvider`
2. Set `SPORT_PATH`, `LEAGUE`, `SPORT` class vars
3. Override `detect_events()` for sport-specific events
4. Register it in `gamesync/sports/registry.py`

That's it — the scheduler, poller, and effect engine pick it up automatically.

---

## Roadmap

- [ ] Custom effect builder in the UI (drag-and-drop step editor)
- [ ] Fantasy league integration (display fantasy score alongside game score)
- [ ] NCAA football and basketball
- [ ] WNBA support
- [ ] Audio file upload (custom goal horns)
- [ ] WLED direct integration (for sub-100ms latency effects)
- [ ] Mobile push notifications via HA companion app
- [ ] Multi-game split-screen dashboard

---

## Contributing

Pull requests welcome. Please open an issue first to discuss major changes.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-sport`)
3. Commit your changes
4. Open a PR

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [ESPN hidden API](https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c) — the community's discovery of ESPN's unauthenticated scoreboard endpoints
- [OpenF1](https://openf1.org/) — free, open Formula 1 timing data
- [ConnectedRoom.io](https://connectedroom.io/) — the inspiration for this project
- [Home Assistant](https://www.home-assistant.io/) — the platform that makes all of this possible
