from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.models import Incident, Service, TimelineEvent

pytestmark = pytest.mark.db


@pytest.fixture
def login_service(db):
    service = Service(
        slug="login-service",
        name="Login Service",
        team="identity",
        rotation="amer",
        customer_facing=True,
    )
    db.add(service)
    db.commit()
    return service


def _list_item(key, title, priority, status, opened_at):
    return {
        "key": key,
        "title": title,
        "service": "login-service",
        "priority": priority,
        "status": status,
        "opened_at": opened_at.isoformat().replace("+00:00", "Z"),
    }


def test_mobile_list_contract(client, db, login_service):
    start = datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc)
    incidents = []
    for index in range(21):
        opened_at = start + timedelta(minutes=index)
        status = "acknowledged" if index == 20 else "open"
        priority = ("P1", "P2", "P3", "P4")[index % 4]
        incidents.append(
            Incident(
                key=f"INC-{4801 + index}",
                title=f"Incident {index:02}",
                service=login_service,
                severity="major",
                priority=priority,
                status=status,
                opened_at=opened_at,
            )
        )
    db.add_all(incidents)
    db.commit()

    first_page = client.get("/mobile/v1/incidents")
    assert first_page.status_code == 200
    expected_items = [
        _list_item(
            f"INC-{4801 + index}",
            f"Incident {index:02}",
            ("P1", "P2", "P3", "P4")[index % 4],
            "acknowledged" if index == 20 else "open",
            start + timedelta(minutes=index),
        )
        for index in reversed(range(1, 21))
    ]
    assert first_page.json() == {"items": expected_items, "next_page": 2}

    second_page = client.get("/mobile/v1/incidents", params={"page": 2})
    assert second_page.status_code == 200
    assert second_page.json() == {
        "items": [_list_item("INC-4801", "Incident 00", "P1", "open", start)],
        "next_page": None,
    }


def test_mobile_incident_detail_contract(client, db, login_service):
    opened_at = datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc)
    incident = Incident(
        key="INC-4821",
        title="Login fails for some customers",
        service=login_service,
        severity="major",
        priority="P1",
        status="acknowledged",
        opened_at=opened_at,
        events=[
            TimelineEvent(at=opened_at, kind="opened", note=""),
            TimelineEvent(
                at=opened_at + timedelta(minutes=1),
                kind="acknowledged",
                note="",
            ),
        ],
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
        "timeline": [
            {"at": "2026-10-13T19:00:00Z", "kind": "opened", "note": ""},
            {
                "at": "2026-10-13T19:01:00Z",
                "kind": "acknowledged",
                "note": "",
            },
        ],
    }


def test_mobile_incident_not_found_contract(client):
    response = client.get("/mobile/v1/incidents/INC-9999")

    assert response.status_code == 404
    assert response.json() == {"error": "not_found"}


def test_mobile_subscription_contract(client, login_service):
    request_body = {
        "engineer": "a.reyes",
        "services": ["login-service"],
        "min_priority": "P2",
    }
    response = client.post("/mobile/v1/subscriptions", json=request_body)

    assert response.status_code == 201
    subscription_id = response.json()["id"]
    assert isinstance(subscription_id, int)
    expected_subscription = {
        "id": subscription_id,
        "engineer": "a.reyes",
        "services": ["login-service"],
        "min_priority": "P2",
    }
    assert response.json() == expected_subscription

    listed = client.get(
        "/mobile/v1/subscriptions",
        params={"engineer": "a.reyes"},
    )
    assert listed.status_code == 200
    assert listed.json() == [expected_subscription]


def test_mobile_unknown_service_contract(client):
    response = client.post(
        "/mobile/v1/subscriptions",
        json={
            "engineer": "a.reyes",
            "services": ["unknown-service"],
            "min_priority": "P2",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Unknown service unknown-service"}
