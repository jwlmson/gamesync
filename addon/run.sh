#!/usr/bin/with-contenv bashio

CONFIG_PATH=/data/options.json
LOG_LEVEL=$(bashio::config 'log_level')

export GAMESYNC_LOG_LEVEL="${LOG_LEVEL}"
export GAMESYNC_DATA_PATH="/data"
export GAMESYNC_OPTIONS_PATH="${CONFIG_PATH}"

exec uvicorn gamesync.main:app \
    --host 0.0.0.0 \
    --port 8099 \
    --log-level "${LOG_LEVEL}" \
    --no-access-log
