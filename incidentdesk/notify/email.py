"""Email to the responders of an incident."""

from dataclasses import dataclass

import pytz

from incidentdesk.config import settings
from incidentdesk.models import Incident


@dataclass(frozen=True)
class Email:
    to: list[str]
    subject: str
    body: str


def incident_email(incident: Incident, recipients: list[str]) -> Email:
    tz = pytz.timezone(settings().timezone)
    opened = incident.opened_at.astimezone(tz)
    subject = f"[{incident.priority}] {incident.key} {incident.title}"
    body = "\n".join([
        f"Service: {incident.service.name}",
        f"Severity: {incident.severity}",
        f"Opened: {opened:%Y-%m-%d %H:%M %Z}",
        "",
        f"Acknowledge: https://incidentdesk.demosoft.example/incidents/{incident.key}",
    ])
    return Email(recipients, subject, body)
