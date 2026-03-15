"""Constants for the GameSync integration."""

DOMAIN = "gamesync"

CONF_ADDON_HOST = "addon_host"
CONF_ADDON_PORT = "addon_port"

DEFAULT_ADDON_HOST = "localhost"
DEFAULT_ADDON_PORT = 8099

# Platforms
PLATFORMS = ["sensor", "binary_sensor"]

# HA Events
EVENT_SCORE = "gamesync_score"
EVENT_GAME_START = "gamesync_game_start"
EVENT_GAME_END = "gamesync_game_end"
EVENT_PERIOD_CHANGE = "gamesync_period_change"
EVENT_SPECIAL = "gamesync_special"
EVENT_MUTE_CHANGED = "gamesync_mute_changed"
EVENT_SESSION_CHANGED = "gamesync_session_changed"

# Services
SERVICE_TRIGGER_EFFECT = "trigger_effect"
SERVICE_SET_DELAY = "set_delay"
SERVICE_EMERGENCY_STOP = "emergency_stop"
SERVICE_MUTE_TOGGLE = "mute_toggle"
SERVICE_SET_PRIMARY_SESSION = "set_primary_session"
SERVICE_REFRESH = "refresh"

# Update interval (seconds)
UPDATE_INTERVAL = 30
