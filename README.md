# IncidentDesk

DemoSoft's incident management service: it sets each incident's priority, tracks its SLA and stores the postmortem
written after it. Python, FastAPI, PostgreSQL, pytest.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
docker compose up -d db
export DATABASE_URL=postgresql+psycopg://incidentdesk:incidentdesk@localhost:5432/incidentdesk
incidentdesk seed && incidentdesk serve     # http://127.0.0.1:8000/docs
pytest
```

The rules the code follows are in `docs/`; how we work is in `CONTRIBUTING.md`.

## For learners

This repository is the template of the course. You work in your own copy:

1. **Use this template > Create a new repository**, owner: your account, visibility: **Public**.
2. Clone your copy and create the backlog, so issue numbers match the lessons (run it once, before you open any issue or
   pull request yourself):
   ```bash
   gh auth login
   python3 scripts/setup_backlog.py
   ```
3. Check that everything is ready: `python3 doctor.py`.

Behind? `python3 scripts/catchup.py --list` shows the tags of every section and practice lesson, and
`python3 scripts/catchup.py c1-s3-start` puts your files where they are at that point. No access to Copilot cloud agent?
`artifacts/` has the session logs, plans and pull requests of the recorded runs.

`data/demo/` is a seeded export of DemoSoft's incidents (`scripts/make_demo_data.py`); `mcp/incidentdesk_mcp.py` is the
read-only IncidentDesk MCP server the agents use.
