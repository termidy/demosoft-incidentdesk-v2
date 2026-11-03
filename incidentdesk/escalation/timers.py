"""When the next escalation step fires for an unacknowledged incident."""

from datetime import datetime

import pytz

from incidentdesk.escalation.policy import Step, steps_for
from incidentdesk.models import Incident


def due_steps(incident: Incident, now: datetime) -> list[Step]:
    """Steps whose time has come. Acknowledging stops escalation."""
    if incident.acknowledged_at or incident.status == "resolved":
        return []
    opened = incident.opened_at.astimezone(pytz.utc)
    return [step for step in steps_for(incident.priority) if opened + step.after <= now]


def next_escalation(incident: Incident, now: datetime) -> datetime | None:
    if incident.acknowledged_at or incident.status == "resolved":
        return None
    opened = incident.opened_at.astimezone(pytz.utc)
    upcoming = [opened + step.after for step in steps_for(incident.priority) if opened + step.after > now]
    return min(upcoming) if upcoming else None
