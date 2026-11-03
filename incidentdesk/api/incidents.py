"""/incidents"""

from datetime import datetime

import pytz
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from incidentdesk import incidents as lifecycle
from incidentdesk.db import get_session
from incidentdesk.models import Incident, Service
from incidentdesk.schemas import IncidentIn, IncidentOut, SlaOut
from incidentdesk.sla import sla_status
from incidentdesk.timeutil import now

router = APIRouter(prefix="/incidents", tags=["incidents"])


def to_out(incident: Incident) -> IncidentOut:
    return IncidentOut(
        key=incident.key, title=incident.title, service=incident.service.slug, severity=incident.severity,
        priority=incident.priority, status=incident.status, source=incident.source, opened_at=incident.opened_at,
        acknowledged_at=incident.acknowledged_at, resolved_at=incident.resolved_at,
    )


def find(session: Session, key: str) -> Incident:
    incident = session.scalar(select(Incident).where(Incident.key == key))
    if not incident:
        raise HTTPException(404, f"No incident {key}")
    return incident


def _utc(value: datetime) -> datetime:
    return pytz.utc.localize(value) if value.tzinfo is None else value.astimezone(pytz.utc)


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    status: str | None = None,
    service: str | None = None,
    priority: str | None = None,
    opened_after: datetime | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    session: Session = Depends(get_session),
):
    query = select(Incident).join(Service).order_by(Incident.opened_at.desc())
    if status:
        query = query.where(Incident.status == status)
    if service:
        query = query.where(Service.slug == service)
    if priority:
        query = query.where(Incident.priority == priority)
    if opened_after:
        query = query.where(Incident.opened_at >= _utc(opened_after))
    return [to_out(i) for i in session.scalars(query.limit(limit).offset(offset))]


@router.post("", response_model=IncidentOut, status_code=201)
def create_incident(body: IncidentIn, session: Session = Depends(get_session)):
    service = session.scalar(select(Service).where(Service.slug == body.service))
    if not service:
        raise HTTPException(422, f"Unknown service {body.service}")
    opened_at = _utc(body.opened_at) if body.opened_at else None
    return to_out(lifecycle.open_incident(session, service, body.title, body.severity, opened_at))


@router.get("/{key}", response_model=IncidentOut)
def get_incident(key: str, session: Session = Depends(get_session)):
    return to_out(find(session, key))


@router.get("/{key}/sla", response_model=SlaOut)
def get_sla(key: str, session: Session = Depends(get_session)):
    status = sla_status(find(session, key), now())
    return SlaOut(**status.__dict__)


@router.post("/{key}/acknowledge", response_model=IncidentOut)
def acknowledge(key: str, session: Session = Depends(get_session)):
    try:
        return to_out(lifecycle.acknowledge(session, find(session, key)))
    except lifecycle.InvalidTransition as e:
        raise HTTPException(409, str(e))


@router.post("/{key}/resolve", response_model=IncidentOut)
def resolve(key: str, note: str = "", session: Session = Depends(get_session)):
    try:
        return to_out(lifecycle.resolve(session, find(session, key), note))
    except lifecycle.InvalidTransition as e:
        raise HTTPException(409, str(e))
