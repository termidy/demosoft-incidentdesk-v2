"""Maintenance windows: planned work during which a service is expected to misbehave.

One-off windows are stored in the database. Every service also has a weekly window, written in wall-clock time of the
service time zone (Sunday 02:00-04:00), so it moves with daylight saving time.
"""

from datetime import datetime, time, timedelta

import pytz

from incidentdesk.config import settings
from incidentdesk.models import MaintenanceWindow

WEEKLY_DAY = 6  # Sunday
WEEKLY_START = time(2, 0)
WEEKLY_HOURS = 2


def weekly_window(at: datetime) -> tuple[datetime, datetime]:
    """The weekly window of the week that contains `at`."""
    tz = pytz.timezone(settings().timezone)
    local = at.astimezone(tz)
    sunday = local.date() + timedelta(days=(WEEKLY_DAY - local.weekday()) % 7)
    if sunday > local.date():
        sunday -= timedelta(days=7)
    start = tz.localize(datetime.combine(sunday, WEEKLY_START))
    return start, start + timedelta(hours=WEEKLY_HOURS)


def in_maintenance(service_id: int, at: datetime, windows: list[MaintenanceWindow]) -> bool:
    start, end = weekly_window(at)
    if start <= at < end:
        return True
    return any(w.service_id == service_id and w.starts_at <= at < w.ends_at for w in windows)
