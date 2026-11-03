"""CSV export of incidents, with times in the service time zone (the format the reporting team asked for)."""

import csv
import io

import pytz

from incidentdesk.config import settings
from incidentdesk.models import Incident

COLUMNS = ["key", "service", "severity", "priority", "status", "opened", "resolved"]


def incidents_csv(incidents: list[Incident]) -> str:
    tz = pytz.timezone(settings().timezone)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(COLUMNS)
    for i in incidents:
        resolved = i.resolved_at.astimezone(tz).strftime("%Y-%m-%d %H:%M") if i.resolved_at else ""
        writer.writerow([i.key, i.service.slug, i.severity, i.priority, i.status,
                         i.opened_at.astimezone(tz).strftime("%Y-%m-%d %H:%M"), resolved])
    return out.getvalue()
