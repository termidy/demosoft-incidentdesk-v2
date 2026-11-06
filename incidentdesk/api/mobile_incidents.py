"""Mobile incident-list API."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from incidentdesk.db import get_session
from incidentdesk.models import Incident

router = APIRouter(prefix="/mobile/v1/incidents", tags=["mobile"])


class MobileIncidentOut(BaseModel):
    key: str
    title: str
    service: str
    priority: str
    status: str
    opened_at: datetime


class MobileIncidentListOut(BaseModel):
    items: list[MobileIncidentOut]
    next_page: int | None


@router.get("", response_model=MobileIncidentListOut)
def list_incidents(page: int = Query(1, ge=1), session: Session = Depends(get_session)):
    query = (
        select(Incident)
        .options(selectinload(Incident.service))
        .where(Incident.status != "resolved")
        .order_by(Incident.opened_at.desc(), Incident.id.desc())
        .offset((page - 1) * 20)
        .limit(21)
    )
    incidents = list(session.scalars(query))
    items = [
        MobileIncidentOut(
            key=incident.key,
            title=incident.title,
            service=incident.service.slug,
            priority=incident.priority,
            status=incident.status,
            opened_at=incident.opened_at,
        )
        for incident in incidents[:20]
    ]
    return MobileIncidentListOut(items=items, next_page=page + 1 if len(incidents) > 20 else None)
