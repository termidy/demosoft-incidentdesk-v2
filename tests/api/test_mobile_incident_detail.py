from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.models import Incident, Service, TimelineEvent

pytestmark = pytest.mark.db


def test_mobile_incident_detail_includes_timeline_oldest_first(client, db):
    opened_at = datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc)
    service = Service(
        slug="login-service",
        name="Login Service",
        team="identity",
        rotation="amer",
        customer_facing=True,
    )
    incident = Incident(
        key="INC-4821",
        title="Login fails for some customers",
        service=service,
        severity="major",
        priority="P1",
        status="acknowledged",
        opened_at=opened_at,
        events=[
            TimelineEvent(at=opened_at + timedelta(minutes=1), kind="acknowledged", note=""),
            TimelineEvent(at=opened_at, kind="opened", note=""),
        ],
    )
    db.add(incident)
    db.commit()

    response = client.get("/mobile/v1/incidents/INC-4821")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"key", "title", "service", "priority", "status", "opened_at", "timeline"}
    assert body["key"] == "INC-4821"
    assert body["title"] == "Login fails for some customers"
    assert body["service"] == "login-service"
    assert body["priority"] == "P1"
    assert body["status"] == "acknowledged"
    assert body["opened_at"].startswith("2026-10-13T19:00:00")
    assert [event["kind"] for event in body["timeline"]] == ["opened", "acknowledged"]
    assert [event["note"] for event in body["timeline"]] == ["", ""]


def test_mobile_incident_detail_matches_response_example(client, db):
    """Proves: the incident detail endpoint preserves every field in issue #42's example."""
    opened_at = datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc)
    service = Service(
        slug="login-service",
        name="Login Service",
        team="identity",
        rotation="amer",
        customer_facing=True,
    )
    incident = Incident(
        key="INC-4821",
        title="Login fails for some customers",
        service=service,
        severity="major",
        priority="P1",
        status="acknowledged",
        opened_at=opened_at,
        events=[TimelineEvent(at=opened_at, kind="opened", note="")],
    )
    db.add(incident)
    db.commit()

    response = client.get("/mobile/v1/incidents/INC-4821")

    assert response.status_code == 200
    assert response.json() == {
        "key": "INC-4821",
        "title": "Login fails for some customers",
        "service": "login-service",
        "priority": "P1",
        "status": "acknowledged",
        "opened_at": "2026-10-13T19:00:00Z",
        "timeline": [{"at": "2026-10-13T19:00:00Z", "kind": "opened", "note": ""}],
    }


def test_mobile_incident_detail_returns_not_found(client):
    response = client.get("/mobile/v1/incidents/INC-9999")

    assert response.status_code == 404
    assert response.json() == {"error": "not_found"}
