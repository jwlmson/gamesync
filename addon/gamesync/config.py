"""Application configuration loaded from HA add-on options."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    log_level: str = "info"
    data_path: str = "/data"
    options_path: str = "/data/options.json"
    supervisor_token: str = ""
    supervisor_url: str = "http://supervisor/core/api"

    # Loaded from options.json
    api_football_key: str = ""

    class Config:
        env_prefix = "GAMESYNC_"

    @property
    def db_path(self) -> str:
        return os.path.join(self.data_path, "gamesync.db")

    @classmethod
    def load(cls) -> "Settings":
        """Load settings, merging env vars with HA options.json."""
        settings = cls(
            supervisor_token=os.environ.get("SUPERVISOR_TOKEN", ""),
        )
        options_path = Path(settings.options_path)
        if options_path.exists():
            with open(options_path) as f:
                options = json.load(f)
            if options.get("api_football_key"):
                settings.api_football_key = options["api_football_key"]
            if options.get("log_level"):
                settings.log_level = options["log_level"]
        return settings


# Singleton
_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings
