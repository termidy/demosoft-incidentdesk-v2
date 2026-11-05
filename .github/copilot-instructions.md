# Instructions for Copilot in incidentdesk

- Every change that users can notice adds one line to CHANGELOG.md
  under "## Unreleased", in plain words for on-call engineers.

- Run the tests with `scripts/test.sh`, not plain `pytest`: it runs the suite twice,
  with the machine's clock in UTC and in Asia/Singapore (#24).

- Long tasks keep a progress log (`docs/progress/<issue>.md`) and a decision log (`docs/decisions.md`). A session starts by reading both and continues from the first file that is not ticked.
- Do one step of the plan per session. Tick a file only when its tests pass.
- Follow the decisions in `docs/decisions.md`. To change one, add a new decision that links to it and says why; never delete one.
