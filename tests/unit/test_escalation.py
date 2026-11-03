from datetime import timedelta

import pytz

from incidentdesk.escalation.timers import due_steps, next_escalation
from tests.conftest import chicago, make_incident


def test_p1_escalates_to_team_lead_after_ten_minutes():
    incident = make_incident(priority="P1")
    at = incident.opened_at.astimezone(pytz.utc) + timedelta(minutes=11)
    assert [s.target for s in due_steps(incident, at)] == ["oncall", "team-lead"]


def test_acknowledged_incident_does_not_escalate():
    opened = chicago(2026, 10, 13, 14, 0)
    incident = make_incident(priority="P1", opened_at=opened, acknowledged_at=opened + timedelta(minutes=3))
    assert due_steps(incident, opened + timedelta(hours=1)) == []
    assert next_escalation(incident, opened + timedelta(hours=1)) is None


def test_next_escalation_time():
    incident = make_incident(priority="P2")
    assert next_escalation(incident, incident.opened_at + timedelta(minutes=5)) == incident.opened_at + timedelta(minutes=30)
