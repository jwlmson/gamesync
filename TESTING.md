# GameSync — Testing Guide

This document covers every testable surface in GameSync: local dev setup, manual UI walkthroughs, REST API curl tests, HA integration checks, and edge-case scenarios.

---

## Table of Contents

1. [Local Development Setup](#1-local-development-setup)
2. [Backend Health Checks](#2-backend-health-checks)
3. [API Endpoint Tests (curl)](#3-api-endpoint-tests-curl)
4. [Web UI Manual Tests](#4-web-ui-manual-tests)
5. [Effect Engine Tests](#5-effect-engine-tests)
6. [Anti-Spoiler Delay Tests](#6-anti-spoiler-delay-tests)
7. [Sound System Tests](#7-sound-system-tests)
8. [HA Integration Tests](#8-ha-integration-tests)
9. [Edge Cases & Error Handling](#9-edge-cases--error-handling)
10. [End-to-End Game Event Flow](#10-end-to-end-game-event-flow)

---

## 1. Local Development Setup

### Prerequisites

- Python 3.12+
- `pip install -r addon/requirements.txt`
- No HA installation required for API and UI tests — light/audio effects will fail gracefully without a `SUPERVISOR_TOKEN`

### Start the backend

```bash
cd addon

# Required env vars
export GAMESYNC_DATA_PATH="./data"
export SUPERVISOR_TOKEN=""          # Empty = HA calls log a warning but don't crash
export GAMESYNC_LOG_LEVEL="debug"

mkdir -p data
uvicorn gamesync.main:app --host 0.0.0.0 --port 8099 --reload
```

**Expected startup output:**
```
INFO:     GameSync starting up...
INFO:     Database initialized (schema vX)
INFO:     Sound manager seeded N built-in sounds
INFO:     No followed teams — scheduler idle
INFO:     GameSync ready
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8099
```

If you see `GameSync ready` the backend is healthy. Open `http://localhost:8099` to reach the web UI.

### Run the React frontend (dev mode)

```bash
cd addon/frontend
npm install
npm run dev      # starts Vite on :5173 with proxy to :8099
```

Visit `http://localhost:5173` for hot-reload dev mode.

---

## 2. Backend Health Checks

### Quick smoke test

```bash
curl -s http://localhost:8099/api/health | python -m json.tool
```

**Expected response shape:**
```json
{
  "status": "ok",
  "version": "0.2.0",
  "scheduler": {
    "running": false,
    "active_leagues": [],
    "live_leagues": [],
    "followed_teams": 0,
    "tracked_games": 0
  },
  "pending_delayed_events": 0
}
```

`status` must be `"ok"`. `scheduler.running` will be `false` if no teams are followed — this is normal.

### Verify all 13 routers mounted

```bash
curl -s http://localhost:8099/openapi.json | python -c "
import json, sys
spec = json.load(sys.stdin)
paths = sorted(spec['paths'].keys())
print(f'{len(paths)} routes registered:')
for p in paths: print(' ', p)
"
```

**Expected — at minimum these route prefixes must appear:**
- `/api/health`
- `/api/games`, `/api/games/live`, `/api/games/calendar`
- `/api/teams`, `/api/teams/followed`, `/api/teams/follow`
- `/api/effects/presets`, `/api/effects/trigger`
- `/api/lights/entities`, `/api/lights/groups`
- `/api/config`
- `/api/events/history`, `/api/events/stream`
- `/api/sounds`, `/api/sounds/upload`
- `/api/sessions`
- `/api/event-types`
- `/api/global/mute`, `/api/global/emergency-stop`
- `/api/game-overrides`

---

## 3. API Endpoint Tests (curl)

Set a base URL for convenience:
```bash
BASE=http://localhost:8099/api
```

### 3.1 Config

```bash
# GET current config
curl -s $BASE/config | python -m json.tool

# UPDATE config
curl -s -X PUT $BASE/config \
  -H "Content-Type: application/json" \
  -d '{"poll_interval_live": 15, "default_delay_seconds": 30}' | python -m json.tool
```

**Expected:** PUT returns the updated config object.

### 3.2 Teams — Browse & Follow

```bash
# Browse all teams (triggers ESPN fetch — may take 2-5s first time)
curl -s "$BASE/teams" | python -c "
import json, sys
d = json.load(sys.stdin)
for league, teams in d['teams'].items():
    print(f'{league}: {len(teams)} teams — e.g. {teams[0][\"display_name\"]} ({teams[0][\"id\"]})')
"

# Browse a single league
curl -s "$BASE/teams?league=nfl" | python -m json.tool | head -40

# Follow a team (use an ID from the browse result above)
curl -s -X POST $BASE/teams/follow \
  -H "Content-Type: application/json" \
  -d '{"team_id": "nfl:21", "league": "nfl", "delay_seconds": 0}' | python -m json.tool

# List followed teams
curl -s $BASE/teams/followed | python -m json.tool

# Update delay for a followed team
curl -s -X PUT "$BASE/teams/follow/nfl:21" \
  -H "Content-Type: application/json" \
  -d '{"delay_seconds": 30}' | python -m json.tool

# Unfollow
curl -s -X DELETE "$BASE/teams/follow/nfl:21"
```

**Expected after follow:** `teams/followed` returns array containing the team with `team_id`, `league`, `delay_seconds`, `effects_enabled`, `priority_rank`.

### 3.3 Games

```bash
# Games for followed teams (today)
curl -s $BASE/games | python -m json.tool

# Currently live games only
curl -s $BASE/games/live | python -m json.tool

# Calendar (next 14 days)
curl -s "$BASE/games/calendar?days=14" | python -m json.tool
```

**Expected:** Each game object contains `home_team.display_name`, `away_team.display_name`, `status`, `score.home`, `score.away`, `start_time`.

### 3.4 Event Types

```bash
# All event types (71 definitions across 10 leagues)
curl -s $BASE/event-types | python -c "
import json, sys
ets = json.load(sys.stdin)
by_league = {}
for et in ets:
    by_league.setdefault(et['league_code'], []).append(et['display_name'])
for lg, names in sorted(by_league.items()):
    print(f'{lg}: {names}')
"

# Filter by league
curl -s "$BASE/event-types?league=nfl" | python -m json.tool
```

**Expected NFL event types:** touchdown, field_goal, safety, two_point_conversion, game_start, game_end, period_change.

### 3.5 Team Event Configurations

Requires a followed team. Follow `nfl:21` first (section 3.2).

```bash
# Get current configs (empty before any are set)
curl -s "$BASE/teams/nfl:21/events" | python -m json.tool

# Bulk-set event configs (get event_type_id values from /event-types?league=nfl)
# Replace 1 with the actual touchdown event_type_id from your DB
curl -s -X PUT "$BASE/teams/nfl:21/events" \
  -H "Content-Type: application/json" \
  -d '{
    "configs": [{
      "event_type_id": 1,
      "light_effect_type": "flash",
      "light_color_hex": "#004C54",
      "target_light_entities": [],
      "sound_asset_id": null,
      "target_media_players": [],
      "fire_ha_event": true,
      "duration_seconds": 5.0
    }]
  }' | python -m json.tool

# Verify configs saved
curl -s "$BASE/teams/nfl:21/events" | python -m json.tool
```

**Expected after PUT:** `{"status": "ok", "count": 1}`. GET then returns the saved config.

### 3.6 Effects

```bash
# List presets
curl -s $BASE/effects/presets | python -m json.tool

# Manually trigger an effect (requires HA — will fail gracefully without SUPERVISOR_TOKEN)
curl -s -X POST $BASE/effects/trigger \
  -H "Content-Type: application/json" \
  -d '{"team_id": "nfl:21", "event_type": "score_change"}' | python -m json.tool
```

**Without HA:** Expect `{"effect": "...", "lights": 0}` — executes with 0 lights affected.

### 3.7 Lights

```bash
# List HA light entities (requires SUPERVISOR_TOKEN — returns [] without it)
curl -s $BASE/lights/entities | python -m json.tool

# Create a light group
curl -s -X POST $BASE/lights/groups \
  -H "Content-Type: application/json" \
  -d '{"name": "Living Room", "entity_ids": ["light.test1", "light.test2"], "team_ids": ["nfl:21"]}' | python -m json.tool

# List groups
curl -s $BASE/lights/groups | python -m json.tool

# Delete group (use ID from list response)
curl -s -X DELETE $BASE/lights/groups/1
```

### 3.8 Sounds

```bash
# List all sounds
curl -s $BASE/sounds | python -m json.tool

# List only custom sounds
curl -s "$BASE/sounds?category=custom" | python -m json.tool

# Upload a custom sound
curl -s -X POST "$BASE/sounds/upload?name=My+Goal+Horn" \
  -F "file=@/path/to/goalhorn.mp3" | python -m json.tool

# Download/verify a sound file (use ID from list response)
curl -I "$BASE/sounds/1/file"
# Expected: HTTP 200, Content-Type: audio/mpeg

# Delete a custom sound
curl -s -X DELETE $BASE/sounds/2
# Expected: {"status": "deleted"}

# Attempt to delete a built-in sound (should fail)
BUILTIN_ID=$(curl -s "$BASE/sounds?category=built_in" | python -c "import json,sys; d=json.load(sys.stdin); print(d[0]['id']) if d else print('none')")
curl -s -X DELETE "$BASE/sounds/$BUILTIN_ID"
# Expected: HTTP 400 with error message
```

### 3.9 Global Controls

```bash
# Get current mute state (check via config)
curl -s $BASE/config | python -c "import json,sys; d=json.load(sys.stdin); print('muted:', d.get('global_mute'))"

# Toggle mute ON
curl -s -X POST $BASE/global/mute | python -m json.tool
# Expected: {"muted": true}

# Toggle mute OFF
curl -s -X POST $BASE/global/mute | python -m json.tool
# Expected: {"muted": false}

# Emergency stop (cancels all running effects)
curl -s -X POST $BASE/global/emergency-stop | python -m json.tool
# Expected: {"stopped_count": 0}  (or N if effects were running)
```

### 3.10 Sessions

Sessions are created automatically when a followed team's game goes live.

```bash
# List active sessions
curl -s $BASE/sessions | python -m json.tool
# Expected: [] when no games live

# Make a session primary (use session ID from list)
curl -s -X POST $BASE/sessions/1/make-primary | python -m json.tool

# End a session
curl -s -X DELETE $BASE/sessions/1 | python -m json.tool
```

### 3.11 Events

```bash
# Event history (last 50 by default)
curl -s $BASE/events/history | python -m json.tool

# Paginated
curl -s "$BASE/events/history?limit=10&offset=0" | python -m json.tool

# SSE stream (press Ctrl+C to exit)
curl -N -H "Accept: text/event-stream" $BASE/events/stream
```

---

## 4. Web UI Manual Tests

Open `http://localhost:8099` (or `http://localhost:5173` with Vite dev server).

### 4.1 Dashboard

| Step | Action | Expected |
|---|---|---|
| 1 | Load page | Spinner, then "No games right now" (no followed teams) |
| 2 | Follow a team, return to Dashboard | Today's game card appears |
| 3 | Live game exists | Card has pulsing "live" badge |
| 4 | Click "Trigger [team abbreviation]" | Toast: "Effect triggered: ..." |
| 5 | Wait 15s | Game cards refresh automatically |
| 6 | Check Recent Events | Events appear after manual trigger |

### 4.2 Teams Page

| Step | Action | Expected |
|---|---|---|
| 1 | Load page | Browse section loads with team grid grouped by league |
| 2 | Verify team cards | Each card shows `display_name`, `abbreviation`, colored dot |
| 3 | Click a team to follow | Toast "Team followed!", card becomes highlighted |
| 4 | Check Followed Teams section | Shows **logo image** (or colored circle fallback), `display_name`, `league · ABBR` |
| 5 | Drag delay slider | Label updates live (e.g. "45s") |
| 6 | Release slider | API call fires — verify with browser DevTools Network tab |
| 7 | Filter by league dropdown | Team grid filters to selected league only |
| 8 | Click followed team | Unfollow prompt; confirms removal from Followed section |

**Key regression check:** Followed Teams must show `display_name` (e.g. "Philadelphia Eagles"), NOT raw `team_id` (e.g. `nfl:21`).

### 4.3 Lights Page

| Step | Action | Expected |
|---|---|---|
| 1 | Load page | "No light groups configured" |
| 2 | Click "+ New Group" | Form slides open |
| 3 | Without HA token | "Failed to load lights from HA" — form still usable |
| 4 | Enter group name, skip entity selection | Save → "Select at least one light" error toast |
| 5 | Enter name, type entity ID manually and click it | Entity chip turns highlighted |
| 6 | Click Save | "Light group created!" toast, group appears in list |
| 7 | Group card shows | Entity chips, assigned team IDs |
| 8 | Click Delete | Group removed from list |

### 4.4 Effects Page

| Step | Action | Expected |
|---|---|---|
| 1 | Load page | Presets load grouped by sport |
| 2 | Select a followed team from dropdown | Team appears in list |
| 3 | Select event type, click Trigger | Toast "Effect triggered: X on Y lights" |
| 4 | Trigger with no team selected | Fires with team_id=undefined (broadcast) |

### 4.5 Calendar Page

| Step | Action | Expected |
|---|---|---|
| 1 | No followed teams | "No upcoming games — Follow teams to see their schedule" |
| 2 | Follow a team, reload | Upcoming games appear grouped by date |
| 3 | Each game card | Shows "Away @ Home", time, venue, broadcast network |

### 4.6 Sounds Page (new)

| Step | Action | Expected |
|---|---|---|
| 1 | Load page | Built-in sounds list appears (if any seeded) |
| 2 | Custom sounds section | "No custom sounds uploaded yet." |
| 3 | Click "Choose File" | OS file picker opens |
| 4 | Select a non-audio file (e.g. .txt) | Upload fails with backend 400 error toast |
| 5 | Select a valid MP3 | Upload → sound appears in Custom Sounds list |
| 6 | Click ▶ Play on the uploaded sound | Audio plays in browser |
| 7 | Click Delete on custom sound | Sound removed; built-in sounds unaffected |
| 8 | Try to delete a built-in sound | No delete button visible for built-ins |
| 9 | Enter a display name before upload | Uploaded sound uses that name |
| 10 | Upload without a display name | Filename used as name |

### 4.7 Settings Page

| Step | Action | Expected |
|---|---|---|
| 1 | Load page | Form populated with current config values |
| 2 | Change poll intervals, click Save | "Settings saved!" toast |
| 3 | Reload page | Values reflect what was saved |
| 4 | Click "Mute Effects" | Button changes to "Unmute Effects" (btn-warning style) |
| 5 | Click "Unmute Effects" | Button reverts to "Mute Effects" |
| 6 | Click "Stop All Effects" | Toast "Stopped 0 effect(s)" (or N if effects running) |
| 7 | System Health section | Shows scheduler status, version, followed team count |

---

## 5. Effect Engine Tests

These tests require a real HA instance with `SUPERVISOR_TOKEN` set.

### 5.1 Manual trigger test

```bash
# Follow a team first
curl -s -X POST $BASE/teams/follow \
  -H "Content-Type: application/json" \
  -d '{"team_id": "nfl:21", "league": "nfl"}' > /dev/null

# Create a light group
curl -s -X POST $BASE/lights/groups \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "entity_ids": ["light.your_real_light"], "team_ids": ["nfl:21"]}' > /dev/null

# Trigger and observe lights physically
curl -s -X POST $BASE/effects/trigger \
  -H "Content-Type: application/json" \
  -d '{"team_id": "nfl:21", "event_type": "score_change"}' | python -m json.tool
```

**Expected:** Lights flash the team's primary color, then restore to their prior state.

### 5.2 Mute behavior

```bash
# Mute effects
curl -s -X POST $BASE/global/mute | python -m json.tool  # {"muted": true}

# Trigger — lights must NOT fire
curl -s -X POST $BASE/effects/trigger \
  -H "Content-Type: application/json" \
  -d '{"team_id": "nfl:21", "event_type": "score_change"}' | python -m json.tool
# Expected: {"effect": "...", "lights": 0, "muted": true}

# Unmute
curl -s -X POST $BASE/global/mute
```

### 5.3 Emergency stop

```bash
# Trigger a long effect (game_end fires a 10x flash sequence)
curl -s -X POST $BASE/effects/trigger \
  -H "Content-Type: application/json" \
  -d '{"team_id": "nfl:21", "event_type": "game_end"}' &

# Immediately stop it
sleep 0.5
curl -s -X POST $BASE/global/emergency-stop | python -m json.tool
# Expected: {"stopped_count": 1}
```

**Expected:** Lights return to state before the effect started.

---

## 6. Anti-Spoiler Delay Tests

### 6.1 Set a delay and verify it applies

```bash
# Set 10-second delay
curl -s -X PUT "$BASE/teams/follow/nfl:21" \
  -H "Content-Type: application/json" \
  -d '{"delay_seconds": 10}'

# Check delay is stored
curl -s $BASE/teams/followed | python -c "
import json, sys
teams = json.load(sys.stdin)['teams']
for t in teams:
    if t['team_id'] == 'nfl:21':
        print('delay:', t['delay_seconds'])
"
```

### 6.2 Verify pending events counter

After a game event fires (or using the debug inject endpoint if available):

```bash
curl -s $BASE/health | python -c "
import json, sys
d = json.load(sys.stdin)
print('Pending delayed events:', d['pending_delayed_events'])
"
```

Within the delay window this should be > 0; it drops to 0 when the event releases.

---

## 7. Sound System Tests

### 7.1 Seed built-in sounds check

```bash
curl -s "$BASE/sounds?category=built_in" | python -c "
import json, sys
sounds = json.load(sys.stdin)
print(f'{len(sounds)} built-in sounds:')
for s in sounds:
    print(f'  [{s[\"id\"]}] {s[\"name\"]} — {s[\"duration_seconds\"]:.1f}s, {s[\"file_size_bytes\"]} bytes')
"
```

### 7.2 Upload / list / delete cycle

```bash
# Create a minimal test MP3 (requires ffmpeg)
ffmpeg -f lavfi -i "sine=frequency=440:duration=1" -q:a 9 /tmp/test_sound.mp3 2>/dev/null

# Upload
SOUND=$(curl -s -X POST "$BASE/sounds/upload?name=Test+Beep" \
  -F "file=@/tmp/test_sound.mp3")
echo $SOUND | python -m json.tool
SOUND_ID=$(echo $SOUND | python -c "import json,sys; print(json.load(sys.stdin)['id'])")

# Verify in list
curl -s "$BASE/sounds?category=custom" | python -c "
import json, sys
sounds = json.load(sys.stdin)
print([s['name'] for s in sounds])
"

# Serve check
curl -sI "$BASE/sounds/$SOUND_ID/file" | head -5
# Expected: HTTP/1.1 200 OK, Content-Type: audio/mpeg

# Delete
curl -s -X DELETE "$BASE/sounds/$SOUND_ID"
# Expected: {"status": "deleted"}

# Confirm gone
curl -s "$BASE/sounds/$SOUND_ID"
# Expected: HTTP 404
```

---

## 8. HA Integration Tests

These require the HACS integration installed and configured.

### 8.1 Integration setup verification

1. Install the custom integration from `integration/custom_components/gamesync/`
2. Go to **Settings → Integrations → Add Integration → GameSync**
3. The integration auto-detects the add-on URL (`http://localhost:8099`)
4. After setup, entities should appear:

```bash
# In HA Developer Tools → Template:
{{ states('sensor.gamesync_eagles_score') }}
{{ states('binary_sensor.gamesync_eagles_live') }}
{{ states('binary_sensor.gamesync_eagles_winning') }}
```

### 8.2 Service calls

In HA Developer Tools → Services:

```yaml
# Trigger an effect
service: gamesync.trigger_effect
data:
  team_id: "nfl:21"
  event_type: "score_change"

# Set delay
service: gamesync.set_delay
data:
  team_id: "nfl:21"
  delay_seconds: 45

# Toggle mute
service: gamesync.mute_toggle

# Emergency stop
service: gamesync.emergency_stop

# Force refresh
service: gamesync.refresh
```

### 8.3 HA event bus verification

In HA Developer Tools → Events, listen for `gamesync_score`:

```yaml
# Listen for:
gamesync_score
gamesync_game_start
gamesync_game_end
gamesync_period_change
gamesync_special
```

Manually trigger an effect and verify the event fires on the bus with correct payload fields (`team_id`, `game_id`, `league`, `details`).

### 8.4 SSE stream real-time check

```bash
# Open SSE stream in terminal
curl -N -H "Accept: text/event-stream" http://localhost:8099/api/events/stream &

# Trigger an effect in another terminal
curl -s -X POST $BASE/effects/trigger \
  -H "Content-Type: application/json" \
  -d '{"team_id": "nfl:21", "event_type": "score_change"}'

# Expected SSE output:
# event: score_change
# data: {"team_id": "nfl:21", ...}
```

---

## 9. Edge Cases & Error Handling

### 9.1 Unknown league

```bash
curl -s -X POST $BASE/teams/follow \
  -H "Content-Type: application/json" \
  -d '{"team_id": "xyz:99", "league": "not_a_league"}'
# Expected: HTTP 400 {"detail": "Invalid league: not_a_league"}
```

### 9.2 Follow same team twice

```bash
curl -s -X POST $BASE/teams/follow \
  -H "Content-Type: application/json" \
  -d '{"team_id": "nfl:21", "league": "nfl"}'
curl -s -X POST $BASE/teams/follow \
  -H "Content-Type: application/json" \
  -d '{"team_id": "nfl:21", "league": "nfl"}'
# Expected: Both return 200/201 (upsert). /teams/followed still shows nfl:21 once.
```

### 9.3 Unfollow a team that isn't followed

```bash
curl -s -X DELETE "$BASE/teams/follow/nfl:99"
# Expected: HTTP 200 {"status": "ok"} (idempotent) or HTTP 404
```

### 9.4 Upload an invalid file type

```bash
echo "this is not audio" > /tmp/fake.mp3
curl -s -X POST "$BASE/sounds/upload" \
  -F "file=@/tmp/fake.mp3" | python -m json.tool
# Expected: HTTP 400 or the file is accepted but duration_seconds=0
```

### 9.5 Delete a built-in sound

```bash
BUILTIN_ID=$(curl -s "$BASE/sounds?category=built_in" | python -c "
import json, sys
d = json.load(sys.stdin)
print(d[0]['id']) if d else print('none')
")
curl -s -X DELETE "$BASE/sounds/$BUILTIN_ID" | python -m json.tool
# Expected: HTTP 400 {"detail": "Cannot delete built-in sound"}
```

### 9.6 Effect trigger with no light groups configured

```bash
curl -s -X POST $BASE/effects/trigger \
  -H "Content-Type: application/json" \
  -d '{"team_id": "nfl:21", "event_type": "score_change"}' | python -m json.tool
# Expected: 200 {"effect": "...", "lights": 0} — no crash, just zero lights affected
```

### 9.7 Make a non-existent session primary

```bash
curl -s -X POST "$BASE/sessions/99999/make-primary" | python -m json.tool
# Expected: HTTP 404 {"detail": "Session 99999 not found"}
```

### 9.8 Backend restart with followed teams

```bash
# Follow a team, set delay
curl -s -X POST $BASE/teams/follow -H "Content-Type: application/json" \
  -d '{"team_id": "nba:14", "league": "nba", "delay_seconds": 60}'

# Restart the server (Ctrl+C, restart uvicorn)
# After restart:
curl -s $BASE/teams/followed | python -m json.tool
# Expected: nba:14 still present with delay_seconds=60

curl -s $BASE/health | python -c "
import json, sys; d=json.load(sys.stdin)
print('Scheduler running:', d['scheduler']['running'])
print('Followed teams:', d['scheduler']['followed_teams'])
"
# Expected: scheduler.running=true (auto-started because teams exist)
```

---

## 10. End-to-End Game Event Flow

This simulates a complete score event from polling to effect execution.

### Prerequisites

- Followed team with an active or upcoming game
- HA configured with at least one `light.*` entity
- `SUPERVISOR_TOKEN` set in environment

### Observation steps

1. **Start the backend** with `debug` log level
2. **Follow a team** that has a game today (use the calendar to check)
3. **Watch the logs** — you should see:
   ```
   DEBUG: Polling nfl live games...
   DEBUG: Game nfl:game123 status=live score=0-0
   ```
4. When a score change occurs:
   ```
   INFO: Score change detected: nfl:21 — 7-0 (touchdown)
   DEBUG: DelayBuffer: queuing event for nfl:21, release in 0.0s
   DEBUG: EffectComposer: resolved effect via preset (no team config)
   DEBUG: EffectExecutor: running flash x5 on 2 lights
   INFO: HA event fired: gamesync_score
   ```
5. **Lights flash** with team primary color
6. **Dashboard auto-refreshes** (15s interval) and shows updated score
7. **Event log** in Dashboard shows the score event entry
8. **SSE stream** (if connected) shows the event in real time without waiting for the poll cycle

### Delay buffer verification

1. Set a 30-second delay on the team
2. When a score is detected in logs, start a timer
3. The effect should fire exactly 30 seconds after the log line `Score change detected`
4. During the 30-second window, `GET /api/health` should show `pending_delayed_events: 1`
5. After firing, it should drop back to `0`

---

## Appendix: Test Checklist

Use this checklist before any release:

### Backend
- [ ] `GET /api/health` returns `status: ok`
- [ ] All 13+ route groups appear in `/openapi.json`
- [ ] Follow/unfollow a team, verify scheduler starts/stops
- [ ] Set and read back config changes
- [ ] Upload and delete a custom sound
- [ ] Mute toggle changes `global_mute` in config
- [ ] Emergency stop returns `stopped_count` ≥ 0
- [ ] Sessions list returns `[]` when no games live
- [ ] Event types return ≥ 71 definitions
- [ ] Database persists across restart

### Web UI
- [ ] All 7 nav links work (Dashboard, Teams, Lights, Effects, Calendar, Sounds, Settings)
- [ ] Teams page shows `display_name` + logo/color dot in Followed Teams
- [ ] Delay slider label updates live in Teams page
- [ ] Sounds page lists built-in sounds
- [ ] Custom sound upload, playback, and delete work
- [ ] Settings mute button toggles state and reflects in API
- [ ] Settings emergency stop fires without error
- [ ] Dashboard auto-refreshes every 15s
- [ ] SSE score event shows as toast notification

### HA Integration
- [ ] Entities created for each followed team
- [ ] `gamesync.trigger_effect` service fires lights
- [ ] `gamesync_score` event appears on HA bus after effect trigger
- [ ] Sensors update within one poll cycle of a score change
