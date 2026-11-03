from datetime import datetime

import pytest
import pytz

from incidentdesk.audit.trail import entry
from tests.conftest import chicago


def test_audit_line_is_in_utc():
    line = entry("t.silva", "acknowledge", "INC-4821", chicago(2026, 10, 13, 14, 0)).line()
    assert line == "2026-10-13T19:00:00Z t.silva acknowledge INC-4821"


def test_naive_time_is_refused():
    with pytest.raises(ValueError):
        entry("t.silva", "resolve", "INC-4821", datetime(2026, 10, 13, 14, 0))


def test_utc_input_stays_utc():
    at = pytz.utc.localize(datetime(2026, 10, 13, 19, 0))
    assert entry("ci", "seed", "demo", at).at == at
