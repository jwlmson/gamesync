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

# Update interval (seconds)
UPDATE_INTERVAL = 30
