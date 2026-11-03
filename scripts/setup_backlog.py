"""Create DemoSoft's backlog in your copy of incidentdesk, so issue numbers match the lessons.

A repository made from a template starts with no issues. This script creates issues #1 to #47 in order: the ones the
lessons use (#3, #12, #18, #24, #31, #40 with its sub-issues #41-#43, #44, #47) stay open, the others are the team's older
work and are closed at once. Run it once, on a new copy, before you open any issue or pull request yourself: issues and
pull requests share one sequence of numbers.

    python3 scripts/setup_backlog.py --dry-run     # what it would create
    python3 scripts/setup_backlog.py               # create it (needs the GitHub CLI, signed in: gh auth login)

It never deletes or edits anything that is already in the repository.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

BACKLOG = json.loads((Path(__file__).resolve().parent / "backlog.json").read_text())


def gh(*args: str, input: dict | None = None) -> str:
    run = subprocess.run(["gh", *args], input=json.dumps(input) if input else None, capture_output=True, text=True)
    if run.returncode != 0:
        sys.exit(f"gh {' '.join(args[:3])} failed: {run.stderr.strip()}")
    return run.stdout


def current_repo() -> str:
    return gh("repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner").strip()


def highest_number(repo: str) -> int:
    """The highest issue or pull request number so far (0 for a new repository)."""
    latest = json.loads(gh("api", f"repos/{repo}/issues?state=all&per_page=1&sort=created&direction=desc"))
    return latest[0]["number"] if latest else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", help="owner/name (default: the repository of this folder)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    issues = BACKLOG["issues"]
    if args.dry_run:
        for issue in issues:
            state = "closed" if issue.get("close") else "open"
            parent = f", sub-issue of #{issue['parent']}" if issue.get("parent") else ""
            print(f"#{issue['n']:<3} {state:<6} {issue['title']}{parent}")
        return

    repo = args.repo or current_repo()
    if highest_number(repo):
        sys.exit(f"{repo} already has issues or pull requests (up to #{highest_number(repo)}): the numbers would not match "
                 "the lessons. Run this on a new copy of the template.")

    for label in BACKLOG["labels"]:
        gh("label", "create", label["name"], "--repo", repo, "--color", label["color"],
           "--description", label["description"], "--force")

    ids = {}
    for issue in issues:
        created = json.loads(gh("api", f"repos/{repo}/issues", "--method", "POST", "--input", "-",
                                input={"title": issue["title"], "body": issue.get("body", ""), "labels": issue["labels"]}))
        if created["number"] != issue["n"]:
            sys.exit(f"Expected #{issue['n']}, GitHub created #{created['number']}. Something else created an issue "
                     "meanwhile; start again on a new copy.")
        ids[issue["n"]] = created["id"]
        if issue.get("close"):
            gh("api", f"repos/{repo}/issues/{issue['n']}", "--method", "PATCH", "--input", "-",
               input={"state": "closed", "state_reason": issue.get("reason", "completed")})
        if issue.get("parent"):
            gh("api", f"repos/{repo}/issues/{issue['parent']}/sub_issues", "--method", "POST", "--input", "-",
               input={"sub_issue_id": ids[issue["n"]]})
        print(f"#{issue['n']} {issue['title']}")
        time.sleep(1)  # GitHub limits how fast one account creates content

    open_ones = ", ".join(f"#{i['n']}" for i in issues if not i.get("close"))
    print(f"\nDone: {len(issues)} issues in {repo}. Open for the course: {open_ones}.")


if __name__ == "__main__":
    main()
