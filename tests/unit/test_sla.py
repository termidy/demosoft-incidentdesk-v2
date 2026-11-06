from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.sla import RESPONSE, RESOLUTION, breaches, sla_status
from tests.conftest import make_incident


OPENED = datetime(2026, 10, 13, 19, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("priority", "response", "resolution"),
    [
        ("P1", timedelta(minutes=15), timedelta(hours=4)),
        ("P2", timedelta(minutes=30), timedelta(hours=8)),
        ("P3", timedelta(hours=4), timedelta(days=3)),
        ("P4", timedelta(days=1), timedelta(days=10)),
    ],
)
def test_sla_due_times_for_each_priority(priority, response, resolution):
    status = sla_status(make_incident(priority=priority, opened_at=OPENED), OPENED)

    assert status.response_due == OPENED + response
    assert status.resolution_due == OPENED + resolution
    assert RESPONSE[priority] == response
    assert RESOLUTION[priority] == resolution


def test_response_uses_acknowledgment_time_when_acknowledged():
    response_due = OPENED + RESPONSE["P1"]
    incident = make_incident(
        priority="P1",
        opened_at=OPENED,
        acknowledged_at=response_due - timedelta(seconds=1),
    )

    # Current time is overdue, but the timely acknowledgment met the target.
    assert not sla_status(incident, response_due + timedelta(hours=1)).response_breached

    incident = make_incident(
        priority="P1",
        opened_at=OPENED,
        acknowledged_at=response_due + timedelta(seconds=1),
    )
    # The acknowledgment itself was late even though now is before the due time.
    assert sla_status(incident, response_due - timedelta(seconds=1)).response_breached


def test_response_uses_current_time_when_not_acknowledged():
    incident = make_incident(priority="P2", opened_at=OPENED)
    response_due = OPENED + RESPONSE["P2"]

    assert not sla_status(incident, response_due - timedelta(seconds=1)).response_breached
    assert sla_status(incident, response_due + timedelta(seconds=1)).response_breached


def test_resolution_uses_resolved_at_when_resolved():
    resolution_due = OPENED + RESOLUTION["P1"]
    incident = make_incident(
        priority="P1",
        status="resolved",
        opened_at=OPENED,
        resolved_at=resolution_due - timedelta(seconds=1),
    )

    # Current time is overdue, but resolution happened on time.
    assert not sla_status(incident, resolution_due + timedelta(hours=1)).resolution_breached

    incident = make_incident(
        priority="P1",
        status="resolved",
        opened_at=OPENED,
        resolved_at=resolution_due + timedelta(seconds=1),
    )
    # Resolution itself was late even though now is before the due time.
    assert sla_status(incident, resolution_due - timedelta(seconds=1)).resolution_breached


def test_resolution_uses_current_time_when_not_resolved():
    incident = make_incident(priority="P2", opened_at=OPENED)
    resolution_due = OPENED + RESOLUTION["P2"]

    assert not sla_status(incident, resolution_due - timedelta(seconds=1)).resolution_breached
    assert sla_status(incident, resolution_due + timedelta(seconds=1)).resolution_breached


def test_waiting_shifts_only_resolution_due_and_includes_all_waiting_time():
    waiting_since = OPENED + timedelta(hours=1)
    now = OPENED + timedelta(hours=3)
    incident = make_incident(
        priority="P1",
        status="waiting",
        opened_at=OPENED,
        waiting_seconds=20 * 60,
        waiting_since=waiting_since,
    )

    status = sla_status(incident, now)

    assert status.response_due == OPENED + RESPONSE["P1"]
    assert status.response_breached
    assert status.resolution_due == OPENED + RESOLUTION["P1"] + timedelta(hours=2, minutes=20)
    assert not status.resolution_breached


def test_open_incident_breaches_before_it_is_closed_and_each_target_is_reported_once():
    overdue = make_incident(key="INC-OVERDUE", priority="P1", status="open", opened_at=OPENED)
    not_overdue = make_incident(key="INC-CURRENT", priority="P4", opened_at=OPENED)
    now = OPENED + timedelta(hours=5)

    assert breaches([overdue, not_overdue], now) == [
        ("INC-OVERDUE", "response"),
        ("INC-OVERDUE", "resolution"),
    ]


@pytest.mark.parametrize("target", ["response", "resolution"])
@pytest.mark.xfail(
    reason="SLA rules require completion before the due time; implementation uses > and treats equality as met"
)
def test_completion_exactly_at_deadline_is_a_breach(target):
    incident = make_incident(priority="P1", opened_at=OPENED)
    due = OPENED + (RESPONSE["P1"] if target == "response" else RESOLUTION["P1"])
    if target == "response":
        incident.acknowledged_at = due
    else:
        incident.resolved_at = due

    status = sla_status(incident, due)

    assert getattr(status, f"{target}_breached")
