# bug-fix-evals
3 hand-built SWE eval tasks from real bugs.
- `python3 scripts/setup.py <task>`: clone upstream at the pinned commit and install deps
- `python3 scripts/grade.py <task>`: run the hidden test (PASS/FAIL)
- `python3 scripts/run_agent.py <task> <agent> --runs N`: run an AI agent N times and log results
Controls per task: empty patch (must FAIL), reference patch (must PASS), naive patch (must FAIL).
