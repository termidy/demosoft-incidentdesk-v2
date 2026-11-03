"""Request and response bodies of the API."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

Severity = Literal["critical", "major", "minor", "cosmetic"]


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    team: str
    rotation: str
    customer_facing: bool


class IncidentIn(BaseModel):
    service: str
    title: str
    severity: Severity
    opened_at: datetime | None = None


class IncidentOut(BaseModel):
    key: str
    title: str
    service: str
    severity: str
    priority: str
    status: str
    source: str
    opened_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None


class TimelineEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    at: datetime
    kind: str
    note: str


class SlaOut(BaseModel):
    response_due: datetime
    resolution_due: datetime
    response_breached: bool
    resolution_breached: bool


class PostmortemOut(BaseModel):
    key: str
    incident: str
    title: str
    summary: str
    impact: str
    root_cause: str | None
    actions: list[str]
    author: str
    published_at: datetime | None
