# Autonomy matrix

What an agent may do in this repository, and how much of a person each action needs.

Rule: give each action the fastest autonomy level that still keeps it inside our security and Responsible AI standards.
Start at the fastest level; add human control only when a risk or a standard demands it. The highest of the three
risks decides the row. Rate an action by what it does, not by where its files sit.

Risk axes: operational (can it break the service or stop the team's work?), security (can it open access or expose a
secret?), compliance (does it touch a law, a customer contract or our own policy, and can we show who changed what?).

Levels (GitHub's training terms): read-only autonomy, propose-only autonomy, execute with guardrails, human-authorized
execution.

| # | Action | Example | Operational | Security | Compliance | Level | Held by |
|---|---|---|---|---|---|---|---|
| 1 | Read the code; write a plan or a review report | planner, security-reviewer | low | low | low | Read-only autonomy | the agents' `tools` lists; the plan check |
| 2 | Explain a failed CI run on the pull request | `.github/workflows/explain-failed-tests.yml` | low | low | low | Execute with guardrails | one allowed tool; job permissions; time limits |
| 3 | Add or change tests and documentation, and nothing else | every changed file under `tests/` or `docs/`; a plan file and this file are decisions, not documentation | low | low | low | Execute with guardrails: the light path (no plan first; merge after the required checks and one approval) | required checks; the ruleset's one approval, whose reviewer checks that every changed file qualifies (any other file sends the pull request to its own row) |
| 4 | Change application code | a bug fix, a new endpoint | medium | low | low | Propose-only autonomy | an approved plan; required checks; code owner review |
| 5 | Add a new package | a new line in `pyproject.toml` | medium | high | medium | Propose-only autonomy, with a security review | code owner review of the package file; required checks |
| 6 | Change workflows, agent profiles, hooks or CODEOWNERS | `.github/**` | high | high | medium | Propose-only autonomy, the code owner must approve | CODEOWNERS and the ruleset; the Copilot hook denies agent edits to `.github/hooks/` |
| 7 | Run a destructive command | delete data, force push, hard reset | high | medium | low | Human-authorized execution: a person runs it | the Copilot hook; the ruleset blocks force pushes |
| 8 | Change the production configuration or its secrets, and deploy | #47 | critical | critical | critical | Human-authorized execution: Mei approves the change and the deploy | CODEOWNERS (`config/**`, Mei); the Copilot hook; the deployment environment `production` |

The production password never reaches an agent: it lives only in the deployment environment `production`, never in
the Agents secrets.

A change to this file is a change to policy: it goes through a reviewed pull request, like a change to code. Moving an
action to a faster level needs its record to show it is safe: measure the same kind of work before and after the move
(time to merge, how often a pull request is sent back, checks passing on the first run, and reverts).
