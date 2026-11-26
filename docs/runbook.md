# On-call runbook: local demo

Run these commands from the repository root in a shell on the machine running the demo. This is a local demo procedure,
not a production recovery procedure. Use Python 3.12 or newer, Docker with Compose, and a free local port 5432.

**Safety:** The demo seed writes data, and database tests drop and recreate tables. Never point these commands at a
production database or a database containing data you need.

## Prepare the environment

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

Success: the installation finishes without an error and the shell can run `incidentdesk --help`.
If installation fails, run the following and resolve the reported missing prerequisite before retrying:

```bash
python3 doctor.py --offline
```

Gap: The repository does not document a complete recovery procedure for missing system dependencies.

## Start the database

```bash
docker compose up -d db
docker compose ps
export DATABASE_URL="postgresql+psycopg://$(docker compose exec -T db printenv POSTGRES_USER):$(docker compose exec -T db printenv POSTGRES_PASSWORD)@localhost:5432/$(docker compose exec -T db printenv POSTGRES_DB)"
```

The connection string is only for the disposable local database in `compose.yaml`. Success: the `db` service
eventually shows `healthy`. If it does not start or become healthy, inspect the specific service:

```bash
docker compose ps -a
docker compose logs --tail 100 db
```

If port 5432 is already allocated, stop here; do not assume the existing database is disposable.
Gap: The repository does not specify how to resolve a port conflict or restore a production database.

## Load the demo data

With the local database running and `DATABASE_URL` set in this shell:

```bash
incidentdesk seed
```

Success: JSON reports `{"services": 12, "incidents": 250}`. Run it only on an empty demo database: loading twice can
fail on duplicate data. If it fails, run the database status and log commands above; if the schema is missing, ensure
the database is running and retry the seed on an empty demo database.
Gap: The repository does not document a non-destructive recovery for a partially populated or previously seeded database.
Do not use `incidentdesk seed --reset` on data you need: it drops tables.

## Run and check the service

In the configured shell:

```bash
incidentdesk serve
```

Success: Uvicorn reports that it is running at `http://127.0.0.1:8000`. Leave it running and check from another shell:

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/docs
```

Success: the check prints `200`. If startup or the check fails, read the Uvicorn output in the service shell and check
the database with the database commands above. This HTTP check does not verify database connectivity; use the SLA or
report command below for that.
Gap: The repository does not provide a production health check or a complete service recovery procedure.

## Run the tests

Only with `DATABASE_URL` pointing to the disposable local database:

```bash
scripts/test.sh
```

Success: two pytest summaries report no failures, once for UTC and once for Asia/Singapore. Database tests are skipped
if `DATABASE_URL` is unset, so a skipped database suite is not a full database check. If a test fails, use the failing
test name and traceback printed by the command; check the database status and logs with the commands above before
retrying.
Gap: The repository does not provide a general remedy for every test failure.

## List SLA breaches

With the local database running, seeded, and `DATABASE_URL` set:

```bash
incidentdesk sla
```

Success: each breach is printed as an incident key, target, and UTC check time; no output means no open-incident
breaches were found. If the command fails, check database status and logs using the commands above and ensure the
database was seeded.
Gap: The repository does not specify an escalation procedure for a reported breach.

## Print the daily report

With the local database running, seeded, and `DATABASE_URL` set, this prints the current day's report in the default
service time zone, America/Chicago:

```bash
INCIDENTDESK_TIMEZONE=America/Chicago incidentdesk report "$(TZ=America/Chicago date +%F)"
```

Success: JSON contains `day`, `opened`, `by_priority`, and `still_open`; zero counts are possible. If the command fails,
check database status and logs using the commands above and ensure the database was seeded.
Gap: The repository does not identify the production service time zone or provide a production reporting procedure.
