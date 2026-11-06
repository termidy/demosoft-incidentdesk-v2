from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.models import Service

pytestmark = pytest.mark.db


@pytest.fixture
def login(db):
    service = Service(slug="login-service", name="Login Service", team="identity", rotation="amer", customer_facing=True)
    db.add(service)
    db.commit()
    return service


def _open_incident(client, title, opened_at):
    return client.post(
        "/incidents",
        json={"service": "login-service", "title": title, "severity": "major", "opened_at": opened_at.isoformat()},
    )


def test_mobile_list_matches_response_example(client, login):
    opened_at = datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc)
    response = _open_incident(client, "Login fails for some customers", opened_at)

    assert response.status_code == 201
    assert client.post(f"/incidents/{response.json()['key']}/acknowledge").status_code == 200
    result = client.get("/mobile/v1/incidents")
    assert result.status_code == 200
    assert result.json() == {
        "items": [
            {
                "key": "INC-4801",
                "title": "Login fails for some customers",
                "service": "login-service",
                "priority": "P1",
                "status": "acknowledged",
                "opened_at": "2026-10-13T19:00:00Z",
            }
        ],
        "next_page": None,
    }


def test_mobile_list_filters_sorts_and_paginates_unresolved_incidents(client, login):
    start = datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc)
    for index in range(21):
        assert _open_incident(client, f"Open {index}", start + timedelta(minutes=index)).status_code == 201
    acknowledged = _open_incident(client, "Acknowledged", start + timedelta(hours=1))
    assert acknowledged.status_code == 201
    assert client.post(f"/incidents/{acknowledged.json()['key']}/acknowledge").status_code == 200

    first_page = client.get("/mobile/v1/incidents")
    assert first_page.status_code == 200
    first_body = first_page.json()
    assert len(first_body["items"]) == 20
    assert first_body["next_page"] == 2
    assert [item["title"] for item in first_body["items"]] == [
        "Acknowledged",
        *[f"Open {index}" for index in reversed(range(2, 21))],
    ]
    assert first_body["items"][0]["status"] == "acknowledged"
    assert all(item["status"] != "resolved" for item in first_body["items"])

    second_page = client.get("/mobile/v1/incidents", params={"page": 2})
    assert second_page.status_code == 200
    assert [item["title"] for item in second_page.json()["items"]] == ["Open 1", "Open 0"]
    assert second_page.json()["next_page"] is None
