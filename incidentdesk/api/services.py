"""/services and /health"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from incidentdesk import __version__
from incidentdesk.db import get_session
from incidentdesk.models import Service
from incidentdesk.schemas import ServiceOut

router = APIRouter(tags=["services"])


@router.get("/health")
def health(session: Session = Depends(get_session)):
    session.execute(text("select 1"))
    return {"status": "ok", "version": __version__}


@router.get("/services", response_model=list[ServiceOut])
def services(session: Session = Depends(get_session)):
    return list(session.scalars(select(Service).order_by(Service.slug)))
