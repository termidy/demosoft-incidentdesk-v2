import argparse
import re
import shlex
from pathlib import Path

import pytest

from incidentdesk.cli import build_parser

ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "docs" / "runbook.md"
SUBCOMMANDS = next(
    action.choices for action in build_parser()._actions if isinstance(action, argparse._SubParsersAction)
)


def reference_errors(text):
    errors = []
    blocks = re.findall(r"```(?:bash|sh)\n(.*?)```", text, re.DOTALL)
    inline = re.findall(r"(?<!`)`([^`\n]+)`(?!`)", re.sub(r"```.*?```", "", text, flags=re.DOTALL))
    for snippet in [*blocks, *inline]:
        for line in snippet.splitlines():
            tokens = shlex.split(line, comments=True)
            for index, token in enumerate(tokens):
                if token == "incidentdesk" and index + 1 < len(tokens):
                    command = tokens[index + 1]
                    if not command.startswith("-") and command not in SUBCOMMANDS:
                        errors.append(f"unknown incidentdesk subcommand: {command}")
                if (
                    not token.startswith(("/", ".venv/", "http://", "https://", "-"))
                    and "=" not in token
                    and ("/" in token or Path(token).suffix in {".py", ".sh", ".yaml", ".yml", ".md", ".json"})
                    and not (ROOT / token).exists()
                ):
                    errors.append(f"missing repository path: {token}")
    return errors


def test_runbook_references_exist():
    text = RUNBOOK.read_text()
    assert "```bash\n" in text
    assert not reference_errors(text)


@pytest.mark.parametrize(
    "text",
    [
        "```bash\nincidentdesk missing-command\n```",
        "```bash\nscripts/missing-script.sh\n```",
        "See `docs/missing-file.md`.",
        "```bash\npython3 missing-file.py\n```",
    ],
)
def test_missing_references_are_rejected(text):
    assert reference_errors(text)
