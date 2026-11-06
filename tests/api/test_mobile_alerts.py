import pytest

from incidentdesk.models import Service
from incidentdesk.mobile_subscriptions import MobileSubscription

pytestmark = pytest.mark.db


@pytest.fixture
def login(db):
    service = Service(slug="login-service", name="Login Service", team="identity", rotation="amer",
                      customer_facing=True)
    db.add(service)
    db.commit()
    return service


def test_create_and_list_subscriptions(client, db, login):
    response = client.post(
        "/mobile/v1/subscriptions",
        json={"engineer": "a.reyes", "services": ["login-service"], "min_priority": "P2"},
    )

    assert response.status_code == 201
    subscription = response.json()
    assert subscription["id"]
    assert subscription["engineer"] == "a.reyes"
    assert subscription["services"] == ["login-service"]
    assert subscription["min_priority"] == "P2"
    assert client.get("/mobile/v1/subscriptions", params={"engineer": "a.reyes"}).json() == [subscription]
    assert db.get(MobileSubscription, subscription["id"]) is not None


def test_unknown_service_is_refused(client, login):
    response = client.post(
        "/mobile/v1/subscriptions",
        json={"engineer": "a.reyes", "services": ["unknown-service"], "min_priority": "P2"},
    )

    assert response.status_code == 422
