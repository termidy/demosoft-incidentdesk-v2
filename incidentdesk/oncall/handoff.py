"""The handoff note: what the next on-call engineer inherits."""

from datetime import datetime

import pytz

from incidentdesk.models import Incident
from incidentdesk.oncall.schedule import ROTATIONS


def handoff_note(rotation_name: str, at: datetime, incidents: list[Incident]) -> str:
    tz = pytz.timezone(ROTATIONS[rotation_name].timezone)
    open_ones = [i for i in incidents if i.status != "resolved" and i.service.rotation == rotation_name]
    lines = [f"Handoff {rotation_name} - {at.astimezone(tz):%a %d %b %H:%M %Z}"]
    if not open_ones:
        lines.append("No open incidents.")
    for incident in sorted(open_ones, key=lambda i: (i.priority, i.opened_at)):
        opened = incident.opened_at.astimezone(tz)
        lines.append(f"- {incident.key} {incident.priority} {incident.title} (open since {opened:%a %H:%M})")
    return "\n".join(lines)
