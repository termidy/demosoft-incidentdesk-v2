from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.sla import breaches, sla_status
from tests.conftest import make_incident


OPENED = datetime(2026, 10, 13, 14, 0, tzinfo=timezone.utc)
TARGETS = [
    ("P1", timedelta(minutes=15), timedelta(hours=4)),
    ("P2", timedelta(minutes=30), timedelta(hours=8)),
    ("P3", timedelta(hours=4), timedelta(days=3)),
    ("P4", timedelta(days=1), timedelta(days=10)),
]


@pytest.mark.parametrize(("priority", "response", "resolution"), TARGETS)
def test_due_times_match_priority_targets(priority, response, resolution):
    incident = make_incident(priority=priority, opened_at=OPENED)

    status = sla_status(incident, OPENED)

    assert status.response_due == OPENED + response
    assert status.resolution_due == OPENED + resolution


@pytest.mark.parametrize(("priority", "response", "resolution"), TARGETS)
def test_acknowledgement_and_resolution_at_due_time_meet_targets(priority, response, resolution):
    incident = make_incident(
        priority=priority,
        opened_at=OPENED,
        acknowledged_at=OPENED + response,
        resolved_at=OPENED + resolution,
    )

    status = sla_status(incident, OPENED + resolution + timedelta(days=1))

    assert not status.response_breached
    assert not status.resolution_breached


def test_acknowledgement_and_resolution_after_due_time_breach_targets():
    incident = make_incident(
        priority="P1",
        opened_at=OPENED,
        acknowledged_at=OPENED + timedelta(minutes=15, seconds=1),
        resolved_at=OPENED + timedelta(hours=4, seconds=1),
    )

    status = sla_status(incident, OPENED + timedelta(days=1))

    assert status.response_breached
    assert status.resolution_breached


def test_customer_wait_pauses_resolution_but_not_response():
    incident = make_incident(
        priority="P1",
        opened_at=OPENED,
        status="waiting",
        waiting_seconds=30 * 60,
        waiting_since=OPENED + timedelta(hours=4),
    )
    now = OPENED + timedelta(hours=5)

    status = sla_status(incident, now)

    assert status.response_due == OPENED + timedelta(minutes=15)
    assert status.resolution_due == OPENED + timedelta(hours=5, minutes=30)
    assert status.response_breached
    assert not status.resolution_breached


def test_waiting_since_only_extends_resolution_while_waiting():
    incident = make_incident(
        priority="P1",
        opened_at=OPENED,
        status="open",
        waiting_since=OPENED + timedelta(hours=4),
    )

    status = sla_status(incident, OPENED + timedelta(hours=5))

    assert status.resolution_due == OPENED + timedelta(hours=4)
    assert status.resolution_breached


def test_open_incident_breaches_after_due_time_and_reports_each_target_once():
    incident = make_incident(priority="P1", opened_at=OPENED)

    assert breaches([incident], OPENED + timedelta(hours=5)) == [
        ("INC-4821", "response"),
        ("INC-4821", "resolution"),
    ]
