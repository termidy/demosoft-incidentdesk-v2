from datetime import datetime, timedelta

import pytz

from incidentdesk.retention.cleanup import to_archive
from tests.conftest import make_incident

NOW = pytz.utc.localize(datetime(2026, 10, 15, 15, 0))


def test_old_resolved_incidents_are_archived_unless_they_have_a_postmortem():
    old = make_incident(key="INC-1", status="resolved", resolved_at=NOW - timedelta(days=400))
    old.id = 1
    kept = make_incident(key="INC-2", status="resolved", resolved_at=NOW - timedelta(days=400))
    kept.id = 2
    recent = make_incident(key="INC-3", status="resolved", resolved_at=NOW - timedelta(days=10))
    recent.id = 3
    assert to_archive([old, kept, recent], with_postmortem={2}, now=NOW) == [old]
