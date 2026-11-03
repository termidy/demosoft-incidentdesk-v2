"""Generate the demo data in data/demo/ (seeded: the same files on every run).

The files are what DemoSoft's production IncidentDesk exported on 2026-10-15: twelve services, sixty days of incidents
and the postmortems written for them. The data is as messy as the real export:
- priorities are the ones production stored, so incidents opened outside business hours carry the bug of issue #12;
- monitoring fires the same alert several times within minutes;
- titles typed by people have stray spaces and lower case;
- some postmortems are drafts with sections missing.
Every planted problem is listed in data/demo/truth.json.

Run it only to rebuild the files from scratch: recorded lessons depend on them. A new need gets a new generator.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

OUT = Path(__file__).resolve().parent.parent / "data" / "demo"
NOW = datetime(2026, 10, 15, 15, 0, tzinfo=ZoneInfo("UTC"))
SERVICE_TZ = ZoneInfo("America/Chicago")
rng = random.Random(600)

SERVICES = [
    ("login-service", "Login Service", "identity", "amer", True),
    ("checkout-api", "Checkout API", "payments", "amer", True),
    ("billing-service", "Billing Service", "payments", "amer", True),
    ("mobile-gateway", "Mobile Gateway", "mobile", "amer", True),
    ("search-api", "Search API", "discovery", "emea", True),
    ("file-storage", "File Storage", "platform", "emea", True),
    ("status-page", "Status Page", "sre", "amer", True),
    ("notification-service", "Notification Service", "platform", "emea", False),
    ("reporting-service", "Reporting Service", "data", "apac", False),
    ("incident-webhooks", "Incident Webhooks", "sre", "amer", False),
    ("audit-log", "Audit Log", "security", "apac", False),
    ("admin-console", "Admin Console", "identity", "emea", False),
]

TITLES = {
    "critical": ["{name} is down", "{name} returns 503 for all requests", "{name}: database connections exhausted"],
    "major": ["{name}: error rate above 5%", "{name}: p95 latency above 2s", "{name} fails for some customers"],
    "minor": ["{name}: slow responses in one region", "{name}: retries increasing", "{name}: disk usage at 85%"],
    "cosmetic": ["{name}: typo on error page", "{name}: wrong icon in admin view", "{name}: log noise from health checks"],
}
SEVERITIES = ["critical"] * 1 + ["major"] * 3 + ["minor"] * 5 + ["cosmetic"] * 2
START = {"critical": 1, "major": 2, "minor": 3, "cosmetic": 4}
RESPONSE = {"P1": 15, "P2": 30, "P3": 240, "P4": 1440}
RESOLUTION = {"P1": 240, "P2": 480, "P3": 4320, "P4": 14400}
AUTHORS = ["Tomás Silva", "Mei Tanaka", "Daniel Kowalski", "Grace Okafor"]


def business_hours(at: datetime) -> bool:
    local = at.astimezone(SERVICE_TZ)
    return local.weekday() < 5 and 9 <= local.hour < 18


def stored_priority(severity: str, customer_facing: bool, at: datetime) -> str:
    """The rule production ran when these incidents were opened (with the bug of issue #12)."""
    level = START[severity] - (1 if customer_facing and business_hours(at) else 0)
    return f"P{max(level, 1)}"


def rule_priority(severity: str, customer_facing: bool) -> str:
    """The rule of docs/priority-rules.md."""
    return f"P{max(START[severity] - (1 if customer_facing else 0), 1)}"


def iso(at: datetime | None) -> str | None:
    return at.astimezone(ZoneInfo("UTC")).isoformat().replace("+00:00", "Z") if at else None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    services = [{"slug": s, "name": n, "team": t, "rotation": r, "customer_facing": cf} for s, n, t, r, cf in SERVICES]
    incidents, truth = [], {"after_hours_priority": [], "duplicates": [], "messy_titles": [], "draft_postmortems": []}

    number = 4700
    for day in range(60, 0, -1):
        for _ in range(rng.choice([2, 3, 3, 4, 5])):
            service = rng.choice(SERVICES)
            slug, name, _, _, customer_facing = service
            severity = rng.choice(SEVERITIES)
            opened = NOW - timedelta(days=day, minutes=rng.randint(0, 24 * 60 - 1))
            number += 1
            priority = stored_priority(severity, customer_facing, opened)
            title = rng.choice(TITLES[severity]).format(name=name)
            source = rng.choice(["monitoring", "monitoring", "monitoring", "email", "manual"])
            if source != "monitoring" and rng.random() < 0.35:
                title = "  " + title.lower() + " "
                truth["messy_titles"].append(f"INC-{number}")
            ack = opened + timedelta(minutes=rng.randint(2, int(RESPONSE[priority] * 1.3)))
            waiting = rng.choice([0, 0, 0, rng.randint(10, 300) * 60])
            resolved = ack + timedelta(minutes=rng.randint(10, int(RESOLUTION[priority] * 1.2))) + timedelta(seconds=waiting)
            if resolved > NOW:
                resolved = None
            incident = {
                "key": f"INC-{number}", "title": title, "service": slug, "severity": severity, "priority": priority,
                "status": "resolved" if resolved else "acknowledged", "source": source,
                "opened_at": iso(opened), "acknowledged_at": iso(ack), "resolved_at": iso(resolved),
                "waiting_seconds": waiting,
                "timeline": [{"at": iso(opened), "kind": "opened", "note": ""}, {"at": iso(ack), "kind": "acknowledged", "note": ""}]
                + ([{"at": iso(resolved), "kind": "resolved", "note": "Mitigated"}] if resolved else []),
            }
            incidents.append(incident)
            if priority != rule_priority(severity, customer_facing):
                truth["after_hours_priority"].append({"key": incident["key"], "stored": priority,
                                                "by_rules": rule_priority(severity, customer_facing),
                                                "opened_local": opened.astimezone(SERVICE_TZ).strftime("%a %H:%M")})
            if source == "monitoring" and rng.random() < 0.15:
                for repeat in range(rng.randint(1, 3)):
                    number += 1
                    dup_opened = opened + timedelta(minutes=2 * (repeat + 1))
                    dup_closed = dup_opened + timedelta(seconds=30)
                    dup = dict(incident, key=f"INC-{number}", opened_at=iso(dup_opened), status="resolved",
                               acknowledged_at=None, resolved_at=iso(dup_closed), waiting_seconds=0,
                               timeline=[{"at": iso(dup_opened), "kind": "opened", "note": ""},
                                         {"at": iso(dup_closed), "kind": "resolved", "note": f"Duplicate of {incident['key']}"}])
                    incidents.append(dup)
                    truth["duplicates"].append({"key": dup["key"], "duplicate_of": incident["key"]})

    postmortems = []
    worth_one = [i for i in incidents if i["severity"] == "critical" and i["status"] == "resolved" and i["acknowledged_at"]]
    for n, incident in enumerate(worth_one[:30], start=101):
        draft = n % 9 == 0
        pm = {
            "key": f"PM-{n}", "incident": incident["key"], "title": incident["title"].strip().capitalize(),
            "summary": f"{incident['title'].strip()} for {rng.randint(8, 95)} minutes.",
            "impact": f"About {rng.randint(2, 40)}% of requests to {incident['service']} failed.",
            "root_cause": None if draft else rng.choice([
                "A configuration change lowered the connection pool size.",
                "A dependency released a breaking change that our version range allowed.",
                "Certificate rotation missed one load balancer.",
                "A slow query locked the incidents table during a report run.",
            ]),
            "actions": [] if draft else rng.sample([
                "Add an alert on connection pool saturation", "Pin the dependency and review upgrades weekly",
                "Automate certificate rotation checks", "Move reports to the read replica",
                "Add a runbook link to the alert", "Load test the new configuration before rollout",
            ], 2),
            "author": rng.choice(AUTHORS),
            "published_at": None if draft else incident["resolved_at"],
        }
        postmortems.append(pm)
        if draft:
            truth["draft_postmortems"].append(pm["key"])

    for name, data in [("services", services), ("incidents", incidents), ("postmortems", postmortems), ("truth", truth)]:
        (OUT / f"{name}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(services)} services, {len(incidents)} incidents, {len(postmortems)} postmortems -> {OUT}")


if __name__ == "__main__":
    main()
