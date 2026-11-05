from datetime import timedelta, timezone

import pytest

from incidentdesk.sla import RESPONSE, RESOLUTION, breaches, sla_status, waiting_time
from tests.conftest import chicago, make_incident


@pytest.mark.parametrize("priority", ["P1", "P2", "P3", "P4"])
def test_due_times_match_each_priority_target(priority):
    incident = make_incident(priority=priority)
    opened = incident.opened_at.astimezone(timezone.utc)

    status = sla_status(incident, opened)

    assert status.response_due == opened + RESPONSE[priority]
    assert status.resolution_due == opened + RESOLUTION[priority]


@pytest.mark.parametrize(
    ("field", "target"),
    [("acknowledged_at", "response_due"), ("resolved_at", "resolution_due")],
)
def test_completed_targets_use_the_completion_time(field, target):
    incident = make_incident(priority="P1")
    due = getattr(sla_status(incident, incident.opened_at), target)
    setattr(incident, field, due - timedelta(seconds=1))

    assert not getattr(sla_status(incident, due + timedelta(days=1)), f"{target.split('_')[0]}_breached")

    setattr(incident, field, due + timedelta(seconds=1))
    assert getattr(sla_status(incident, due), f"{target.split('_')[0]}_breached")


@pytest.mark.parametrize(
    ("field", "target", "breach_field"),
    [
        ("acknowledged_at", "response_due", "response_breached"),
        ("resolved_at", "resolution_due", "resolution_breached"),
    ],
)
@pytest.mark.xfail(
    reason="SLA documentation says a target is met only before its due time; equality is currently treated as met",
    strict=True,
)
def test_completion_at_due_time_is_late(field, target, breach_field):
    incident = make_incident(priority="P1")
    due = getattr(sla_status(incident, incident.opened_at), target)
    setattr(incident, field, due)

    assert getattr(sla_status(incident, due), breach_field)


def test_open_incidents_breach_when_each_due_time_has_passed():
    incident = make_incident(priority="P1")
    now = incident.opened_at + timedelta(hours=5)

    status = sla_status(incident, now)

    assert status.response_breached
    assert status.resolution_breached


def test_open_incident_only_breaches_response_before_resolution_due():
    incident = make_incident(priority="P1")
    status = sla_status(incident, incident.opened_at + timedelta(minutes=16))

    assert status.response_breached
    assert not status.resolution_breached


def test_waiting_time_includes_completed_and_current_customer_wait():
    incident = make_incident(
        priority="P1",
        status="waiting",
        waiting_seconds=3600,
        waiting_since=chicago(2026, 10, 13, 15, 0),
    )
    now = chicago(2026, 10, 13, 15, 30)

    assert waiting_time(incident, now) == timedelta(minutes=90)
    assert sla_status(incident, now).resolution_due == (
        incident.opened_at.astimezone(timezone.utc)
        + RESOLUTION["P1"]
        + timedelta(minutes=90)
    )


def test_waiting_time_is_not_added_when_incident_is_not_waiting():
    incident = make_incident(
        status="open",
        waiting_seconds=600,
        waiting_since=chicago(2026, 10, 13, 15, 0),
    )

    assert waiting_time(incident, chicago(2026, 10, 13, 15, 30)) == timedelta(minutes=10)


def test_customer_wait_pauses_resolution_but_never_response():
    incident = make_incident(
        priority="P1",
        status="waiting",
        waiting_since=chicago(2026, 10, 13, 14, 10),
    )
    now = chicago(2026, 10, 13, 14, 16)

    status = sla_status(incident, now)

    assert status.response_breached
    assert not status.resolution_breached
    assert status.response_due == incident.opened_at.astimezone(timezone.utc) + RESPONSE["P1"]
    assert status.resolution_due == (
        incident.opened_at.astimezone(timezone.utc)
        + RESOLUTION["P1"]
        + timedelta(minutes=6)
    )


def test_breaches_reports_each_breached_target_once():
    incident = make_incident(priority="P1")

    assert breaches([incident], incident.opened_at + timedelta(hours=5)) == [
        (incident.key, "response"),
        (incident.key, "resolution"),
    ]
