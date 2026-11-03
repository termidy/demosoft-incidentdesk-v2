"""Check that your copy of incidentdesk is ready for the course. It only reads; it changes nothing.

    python3 doctor.py              # everything
    python3 doctor.py --offline    # without the checks that ask GitHub

Exit code 0 when every required check passes. Notes (lines with "note") are not required.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COURSE_ISSUES = {3: "--version", 12: "priority", 18: "Markdown", 24: "zoneinfo", 31: "SLA", 40: "mobile app", 47: "production"}
failed = 0


def ok(text: str) -> None:
    print(f"  ok    {text}")


def bad(text: str, fix: str) -> None:
    global failed
    failed += 1
    print(f"  FAIL  {text}\n        -> {fix}")


def note(text: str) -> None:
    print(f"  note  {text}")


def run(*cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


def check_tools() -> None:
    print("Tools")
    if sys.version_info >= (3, 12):
        ok(f"Python {sys.version.split()[0]}")
    else:
        bad(f"Python {sys.version.split()[0]}", "IncidentDesk needs Python 3.12 or newer for its tests")
    for tool, why in [("git", "https://git-scm.com/downloads"), ("gh", "https://cli.github.com, then: gh auth login")]:
        if shutil.which(tool):
            ok(tool)
        else:
            bad(f"{tool} not found", f"install it: {why}")
    missing = [m for m in ("fastapi", "sqlalchemy", "psycopg", "pytz", "pytest") if not importlib.util.find_spec(m)]
    if missing:
        bad(f"Python packages missing: {', '.join(missing)}", 'pip install -e ".[dev]" (in a virtual environment)')
    else:
        ok("Python packages")
    if shutil.which("docker"):
        ok("docker (for the local database)")
    else:
        note("no docker: tests that need the database are skipped locally; CI runs them")


def check_github(offline: bool) -> None:
    print("GitHub")
    if offline:
        note("skipped (--offline)")
        return
    if run("gh", "auth", "status").returncode != 0:
        bad("the GitHub CLI is not signed in", "gh auth login")
        return
    ok("gh signed in")
    view = run("gh", "repo", "view", "--json", "nameWithOwner,isTemplate,visibility")
    if view.returncode != 0:
        bad("this folder is not a GitHub repository", "clone your copy of the template and run doctor.py inside it")
        return
    repo = json.loads(view.stdout)
    if repo["isTemplate"]:
        bad(f"{repo['nameWithOwner']} is the template itself", "create your own copy: Use this template > Create a new repository")
        return
    ok(f"your copy: {repo['nameWithOwner']} ({repo['visibility'].lower()})")
    if repo["visibility"] != "PUBLIC":
        note("the course uses a public copy: code scanning and secret scanning are free there")
    issues = run("gh", "issue", "list", "--state", "all", "--limit", "60", "--json", "number,title")
    titles = {i["number"]: i["title"] for i in json.loads(issues.stdout or "[]")}
    wrong = [n for n, word in COURSE_ISSUES.items() if word.lower() not in titles.get(n, "").lower()]
    if wrong:
        bad(f"the backlog numbers do not match the lessons (#{', #'.join(map(str, wrong))})",
            "on a new copy: python3 scripts/setup_backlog.py")
    else:
        ok("backlog: #3, #12, #18, #24, #31, #40, #47 in place")


def check_mcp() -> None:
    print("IncidentDesk MCP server")
    if not os.environ.get("INCIDENTDESK_API_KEY"):
        note("INCIDENTDESK_API_KEY is not set here; the agent gets it from the Agents secret COPILOT_MCP_INCIDENTDESK_KEY")
        return
    check = run(sys.executable, "mcp/incidentdesk_mcp.py", "--check")
    if check.returncode == 0:
        ok(check.stdout.strip())
    else:
        bad("the MCP server does not start", check.stderr.strip())


def check_tests() -> None:
    print("Tests")
    if not importlib.util.find_spec("pytest"):
        note("skipped: pytest is not installed")
        return
    result = run(sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-m", "not db")
    last = (result.stdout.strip().splitlines() or ["no output"])[-1]
    if result.returncode == 0:
        ok(f"unit tests: {last}")
    else:
        bad(f"unit tests: {last}", "python3 -m pytest -m 'not db' and read the first failure")
    if not os.environ.get("DATABASE_URL"):
        note("DATABASE_URL is not set: database tests skipped (docker compose up -d db, see CONTRIBUTING.md)")


def main() -> None:
    offline = "--offline" in sys.argv
    print(f"incidentdesk doctor ({ROOT})")
    check_tools()
    check_github(offline)
    check_mcp()
    check_tests()
    print("\nReady." if not failed else f"\n{failed} check(s) failed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
