from incidentdesk.exporters.csv_export import incidents_csv
from tests.conftest import make_incident


def test_csv_has_a_header_and_local_times():
    lines = incidents_csv([make_incident()]).splitlines()
    assert lines[0] == "key,service,severity,priority,status,opened,resolved"
    assert lines[1] == "INC-4821,login-service,major,P2,open,2026-10-13 14:00,"
