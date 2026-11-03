"""The incidentdesk command."""

import argparse
import json
from datetime import date

import pytz


def cmd_serve(args) -> None:
    import uvicorn

    uvicorn.run("incidentdesk.app:app", host=args.host, port=args.port)


def cmd_seed(args) -> None:
    from incidentdesk.seed import seed

    print(json.dumps(seed(reset=args.reset)))


def cmd_sla(args) -> None:
    from sqlalchemy import select

    from incidentdesk.db import session
    from incidentdesk.models import Incident
    from incidentdesk.sla import breaches
    from incidentdesk.timeutil import now

    with session() as s:
        open_ones = list(s.scalars(select(Incident).where(Incident.status != "resolved")))
        at = now()
        for key, target in breaches(open_ones, at):
            print(f"{key} {target} breached (checked {at.astimezone(pytz.utc):%Y-%m-%d %H:%M} UTC)")


def cmd_report(args) -> None:
    from sqlalchemy import select

    from incidentdesk.db import session
    from incidentdesk.models import Incident
    from incidentdesk.reports.daily import daily_report

    with session() as s:
        print(json.dumps(daily_report(list(s.scalars(select(Incident))), date.fromisoformat(args.day)), indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="incidentdesk", description="DemoSoft's incident management service")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run the HTTP API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.set_defaults(func=cmd_serve)

    seed = sub.add_parser("seed", help="load the demo data into the database")
    seed.add_argument("--reset", action="store_true", help="drop every table first")
    seed.set_defaults(func=cmd_seed)

    sla = sub.add_parser("sla", help="print SLA breaches of open incidents")
    sla.set_defaults(func=cmd_sla)

    report = sub.add_parser("report", help="print the daily report of one day (service time zone)")
    report.add_argument("day", help="YYYY-MM-DD")
    report.set_defaults(func=cmd_report)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
