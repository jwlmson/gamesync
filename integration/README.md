# GameSync — Home Assistant Integration

> HACS custom integration that exposes [GameSync add-on](https://github.com/jwlmson/gamesync-addon) data as native Home Assistant entities, sensors, and events.

![HACS](https://img.shields.io/badge/HACS-custom-orange) ![HA Version](https://img.shields.io/badge/HA-2024.1%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

---

## What This Integration Does

The [GameSync add-on](https://github.com/jwlmson/gamesync-addon) handles score polling, light effects, and audio. This HACS integration bridges the add-on into the native HA entity ecosystem so you can:

- **Use scores in dashboards** — add game score cards to Lovelace
- **Trigger automations** — react to `gamesync_score` and other events natively
- **Check game state in conditions** — `binary_sensor.gamesync_eagles_live` is `on` during games
- **Call services** — `gamesync.trigger_effect`, `gamesync.set_delay` from any automation

---

## Installation

### Requirements
- [GameSync add-on](https://github.com/jwlmson/gamesync-addon) installed and running
- Home Assistant 2024.1+
- [HACS](https://hacs.xyz/) installed

### Install via HACS

1. Open HACS → **Integrations** → ⋮ → **Custom repositories**
2. Add URL: `https://github.com/jwlmson/gamesync-ha`
3. Category: **Integration**
4. Find **GameSync** in HACS and install
5. Restart Home Assistant
6. Go to **Settings → Integrations → + Add Integration → GameSync**

### Manual Install

```bash
# Copy to your HA config directory
cp -r custom_components/gamesync /config/custom_components/gamesync
```

Restart HA, then add the integration from Settings → Integrations.

---

## Configuration

The config flow auto-detects the GameSync add-on on `localhost:8099`. If you're running the add-on on a different host, enter it manually.

| Field | Default | Description |
|---|---|---|
| Host | `localhost` | Host where the GameSync add-on is running |
| Port | `8099` | Port of the GameSync add-on REST API |

---

## Entities

For each **followed team**, the integration creates:

### Sensors

| Entity ID | State | Description |
|---|---|---|
| `sensor.gamesync_{team}_score` | `"3 - 1"` or `"--"` | Current score as `away - home` |
| `sensor.gamesync_{team}_state` | `live` / `scheduled` / `final` / `off` | Game lifecycle state |

**Score sensor attributes:**
```yaml
home_score: 3
away_score: 1
my_score: 3          # score for the team you followed
opponent_score: 1
period: "Q3"
clock: "4:32"
game_id: "nfl:401547417"
opponent: "Dallas Cowboys"
venue: "Lincoln Financial Field"
broadcast: "FOX"
```

### Binary Sensors

| Entity ID | On when | Description |
|---|---|---|
| `binary_sensor.gamesync_{team}_live` | Game is in progress | Use in automations to gate effects |
| `binary_sensor.gamesync_{team}_winning` | Team is currently leading | Great for lighting scenes |

---

## Services

### `gamesync.trigger_effect`
Manually fire a light effect — useful for testing or custom automations.

```yaml
service: gamesync.trigger_effect
data:
  team_id: "nfl:21"          # optional — uses all lights if omitted
  event_type: "score_change" # score_change | game_start | game_end | period_start
```

### `gamesync.set_delay`
Update the anti-spoiler delay for a team at runtime.

```yaml
service: gamesync.set_delay
data:
  team_id: "nfl:21"
  delay_seconds: 45   # 0-120 seconds
```

### `gamesync.refresh`
Force an immediate game data refresh.

```yaml
service: gamesync.refresh
```

---

## Events

GameSync fires these events on the HA event bus. Use them as automation triggers:

| Event | Fires when |
|---|---|
| `gamesync_score` | A followed team scores |
| `gamesync_game_start` | A game begins |
| `gamesync_game_end` | A game ends |
| `gamesync_period_change` | Quarter/period/half changes |
| `gamesync_special` | Red zone entry, power play, safety car, cards |

### Event data fields

```yaml
# gamesync_score example
event_type: "score_change"
team_id: "nfl:21"
team_name: "Philadelphia Eagles"
league: "nfl"
home_score: 14
away_score: 7
scoring_type: "touchdown"   # touchdown | field_goal | goal | basket | run | etc.
game_id: "nfl:401547417"
timestamp: "2025-01-12T20:34:11+00:00"
```

---

## Example Automations

### Flash lights on any score for a followed team

```yaml
automation:
  - alias: "GameSync — Any Score Flash"
    trigger:
      - platform: event
        event_type: gamesync_score
    action:
      - service: gamesync.trigger_effect
        data:
          team_id: "{{ trigger.event.data.team_id }}"
          event_type: score_change
```

### Turn on game-day lighting scene when game goes live

```yaml
automation:
  - alias: "GameSync — Game Day Scene"
    trigger:
      - platform: state
        entity_id: binary_sensor.gamesync_eagles_live
        to: "on"
    action:
      - service: scene.turn_on
        target:
          entity_id: scene.game_day
```

### Announce final score via TTS

```yaml
automation:
  - alias: "GameSync — Final Score Announcement"
    trigger:
      - platform: event
        event_type: gamesync_game_end
        event_data:
          team_id: "nfl:21"
    action:
      - service: tts.speak
        target:
          entity_id: media_player.living_room
        data:
          message: >
            The Eagles game is over. Final score:
            {{ trigger.event.data.home_score }} to
            {{ trigger.event.data.away_score }}.
            {% if trigger.event.data.result == 'home_win' %}Fly Eagles Fly!{% endif %}
```

### Adjust delay before the game starts

```yaml
automation:
  - alias: "GameSync — Set NFL Delay at Kickoff"
    trigger:
      - platform: event
        event_type: gamesync_game_start
        event_data:
          league: "nfl"
    action:
      - service: gamesync.set_delay
        data:
          team_id: "{{ trigger.event.data.team_id }}"
          delay_seconds: 30
```

---

## Dashboard Cards

### Current score card (Markdown)

```yaml
type: markdown
content: |
  ## 🏈 Eagles
  **{{ states('sensor.gamesync_eagles_score') }}**
  {{ state_attr('sensor.gamesync_eagles_score', 'period') }}
  {{ state_attr('sensor.gamesync_eagles_score', 'clock') }}
```

### Conditional live indicator

```yaml
type: conditional
conditions:
  - condition: state
    entity: binary_sensor.gamesync_eagles_live
    state: "on"
card:
  type: entity
  entity: sensor.gamesync_eagles_score
  name: LIVE — Eagles
```

---

## Troubleshooting

**Integration shows "Cannot connect"**
- Make sure the GameSync add-on is running (check its log)
- Verify the host/port match (default: `localhost:8099`)
- Try `http://homeassistant.local:8099/api/health` in your browser

**Sensors show `--` or `off` during a live game**
- In the GameSync add-on UI, go to **Teams** and confirm the team is followed
- Check the add-on log for polling errors
- Use `gamesync.refresh` to force a poll

**No entities created after setup**
- Entities are created per followed team. Follow at least one team in the GameSync add-on UI first, then re-add the integration or restart HA.

**Events not firing**
- Events fire after the anti-spoiler delay. If you have a delay set, wait for it to expire.
- Check the **Events** page in the GameSync web UI to see the event log.

---

## Related

- **[GameSync Add-on](https://github.com/jwlmson/gamesync-addon)** — the add-on this integration connects to (install this first)

---

## License

MIT License — see [LICENSE](LICENSE) for details.
