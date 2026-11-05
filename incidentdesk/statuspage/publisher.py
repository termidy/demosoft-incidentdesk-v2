"""Public status page entries. The status page always shows UTC."""

from datetime import timezone

from incidentdesk.models import Incident

PUBLIC_STATE = {"open": "Investigating", "acknowledged": "Identified", "waiting": "Monitoring", "resolved": "Resolved"}


def status_entry(incident: Incident) -> dict | None:
    """Only customer-facing services appear on the status page, and only P1 and P2."""
    if not incident.service.customer_facing or incident.priority not in ("P1", "P2"):
        return None
    opened = incident.opened_at.astimezone(timezone.utc)
    entry = {
        "service": incident.service.name,
        "state": PUBLIC_STATE[incident.status],
        "since": opened.strftime("%Y-%m-%d %H:%M UTC"),
    }
    if incident.resolved_at:
        entry["resolved"] = incident.resolved_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return entry
