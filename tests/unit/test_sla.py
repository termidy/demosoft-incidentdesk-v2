from datetime import datetime, timedelta, timezone

import pytest

from incidentdesk.sla import breaches, sla_status
from tests.conftest import make_incident


OPENED = datetime(2026, 10, 13, 14, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("priority", "response_after", "resolution_after"),
    [
        ("P1", timedelta(minutes=15), timedelta(hours=4)),
        ("P2", timedelta(minutes=30), timedelta(hours=8)),
        ("P3", timedelta(hours=4), timedelta(days=3)),
        ("P4", timedelta(days=1), timedelta(days=10)),
    ],
)
def test_due_times_use_documented_priority_durations(priority, response_after, resolution_after):
    incident = make_incident(priority=priority, opened_at=OPENED)

    status = sla_status(incident, OPENED)

    assert status.response_due == OPENED + response_after
    assert status.resolution_due == OPENED + resolution_after


@pytest.mark.parametrize("priority", ["P1", "P2", "P3", "P4"])
def test_acknowledgement_and_resolution_at_due_time_are_met(priority):
    incident = make_incident(priority=priority, opened_at=OPENED)
    due = sla_status(incident, OPENED)
    incident.acknowledged_at = due.response_due
    incident.resolved_at = due.resolution_due

    status = sla_status(incident, due.resolution_due + timedelta(days=1))

    assert not status.response_breached
    assert not status.resolution_breached


def test_acknowledgement_and_resolution_after_due_time_breach():
    incident = make_incident(priority="P1", opened_at=OPENED)
    due = sla_status(incident, OPENED)
    incident.acknowledged_at = due.response_due + timedelta(seconds=1)
    incident.resolved_at = due.resolution_due + timedelta(seconds=1)

    status = sla_status(incident, incident.resolved_at)

    assert status.response_breached
    assert status.resolution_breached


def test_accumulated_customer_wait_extends_resolution_due_time():
    incident = make_incident(
        priority="P1",
        opened_at=OPENED,
        waiting_seconds=2 * 60 * 60,
        resolved_at=OPENED + timedelta(hours=5),
    )

    status = sla_status(incident, OPENED + timedelta(hours=5))

    assert status.resolution_due == OPENED + timedelta(hours=6)
    assert not status.resolution_breached


def test_current_customer_wait_extends_resolution_due_time_by_elapsed_wait():
    waiting_since = OPENED + timedelta(hours=3)
    now = OPENED + timedelta(hours=4)
    incident = make_incident(
        priority="P1",
        status="waiting",
        opened_at=OPENED,
        waiting_since=waiting_since,
        waiting_seconds=10 * 60,
    )

    status = sla_status(incident, now)

    assert status.resolution_due == OPENED + timedelta(hours=5, minutes=10)
    assert not status.resolution_breached


def test_customer_wait_never_pauses_response_target():
    incident = make_incident(
        priority="P1",
        status="waiting",
        opened_at=OPENED,
        waiting_since=OPENED + timedelta(minutes=1),
    )
    now = OPENED + timedelta(minutes=16)

    status = sla_status(incident, now)

    assert status.response_due == OPENED + timedelta(minutes=15)
    assert status.response_breached


def test_open_unresolved_incident_is_in_breach_after_both_due_times():
    incident = make_incident(priority="P1", status="open", opened_at=OPENED)

    status = sla_status(incident, OPENED + timedelta(days=1))

    assert incident.resolved_at is None
    assert status.response_breached
    assert status.resolution_breached


def test_breaches_reports_each_breached_target_once():
    incident = make_incident(key="INC-1", priority="P1", status="open", opened_at=OPENED)

    found = breaches([incident], OPENED + timedelta(days=1))

    assert found == [("INC-1", "response"), ("INC-1", "resolution")]
