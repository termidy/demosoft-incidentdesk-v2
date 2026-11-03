"""Uptime history for the status page: one bar per UTC day, the last 90 days."""

from datetime import date, datetime, timedelta

import pytz

from incidentdesk.models import Incident

DAYS = 90


def downtime_by_day(incidents: list[Incident], service_slug: str, today: date) -> dict[date, timedelta]:
    first = today - timedelta(days=DAYS - 1)
    history = {first + timedelta(days=n): timedelta(0) for n in range(DAYS)}
    for incident in incidents:
        if incident.service.slug != service_slug or incident.severity != "critical" or not incident.resolved_at:
            continue
        start = incident.opened_at.astimezone(pytz.utc)
        end = incident.resolved_at.astimezone(pytz.utc)
        while start < end:
            midnight = pytz.utc.localize(datetime.combine(start.date() + timedelta(days=1), datetime.min.time()))
            piece_end = min(end, midnight)
            if start.date() in history:
                history[start.date()] += piece_end - start
            start = piece_end
    return history


def uptime_percent(history: dict[date, timedelta]) -> float:
    down = sum((d.total_seconds() for d in history.values()), 0.0)
    return round(100 * (1 - down / (len(history) * 86400)), 3)
