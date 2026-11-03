"""Chat messages for the incident channel."""

import pytz

from incidentdesk.models import Incident, TimelineEvent

ICONS = {"P1": ":rotating_light:", "P2": ":warning:", "P3": ":large_yellow_circle:", "P4": ":white_circle:"}


def opened_message(incident: Incident, responders: list[str]) -> str:
    opened = incident.opened_at.astimezone(pytz.utc)
    who = ", ".join(responders)
    return f"{ICONS[incident.priority]} {incident.key} {incident.priority} {incident.title} - opened {opened:%H:%M} UTC, paging {who}"


def event_message(incident: Incident, event: TimelineEvent) -> str:
    at = event.at.astimezone(pytz.utc)
    return f"{incident.key} {event.kind} at {at:%H:%M} UTC: {event.note}".rstrip(": ")
