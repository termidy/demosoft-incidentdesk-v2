from datetime import timedelta, timezone

import pytest

from incidentdesk.sla import RESPONSE, RESOLUTION, breaches, sla_status
from tests.conftest import make_incident


@pytest.mark.parametrize(
    ("priority", "response", "resolution"),
    [
        ("P1", timedelta(minutes=15), timedelta(hours=4)),
        ("P2", timedelta(minutes=30), timedelta(hours=8)),
        ("P3", timedelta(hours=4), timedelta(days=3)),
        ("P4", timedelta(days=1), timedelta(days=10)),
    ],
)
def test_due_times_are_measured_from_opened_at(priority, response, resolution):
    incident = make_incident(priority=priority)

    status = sla_status(incident, incident.opened_at)
    opened = incident.opened_at.astimezone(timezone.utc)

    assert status.response_due == opened + response == opened + RESPONSE[priority]
    assert status.resolution_due == opened + resolution == opened + RESOLUTION[priority]


@pytest.mark.parametrize("priority", ["P1", "P2", "P3", "P4"])
def test_acknowledgment_and_resolution_at_due_time_meet_the_targets(priority):
    incident = make_incident(priority=priority)
    opened = incident.opened_at.astimezone(timezone.utc)
    incident.acknowledged_at = opened + RESPONSE[priority]
    incident.resolved_at = opened + RESOLUTION[priority]

    status = sla_status(incident, incident.resolved_at)

    assert not status.response_breached
    assert not status.resolution_breached


@pytest.mark.parametrize("priority", ["P1", "P2", "P3", "P4"])
def test_acknowledgment_and_resolution_after_due_time_breach_the_targets(priority):
    incident = make_incident(priority=priority)
    opened = incident.opened_at.astimezone(timezone.utc)
    incident.acknowledged_at = opened + RESPONSE[priority] + timedelta(seconds=1)
    incident.resolved_at = opened + RESOLUTION[priority] + timedelta(seconds=1)

    status = sla_status(incident, incident.resolved_at)

    assert status.response_breached
    assert status.resolution_breached


def test_waiting_time_extends_resolution_due_but_does_not_pause_response():
    incident = make_incident(
        priority="P2",
        status="waiting",
        waiting_seconds=30 * 60,
        waiting_since=make_incident().opened_at + timedelta(hours=2),
    )
    opened = incident.opened_at.astimezone(timezone.utc)
    now = opened + timedelta(hours=5)

    status = sla_status(incident, now)

    assert status.response_due == opened + timedelta(minutes=30)
    assert status.resolution_due == opened + timedelta(hours=11, minutes=30)
    assert status.response_breached
    assert not status.resolution_breached


def test_open_incident_is_breached_after_due_times_and_reported_once_per_target():
    incident = make_incident(priority="P1")
    now = incident.opened_at + timedelta(hours=4, seconds=1)

    status = sla_status(incident, now)

    assert status.response_breached
    assert status.resolution_breached
    assert breaches([incident], now) == [
        (incident.key, "response"),
        (incident.key, "resolution"),
    ]
