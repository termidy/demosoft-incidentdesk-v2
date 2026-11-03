"""Catch up with the course: put the files of your copy where they are at a tag of the course.

Every section has a tag at its start and end (c1-s3-start, c1-s3-end), and every practice lesson a tag before and after
it (c1-1-4-2-before). The tags live in the course's template repository, not in your copy.

    python3 scripts/catchup.py --list              # the tags you can catch up to
    python3 scripts/catchup.py c1-s3-start         # files as at that tag

It overwrites only files that the tag has; it never deletes a file. Every file of yours that it replaces and that
differs is copied first to .backup/<time>/. Nothing is committed: review with git status, then commit and push.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

TEMPLATE = "https://github.com/termidy/incidentdesk.git"  # the course template (to confirm before publishing)
ROOT = Path(__file__).resolve().parent.parent


def git(*args: str, check: bool = True) -> str:
    run = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    if check and run.returncode != 0:
        sys.exit(f"git {' '.join(args)}: {run.stderr.strip()}")
    return run.stdout


def fetch_tags() -> list[str]:
    git("fetch", "--quiet", "--no-tags", TEMPLATE, "+refs/tags/c1-*:refs/catchup/c1-*")
    refs = git("for-each-ref", "--format=%(refname:strip=2)", "refs/catchup/").split()
    return sorted(refs)


def catch_up(tag: str) -> None:
    ref = f"refs/catchup/{tag}"
    files = git("ls-tree", "-r", "--name-only", ref).splitlines()
    backup = ROOT / ".backup" / datetime.now().strftime("%Y%m%d-%H%M%S")
    replaced = 0
    for name in files:
        mine = ROOT / name
        theirs = git("show", f"{ref}:{name}", check=False)
        if mine.exists() and mine.read_text(errors="replace") != theirs:
            (backup / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(mine, backup / name)
            replaced += 1
    git("checkout", ref, "--", ".")
    print(f"Files as at {tag}: {len(files)}; {replaced} of yours replaced" + (f", saved in {backup}" if replaced else ""))
    print("Review with git status, then commit and push.")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    tags = fetch_tags()
    if sys.argv[1] == "--list":
        print("\n".join(tags) or "No tags yet.")
        return
    if sys.argv[1] not in tags:
        sys.exit(f"No tag {sys.argv[1]}. See: python3 scripts/catchup.py --list")
    catch_up(sys.argv[1])


if __name__ == "__main__":
    main()
