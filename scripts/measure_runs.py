"""Measure the test-writer's runs on one issue: before and after a tuning.

    python scripts/measure_runs.py before=82,83,85 after=84,86,87

Each pull request's test file runs alone, on its own branch, with branch coverage of the module.
"""
import ast
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from statistics import mean

MODULE = "incidentdesk.sla"
TEST_FILE = "tests/unit/test_sla.py"


def sh(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True).stdout


def tests_without_a_check(source):
    count = 0
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            checks = [n for n in ast.walk(node)
                      if isinstance(n, ast.Assert) or (isinstance(n, ast.Attribute) and n.attr == "raises")]
            count += not checks
    return count


def session_minutes(pr, sessions):
    mine = [s for s in sessions if s["pullRequestNumber"] == pr and s["completedAt"]]
    start, end = (datetime.fromisoformat(mine[-1][k][:19]) for k in ("createdAt", "completedAt"))
    return (end - start).seconds / 60


def measure(pr, sessions):
    with tempfile.TemporaryDirectory() as tmp:
        work = f"{tmp}/run"
        sh("git", "fetch", "-q", "origin", f"pull/{pr}/head")
        sh("git", "worktree", "add", "-q", "--detach", work, "FETCH_HEAD")
        out = sh(sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", TEST_FILE, f"--cov={MODULE}",
                 "--cov-branch", f"--cov-report=json:{tmp}/cov.json", cwd=work)
        totals = json.load(open(f"{tmp}/cov.json"))["totals"]
        source = open(f"{work}/{TEST_FILE}").read()
        sh("git", "worktree", "remove", "--force", work)
    counts = dict((word, int(n)) for n, word in re.findall(r"(\d+) (passed|failed|xfailed|xpassed)", out))
    reviews = json.loads(sh("gh", "pr", "view", str(pr), "--json", "reviews"))["reviews"]
    return {
        "tests": sum(counts.values()),
        "no check": tests_without_a_check(source),
        "xfail": counts.get("xfailed", 0),
        "lines %": 100 * totals["covered_lines"] / totals["num_statements"],
        "branches %": 100 * totals["covered_branches"] / totals["num_branches"],
        "minutes": session_minutes(pr, sessions),
        "sent back": sum(r["state"] == "CHANGES_REQUESTED" for r in reviews),
    }


def cell(column, value):
    return f"{value:.1f}" if column == "minutes" else f"{value:.0f}"


def main():
    repo = json.loads(sh("gh", "repo", "view", "--json", "nameWithOwner"))["nameWithOwner"]
    sessions = [s for s in json.loads(sh("gh", "agent-task", "list", "-L", "100", "--json",
                                         "repository,pullRequestNumber,createdAt,completedAt"))
                if s["repository"] == repo]
    columns = ["tests", "no check", "xfail", "lines %", "branches %", "minutes", "sent back"]
    print(f"{'run':<8}{'PR':>6}" + "".join(f"{c:>12}" for c in columns))
    for group in sys.argv[1:]:
        name, prs = group.split("=")
        rows = [measure(int(pr), sessions) for pr in prs.split(",")]
        for pr, row in zip(prs.split(","), rows):
            print(f"{name:<8}{'#' + pr:>6}" + "".join(f"{cell(c, row[c]):>12}" for c in columns))
        print(f"{'':<8}{'mean':>6}" + "".join(f"{mean(r[c] for r in rows):>12.1f}" for c in columns))
        print(f"{'':<8}{'range':>6}" + "".join(
            f"{cell(c, min(r[c] for r in rows)) + '-' + cell(c, max(r[c] for r in rows)):>12}" for c in columns))
        print()


main()
