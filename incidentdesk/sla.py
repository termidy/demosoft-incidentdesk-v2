"""SLA targets and breaches (docs/sla.md)."""

from dataclasses import dataclass
from datetime import datetime, timedelta

import pytz

from incidentdesk.models import Incident

RESPONSE = {"P1": timedelta(minutes=15), "P2": timedelta(minutes=30), "P3": timedelta(hours=4), "P4": timedelta(days=1)}
RESOLUTION = {"P1": timedelta(hours=4), "P2": timedelta(hours=8), "P3": timedelta(days=3), "P4": timedelta(days=10)}


@dataclass(frozen=True)
class SlaStatus:
    response_due: datetime
    resolution_due: datetime
    response_breached: bool
    resolution_breached: bool


def waiting_time(incident: Incident, now: datetime) -> timedelta:
    waited = timedelta(seconds=incident.waiting_seconds)
    if incident.status == "waiting" and incident.waiting_since:
        waited += now - incident.waiting_since
    return waited


def sla_status(incident: Incident, now: datetime) -> SlaStatus:
    opened = incident.opened_at.astimezone(pytz.utc)
    response_due = opened + RESPONSE[incident.priority]
    resolution_due = opened + RESOLUTION[incident.priority] + waiting_time(incident, now)

    if incident.acknowledged_at:
        response_breached = incident.acknowledged_at > response_due
    else:
        response_breached = now > response_due

    if incident.resolved_at:
        resolution_breached = incident.resolved_at > resolution_due
    else:
        resolution_breached = now > resolution_due

    return SlaStatus(response_due, resolution_due, response_breached, resolution_breached)


def breaches(incidents: list[Incident], now: datetime) -> list[tuple[str, str]]:
    """(incident key, target) for every breached target."""
    found = []
    for incident in incidents:
        status = sla_status(incident, now)
        if status.response_breached:
            found.append((incident.key, "response"))
        if status.resolution_breached:
            found.append((incident.key, "resolution"))
    return found
