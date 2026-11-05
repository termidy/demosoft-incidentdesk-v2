import pytest

from incidentdesk.seed import seed

pytestmark = pytest.mark.db


def test_demo_data_loads(db):
    counts = seed(reset=True)
    assert counts["services"] == 12 and counts["incidents"] > 200


def test_published_postmortems_only_by_default(client):
    seed(reset=True)
    published = client.get("/postmortems").json()
    everything = client.get("/postmortems", params={"include_drafts": True}).json()
    assert len(everything) > len(published)
    assert all(pm["published_at"] for pm in published)


def test_postmortem_by_key(client):
    seed(reset=True)
    key = client.get("/postmortems").json()[0]["key"]
    pm = client.get(f"/postmortems/{key}").json()
    assert pm["key"] == key and pm["incident"].startswith("INC-")
    assert client.get("/postmortems/PM-1").status_code == 404
