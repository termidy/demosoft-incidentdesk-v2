import os
from datetime import datetime

import pytest
import pytz

from incidentdesk.config import settings
from incidentdesk.models import Incident, Service

CHICAGO = pytz.timezone("America/Chicago")


@pytest.fixture(autouse=True)
def service_timezone(monkeypatch):
    monkeypatch.setenv("INCIDENTDESK_TIMEZONE", "America/Chicago")
    settings.cache_clear()
    yield
    settings.cache_clear()


def chicago(year, month, day, hour=0, minute=0) -> datetime:
    """A wall-clock time in Chicago, the service time zone of the tests."""
    return CHICAGO.localize(datetime(year, month, day, hour, minute))


def make_service(slug="login-service", customer_facing=True, team="identity", rotation="amer") -> Service:
    return Service(id=1, slug=slug, name=slug.replace("-", " ").title(), team=team, rotation=rotation,
                   customer_facing=customer_facing)


def make_incident(key="INC-4821", priority="P2", severity="major", status="open", opened_at=None,
                  service=None, **fields) -> Incident:
    return Incident(key=key, title="Login fails for some customers", severity=severity, priority=priority,
                    status=status, opened_at=opened_at or chicago(2026, 10, 13, 14, 0), service=service or make_service(),
                    waiting_seconds=fields.pop("waiting_seconds", 0), **fields)


def pytest_collection_modifyitems(config, items):
    if os.environ.get("DATABASE_URL"):
        return
    skip = pytest.mark.skip(reason="needs DATABASE_URL (PostgreSQL)")
    for item in items:
        if "db" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def db():
    """An empty database for one test."""
    from incidentdesk.db import Base, engine, session

    Base.metadata.drop_all(engine())
    Base.metadata.create_all(engine())
    with session() as s:
        yield s


@pytest.fixture
def client(db):
    from fastapi.testclient import TestClient

    from incidentdesk.app import create_app

    return TestClient(create_app())
