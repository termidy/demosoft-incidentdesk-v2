"""Load the demo data (data/demo/*.json) into the database."""

import json
from pathlib import Path

import pytz
from sqlalchemy.orm import Session

from incidentdesk.db import Base, engine
from incidentdesk.models import Incident, Postmortem, Service, TimelineEvent
from incidentdesk.timeutil import parse_utc

DEMO = Path(__file__).resolve().parent.parent / "data" / "demo"


def _time(value: str | None):
    return parse_utc(value).astimezone(pytz.utc) if value else None


def load(name: str) -> list[dict]:
    return json.loads((DEMO / f"{name}.json").read_text())


def seed(reset: bool = False) -> dict[str, int]:
    if reset:
        Base.metadata.drop_all(engine())
    Base.metadata.create_all(engine())
    with Session(engine()) as session:
        services = {s["slug"]: Service(**s) for s in load("services")}
        session.add_all(services.values())
        incidents = {}
        for row in load("incidents"):
            incident = Incident(
                key=row["key"], title=row["title"], service=services[row["service"]], severity=row["severity"],
                priority=row["priority"], status=row["status"], source=row["source"],
                opened_at=_time(row["opened_at"]), acknowledged_at=_time(row["acknowledged_at"]),
                resolved_at=_time(row["resolved_at"]), waiting_seconds=row["waiting_seconds"],
            )
            incident.events = [TimelineEvent(at=_time(e["at"]), kind=e["kind"], note=e["note"]) for e in row["timeline"]]
            incidents[row["key"]] = incident
        session.add_all(incidents.values())
        for row in load("postmortems"):
            session.add(Postmortem(**{**row, "incident": incidents[row["incident"]], "published_at": _time(row["published_at"])}))
        session.commit()
    return {"services": len(services), "incidents": len(incidents)}
