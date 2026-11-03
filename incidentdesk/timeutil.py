"""Time helpers. Times are stored in UTC; business rules use the service time zone."""

import os
from datetime import datetime

import pytz

from incidentdesk.config import settings

UTC = pytz.utc


def service_tz():
    return pytz.timezone(settings().timezone)


def now() -> datetime:
    """The current time in UTC. INCIDENTDESK_NOW pins it (demo data and tests)."""
    pinned = os.environ.get("INCIDENTDESK_NOW")
    if pinned:
        return parse_utc(pinned)
    return datetime.now(UTC)


def parse_utc(text: str) -> datetime:
    """An ISO 8601 string as an aware UTC datetime; a string without an offset is taken as UTC."""
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return UTC.localize(dt)
    return dt.astimezone(UTC)


def to_local(dt: datetime) -> datetime:
    return service_tz().normalize(dt.astimezone(service_tz()))


def local_datetime(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """A wall-clock time in the service time zone, as an aware datetime."""
    return service_tz().localize(datetime(year, month, day, hour, minute))


def is_business_hours(dt: datetime) -> bool:
    local = to_local(dt)
    return local.weekday() < 5 and 9 <= local.hour < 18
