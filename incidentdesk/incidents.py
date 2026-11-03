"""The life of an incident: open, acknowledge, wait on the customer, resume, resolve."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from incidentdesk.maintenance.windows import in_maintenance
from incidentdesk.models import Incident, MaintenanceWindow, Service, TimelineEvent
from incidentdesk.priority import compute_priority
from incidentdesk.routing import first_responders
from incidentdesk.timeutil import now


class InvalidTransition(Exception):
    pass


def next_key(session: Session) -> str:
    last = session.scalar(select(func.max(Incident.id))) or 0
    return f"INC-{4800 + last + 1}"


def open_incident(session: Session, service: Service, title: str, severity: str,
                  opened_at: datetime | None = None, source: str = "manual") -> Incident:
    opened_at = opened_at or now()
    windows = list(session.scalars(select(MaintenanceWindow).where(MaintenanceWindow.service_id == service.id)))
    priority = compute_priority(severity, service.customer_facing, opened_at, in_maintenance(service.id, opened_at, windows))
    incident = Incident(key=next_key(session), title=title.strip(), service=service, severity=severity,
                        priority=priority, status="open", source=source, opened_at=opened_at)
    responders = ", ".join(first_responders(service, priority, opened_at))
    incident.events.append(TimelineEvent(at=opened_at, kind="opened", note=f"Paged {responders}"))
    session.add(incident)
    session.commit()
    return incident


def _move(session: Session, incident: Incident, allowed: tuple[str, ...], status: str, note: str = "") -> Incident:
    if incident.status not in allowed:
        raise InvalidTransition(f"{incident.key} is {incident.status}, cannot become {status}")
    at = now()
    if incident.status == "waiting" and incident.waiting_since:
        incident.waiting_seconds += int((at - incident.waiting_since).total_seconds())
        incident.waiting_since = None
    if status == "acknowledged" and not incident.acknowledged_at:
        incident.acknowledged_at = at
    if status == "waiting":
        incident.waiting_since = at
    if status == "resolved":
        incident.resolved_at = at
    incident.status = status
    incident.events.append(TimelineEvent(at=at, kind=status, note=note))
    session.commit()
    return incident


def acknowledge(session: Session, incident: Incident) -> Incident:
    return _move(session, incident, ("open",), "acknowledged")


def wait_on_customer(session: Session, incident: Incident, note: str) -> Incident:
    return _move(session, incident, ("open", "acknowledged"), "waiting", note)


def resume(session: Session, incident: Incident) -> Incident:
    return _move(session, incident, ("waiting",), "acknowledged", "Customer replied")


def resolve(session: Session, incident: Incident, note: str) -> Incident:
    return _move(session, incident, ("open", "acknowledged", "waiting"), "resolved", note)
