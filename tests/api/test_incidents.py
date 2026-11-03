import pytest

from incidentdesk.models import Service

pytestmark = pytest.mark.db


@pytest.fixture
def login(db):
    service = Service(slug="login-service", name="Login Service", team="identity", rotation="amer", customer_facing=True)
    db.add(service)
    db.commit()
    return service


def test_open_an_incident_during_the_day(client, login):
    r = client.post("/incidents", json={"service": "login-service", "title": " Login fails ", "severity": "major",
                                        "opened_at": "2026-10-13T19:00:00Z"})
    assert r.status_code == 201
    body = r.json()
    assert body["key"] == "INC-4801" and body["priority"] == "P1" and body["title"] == "Login fails"


def test_unknown_service_is_refused(client, login):
    r = client.post("/incidents", json={"service": "nope", "title": "x", "severity": "minor"})
    assert r.status_code == 422


def test_acknowledge_then_resolve(client, login):
    key = client.post("/incidents", json={"service": "login-service", "title": "Slow", "severity": "minor"}).json()["key"]
    assert client.post(f"/incidents/{key}/acknowledge").json()["status"] == "acknowledged"
    assert client.post(f"/incidents/{key}/acknowledge").status_code == 409
    assert client.post(f"/incidents/{key}/resolve", params={"note": "Restarted"}).json()["status"] == "resolved"
    kinds = [e["kind"] for e in client.get(f"/incidents/{key}/timeline").json()]
    assert kinds == ["opened", "acknowledged", "resolved"]


def test_list_filters_by_priority(client, login):
    client.post("/incidents", json={"service": "login-service", "title": "A", "severity": "cosmetic",
                                    "opened_at": "2026-10-13T19:00:00Z"})
    client.post("/incidents", json={"service": "login-service", "title": "B", "severity": "critical"})
    assert [i["title"] for i in client.get("/incidents", params={"priority": "P3"}).json()] == ["A"]


def test_sla_of_an_incident(client, login):
    key = client.post("/incidents", json={"service": "login-service", "title": "Down", "severity": "critical",
                                          "opened_at": "2026-10-13T19:00:00Z"}).json()["key"]
    sla = client.get(f"/incidents/{key}/sla").json()
    assert sla["response_due"].startswith("2026-10-13T19:15")
