from datetime import datetime

import pytz

from incidentdesk.oncall.handoff import handoff_note
from incidentdesk.oncall.rotation import shifts
from incidentdesk.oncall.schedule import on_call
from tests.conftest import chicago, make_incident


def test_handoff_happens_monday_at_ten_local():
    before = chicago(2026, 10, 12, 9, 59)
    after = chicago(2026, 10, 12, 10, 0)
    assert on_call("amer", before) != on_call("amer", after)


def test_each_rotation_uses_its_own_time_zone():
    lisbon = pytz.timezone("Europe/Lisbon")
    at = lisbon.localize(datetime(2026, 10, 12, 10, 30))
    assert on_call("emea", at) != on_call("emea", lisbon.localize(datetime(2026, 10, 12, 9, 30)))


def test_shift_table_keeps_ten_oclock_across_daylight_saving():
    table = shifts("amer", chicago(2026, 10, 27, 12, 0), weeks=2)
    tz = pytz.timezone("America/Chicago")
    assert [s.starts_at.astimezone(tz).hour for s in table] == [10, 10]
    assert table[0].ends_at == table[1].starts_at


def test_handoff_note_lists_open_incidents_of_the_rotation():
    note = handoff_note("amer", chicago(2026, 10, 12, 10, 0), [make_incident(), make_incident(key="INC-4822", status="resolved")])
    assert "INC-4821" in note and "INC-4822" not in note
