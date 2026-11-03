"""The daily report: incidents of one calendar day in the service time zone."""

from collections import Counter
from datetime import date, datetime, timedelta

import pytz

from incidentdesk.config import settings
from incidentdesk.models import Incident


def day_bounds(day: date) -> tuple[datetime, datetime]:
    """Start and end of a local calendar day, in UTC. A daylight saving day is 23 or 25 hours long."""
    tz = pytz.timezone(settings().timezone)
    start = tz.localize(datetime.combine(day, datetime.min.time()))
    end = tz.localize(datetime.combine(day + timedelta(days=1), datetime.min.time()))
    return start.astimezone(pytz.utc), end.astimezone(pytz.utc)


def daily_report(incidents: list[Incident], day: date) -> dict:
    start, end = day_bounds(day)
    today = [i for i in incidents if start <= i.opened_at < end]
    return {
        "day": day.isoformat(),
        "opened": len(today),
        "by_priority": dict(sorted(Counter(i.priority for i in today).items())),
        "still_open": sum(1 for i in today if i.status != "resolved"),
    }
