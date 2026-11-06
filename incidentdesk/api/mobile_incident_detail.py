"""/mobile/v1/incidents/{key}"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from incidentdesk.api.mobile_incidents import MobileIncidentOut
from incidentdesk.db import get_session
from incidentdesk.models import Incident
from incidentdesk.schemas import TimelineEventOut

router = APIRouter(prefix="/mobile/v1/incidents", tags=["mobile incidents"])


class MobileIncidentDetailOut(MobileIncidentOut):
    timeline: list[TimelineEventOut]


@router.get("/{key}", response_model=MobileIncidentDetailOut)
def get_incident_detail(key: str, session: Session = Depends(get_session)):
    incident = session.scalar(select(Incident).where(Incident.key == key))
    if incident is None:
        return JSONResponse(status_code=404, content={"error": "not_found"})

    return MobileIncidentDetailOut(
        key=incident.key,
        title=incident.title,
        service=incident.service.slug,
        priority=incident.priority,
        status=incident.status,
        opened_at=incident.opened_at,
        timeline=sorted(incident.events, key=lambda event: event.at),
    )
