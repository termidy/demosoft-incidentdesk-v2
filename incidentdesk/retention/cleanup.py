"""Retention: resolved incidents older than a year are archived; incidents with a postmortem are kept."""

from datetime import datetime, timedelta

import pytz

from incidentdesk.models import Incident

KEEP = timedelta(days=365)


def to_archive(incidents: list[Incident], with_postmortem: set[int], now: datetime) -> list[Incident]:
    cutoff = now.astimezone(pytz.utc) - KEEP
    return [
        i for i in incidents
        if i.status == "resolved" and i.resolved_at and i.resolved_at < cutoff and i.id not in with_postmortem
    ]
