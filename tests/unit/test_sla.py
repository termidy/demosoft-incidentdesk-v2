from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.sla import breaches, sla_status
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
def test_sla_targets_are_measured_from_opened_at(priority, response, resolution):
    incident = make_incident(priority=priority, opened_at=OPENED)

    status = sla_status(incident, OPENED)

    assert status.response_due == OPENED + response
    assert status.resolution_due == OPENED + resolution


def test_acknowledged_and_resolved_before_due_meet_both_targets():
    incident = make_incident(
        priority="P2",
        opened_at=OPENED,
        acknowledged_at=OPENED + timedelta(minutes=29),
        resolved_at=OPENED + timedelta(hours=7),
    )

    status = sla_status(incident, OPENED + timedelta(hours=9))

    assert not status.response_breached
    assert not status.resolution_breached


def test_late_acknowledgement_and_resolution_breach_their_targets():
    incident = make_incident(
        priority="P1",
        opened_at=OPENED,
        acknowledged_at=OPENED + timedelta(minutes=16),
        resolved_at=OPENED + timedelta(hours=5),
    )

    status = sla_status(incident, OPENED + timedelta(hours=6))

    assert status.response_breached
    assert status.resolution_breached


def test_events_exactly_at_due_time_meet_targets():
    incident = make_incident(
        priority="P2",
        opened_at=OPENED,
        acknowledged_at=OPENED + timedelta(minutes=30),
        resolved_at=OPENED + timedelta(hours=8),
    )

    status = sla_status(incident, OPENED + timedelta(days=1))

    assert not status.response_breached
    assert not status.resolution_breached


def test_customer_wait_shifts_resolution_due_but_not_response_due():
    waiting_since = OPENED + timedelta(minutes=5)
    now = OPENED + timedelta(minutes=40)
    incident = make_incident(
        priority="P2",
        status="waiting",
        opened_at=OPENED,
        waiting_seconds=timedelta(minutes=20).total_seconds(),
        waiting_since=waiting_since,
    )

    status = sla_status(incident, now)

    assert status.response_due == OPENED + timedelta(minutes=30)
    assert status.resolution_due == OPENED + timedelta(hours=8, minutes=55)
    assert status.response_breached
    assert not status.resolution_breached


def test_accumulated_customer_wait_shifts_resolution_due():
    incident = make_incident(
        priority="P3",
        opened_at=OPENED,
        waiting_seconds=timedelta(hours=2).total_seconds(),
    )

    status = sla_status(incident, OPENED + timedelta(hours=4))

    assert status.resolution_due == OPENED + timedelta(days=3, hours=2)
    assert not status.resolution_breached


def test_open_incident_past_due_is_reported_once_for_each_target():
    incident = make_incident(priority="P1", opened_at=OPENED)

    assert breaches([incident], OPENED + timedelta(hours=5)) == [
        (incident.key, "response"),
        (incident.key, "resolution"),
    ]
