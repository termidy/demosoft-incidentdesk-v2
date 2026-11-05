"""/postmortems"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from incidentdesk.db import get_session
from incidentdesk.models import Postmortem
from incidentdesk.postmortems import get_postmortem, list_postmortems
from incidentdesk.schemas import PostmortemOut

router = APIRouter(prefix="/postmortems", tags=["postmortems"])


def to_out(pm: Postmortem) -> PostmortemOut:
    return PostmortemOut(
        key=pm.key, incident=pm.incident.key, title=pm.title, summary=pm.summary, impact=pm.impact,
        root_cause=pm.root_cause, actions=pm.actions, author=pm.author, published_at=pm.published_at,
    )


@router.get("", response_model=list[PostmortemOut])
def postmortems(include_drafts: bool = False, session: Session = Depends(get_session)):
    return [to_out(pm) for pm in list_postmortems(session, published_only=not include_drafts)]


@router.get("/{key}", response_model=PostmortemOut)
def postmortem(key: str, session: Session = Depends(get_session)):
    pm = get_postmortem(session, key)
    if not pm:
        raise HTTPException(404, f"No postmortem {key}")
    return to_out(pm)
