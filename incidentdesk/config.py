"""Settings from the environment, read once."""

import os
from dataclasses import dataclass
from functools import lru_cache
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    timezone: str


@lru_cache
def settings() -> Settings:
    tz_name = os.environ.get("INCIDENTDESK_TIMEZONE", "America/Chicago")
    ZoneInfo(tz_name)  # a typo fails here, not at the first incident
    return Settings(database_url=os.environ.get("DATABASE_URL"), timezone=tz_name)
