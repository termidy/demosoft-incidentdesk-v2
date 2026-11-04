from incidentdesk.models import Postmortem
from incidentdesk.postmortems import missing_sections


def make_postmortem(**sections) -> Postmortem:
    fields = {
        "key": "PM-117",
        "incident_id": 1,
        "title": "Login outage",
        "summary": "",
        "impact": "",
        "root_cause": None,
        "actions": [],
        "author": "On-call engineer",
    }
    fields.update(sections)
    return Postmortem(**fields)


def test_missing_sections_returns_nothing_when_all_sections_are_filled():
    postmortem = make_postmortem(
        summary="Login errors",
        impact="Some users could not log in",
        root_cause="A failed deployment",
        actions=["Add a canary"],
    )

    assert missing_sections(postmortem) == []


def test_missing_sections_identifies_draft_without_root_cause():
    postmortem = make_postmortem(
        summary="Login errors",
        impact="Some users could not log in",
        actions=["Add a canary"],
    )

    assert missing_sections(postmortem) == ["root_cause"]


def test_missing_sections_returns_all_sections_in_required_order_for_empty_postmortem():
    assert missing_sections(make_postmortem()) == [
        "summary",
        "impact",
        "root_cause",
        "actions",
    ]
