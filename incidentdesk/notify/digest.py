"""The morning digest: sent at 08:00 in each recipient's own time zone."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from incidentdesk.models import Incident

DIGEST_TIME = time(8, 0)


def next_digest_at(recipient_tz: str, now: datetime) -> datetime:
    tz = ZoneInfo(recipient_tz)
    local = now.astimezone(tz)
    send = datetime.combine(local.date(), DIGEST_TIME).replace(tzinfo=tz)
    if send <= local:
        send = datetime.combine(local.date() + timedelta(days=1), DIGEST_TIME).replace(tzinfo=tz)
    return send


def digest(incidents: list[Incident], recipient_tz: str, now: datetime) -> str:
    tz = ZoneInfo(recipient_tz)
    since = now - timedelta(hours=24)
    recent = [i for i in incidents if i.opened_at >= since]
    lines = [f"IncidentDesk digest - {now.astimezone(tz):%A %d %B}", f"{len(recent)} incidents in the last 24 hours"]
    for incident in sorted(recent, key=lambda i: i.opened_at):
        lines.append(f"- {incident.opened_at.astimezone(tz):%H:%M} {incident.key} {incident.priority} {incident.status}")
    return "\n".join(lines)
