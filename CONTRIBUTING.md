# Contributing to IncidentDesk

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

Tests that need the database are marked `db`. They run when `DATABASE_URL` points to a PostgreSQL database and are
skipped otherwise:

```bash
docker compose up -d db
export DATABASE_URL=postgresql+psycopg://incidentdesk:incidentdesk@localhost:5432/incidentdesk
pytest
```

## Conventions

- Tests mirror the package. A test for `incidentdesk/<module>.py` lives in `tests/unit/test_<module>.py`; a test for
  a module in a subpackage lives in `tests/unit/test_<subpackage>.py`; a test for an HTTP endpoint lives in
  `tests/api/test_<router>.py` and is marked `db`.
- Every bug fix comes with a test that fails before the fix.
- Times are stored in UTC and converted to the service time zone (`INCIDENTDESK_TIMEZONE`) only for business rules and
  display. Use the helpers in `incidentdesk/timeutil.py`; never call `datetime.now()` directly.
- Business rules are written down in `docs/` first. Code follows the document; when they disagree, the document wins
  and the code is a bug.
- One pull request per issue. The description links the issue (`Fixes #12`).
