"""Database tables."""

from datetime import datetime

import pytz
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from incidentdesk.db import Base


def _utcnow() -> datetime:
    return datetime.now(pytz.utc)


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    team: Mapped[str] = mapped_column(String(60))
    rotation: Mapped[str] = mapped_column(String(20))
    customer_facing: Mapped[bool] = mapped_column(Boolean, default=False)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(20), unique=True)  # INC-4821
    title: Mapped[str] = mapped_column(String(200))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    severity: Mapped[str] = mapped_column(String(20))  # critical, major, minor, cosmetic
    priority: Mapped[str] = mapped_column(String(2))  # P1..P4
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, acknowledged, waiting, resolved
    source: Mapped[str] = mapped_column(String(20), default="manual")
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    waiting_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    waiting_seconds: Mapped[int] = mapped_column(Integer, default=0)

    service: Mapped[Service] = relationship()
    events: Mapped[list["TimelineEvent"]] = relationship(back_populates="incident", order_by="TimelineEvent.at")


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"))
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    kind: Mapped[str] = mapped_column(String(30))  # opened, acknowledged, note, waiting, resumed, resolved
    note: Mapped[str] = mapped_column(Text, default="")

    incident: Mapped[Incident] = relationship(back_populates="events")


class Postmortem(Base):
    __tablename__ = "postmortems"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(20), unique=True)  # PM-117
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"))
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    impact: Mapped[str] = mapped_column(Text)
    root_cause: Mapped[str | None] = mapped_column(Text)
    actions: Mapped[list] = mapped_column(JSON, default=list)
    author: Mapped[str] = mapped_column(String(80))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    incident: Mapped[Incident] = relationship()


class MaintenanceWindow(Base):
    __tablename__ = "maintenance_windows"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(200))
