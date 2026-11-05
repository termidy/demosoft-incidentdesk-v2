from datetime import datetime
from zoneinfo import ZoneInfo

from incidentdesk.oncall.handoff import handoff_note
from incidentdesk.oncall.rotation import shifts
from incidentdesk.oncall.schedule import on_call
from tests.conftest import chicago, make_incident, make_service


def test_handoff_happens_monday_at_ten_local():
    before = chicago(2026, 10, 12, 9, 59)
    after = chicago(2026, 10, 12, 10, 0)
    assert on_call("amer", before) != on_call("amer", after)


def test_each_rotation_uses_its_own_time_zone():
    lisbon = ZoneInfo("Europe/Lisbon")
    at = datetime(2026, 10, 12, 10, 30, tzinfo=lisbon)
    assert on_call("emea", at) != on_call("emea", datetime(2026, 10, 12, 9, 30, tzinfo=lisbon))


def test_shift_table_keeps_ten_oclock_across_daylight_saving():
    table = shifts("amer", chicago(2026, 10, 27, 12, 0), weeks=2)
    tz = ZoneInfo("America/Chicago")
    assert [s.starts_at.astimezone(tz).hour for s in table] == [10, 10]
    assert table[0].ends_at == table[1].starts_at


def test_handoff_note_says_when_there_are_no_open_incidents():
    note = handoff_note("amer", chicago(2026, 10, 12, 10, 0), [])
    assert note == "Handoff amer - Mon 12 Oct 10:00 CDT\nNo open incidents."


def test_handoff_note_sorts_and_filters_incidents():
    incidents = [
        make_incident(key="INC-4824", priority="P2", opened_at=chicago(2026, 10, 13, 13, 0)),
        make_incident(key="INC-4823", priority="P1", opened_at=chicago(2026, 10, 13, 12, 0)),
        make_incident(key="INC-4822", priority="P1", opened_at=chicago(2026, 10, 13, 11, 0)),
        make_incident(key="INC-4825", status="resolved"),
        make_incident(key="INC-4826", service=make_service(rotation="emea")),
    ]

    note = handoff_note("amer", chicago(2026, 10, 13, 9, 0), incidents)

    assert note == "\n".join(
        [
            "Handoff amer - Tue 13 Oct 09:00 CDT",
            "- INC-4822 P1 Login fails for some customers (open since Tue 11:00)",
            "- INC-4823 P1 Login fails for some customers (open since Tue 12:00)",
            "- INC-4824 P2 Login fails for some customers (open since Tue 13:00)",
        ]
    )


def test_handoff_note_uses_chicago_time_before_and_after_daylight_saving():
    for at, expected in [
        (chicago(2026, 10, 31, 9, 0), "Handoff amer - Sat 31 Oct 09:00 CDT"),
        (chicago(2026, 11, 2, 9, 0), "Handoff amer - Mon 02 Nov 09:00 CST"),
    ]:
        incident = make_incident(opened_at=chicago(at.year, at.month, at.day, 14, 5))

        note = handoff_note("amer", at, [incident])

        assert note == "\n".join(
            [
                f"{expected}",
                f"- INC-4821 P2 Login fails for some customers (open since {at:%a 14:05})",
            ]
        )
