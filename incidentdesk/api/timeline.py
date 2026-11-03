"""/incidents/{key}/timeline"""

from datetime import datetime

import pytz
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from incidentdesk.api.incidents import find
from incidentdesk.db import get_session
from incidentdesk.schemas import TimelineEventOut

router = APIRouter(prefix="/incidents", tags=["timeline"])


@router.get("/{key}/timeline", response_model=list[TimelineEventOut])
def timeline(key: str, since: datetime | None = None, session: Session = Depends(get_session)):
    events = find(session, key).events
    if since:
        since = pytz.utc.localize(since) if since.tzinfo is None else since
        events = [e for e in events if e.at >= since]
    return events
