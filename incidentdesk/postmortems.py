"""Postmortems: what happened, why, and what we change."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from incidentdesk.models import Postmortem

REQUIRED_SECTIONS = ("summary", "impact", "root_cause", "actions")


def list_postmortems(session: Session, published_only: bool = True) -> list[Postmortem]:
    query = select(Postmortem).order_by(Postmortem.id.desc())
    if published_only:
        query = query.where(Postmortem.published_at.is_not(None))
    return list(session.scalars(query))


def get_postmortem(session: Session, key: str) -> Postmortem | None:
    return session.scalar(select(Postmortem).where(Postmortem.key == key))


def missing_sections(postmortem: Postmortem) -> list[str]:
    """A postmortem may be published only when every required section is filled in."""
    return [name for name in REQUIRED_SECTIONS if not getattr(postmortem, name)]
