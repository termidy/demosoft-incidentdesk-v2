from datetime import datetime

import pytz
import pytest

from incidentdesk.oncall.handoff import handoff_note
from incidentdesk.oncall.rotation import shifts
from incidentdesk.oncall.schedule import on_call
from tests.conftest import chicago, make_incident, make_service


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


def test_handoff_note_without_open_incidents_has_exact_message():
    note = handoff_note("amer", chicago(2026, 10, 12, 10, 0), [])
    assert note == "Handoff amer - Mon 12 Oct 10:00 CDT\nNo open incidents."


def test_handoff_note_sorts_incidents_by_priority_then_opened_at():
    incidents = [
        make_incident(key="INC-3", priority="P2", opened_at=chicago(2026, 10, 13, 16, 0)),
        make_incident(key="INC-1", priority="P1", opened_at=chicago(2026, 10, 13, 17, 0)),
        make_incident(key="INC-2", priority="P1", opened_at=chicago(2026, 10, 13, 15, 0)),
    ]

    note = handoff_note("amer", chicago(2026, 10, 12, 10, 0), incidents)

    assert [line.split()[1] for line in note.splitlines()[1:]] == ["INC-2", "INC-1", "INC-3"]


@pytest.mark.parametrize(
    ("at", "opened_at", "expected_header", "expected_opened"),
    [
        (
            pytz.UTC.localize(datetime(2026, 3, 8, 7, 30)),
            pytz.UTC.localize(datetime(2026, 3, 8, 7, 15)),
            "Handoff amer - Sun 08 Mar 01:30 CST",
            "Sun 01:15",
        ),
        (
            pytz.UTC.localize(datetime(2026, 3, 8, 8, 30)),
            pytz.UTC.localize(datetime(2026, 3, 8, 8, 15)),
            "Handoff amer - Sun 08 Mar 03:30 CDT",
            "Sun 03:15",
        ),
    ],
)
def test_handoff_note_uses_chicago_timezone_before_and_after_dst(
    at, opened_at, expected_header, expected_opened
):
    note = handoff_note("amer", at, [make_incident(opened_at=opened_at)])

    assert note.splitlines()[0] == expected_header
    assert f"(open since {expected_opened})" in note


def test_handoff_note_excludes_resolved_incidents_and_other_rotations():
    incidents = [
        make_incident(key="INC-4822", status="resolved"),
        make_incident(key="INC-4823", service=make_service(rotation="emea")),
        make_incident(key="INC-4824"),
    ]

    note = handoff_note("amer", chicago(2026, 10, 12, 10, 0), incidents)

    assert "INC-4824" in note
    assert "INC-4822" not in note
    assert "INC-4823" not in note
