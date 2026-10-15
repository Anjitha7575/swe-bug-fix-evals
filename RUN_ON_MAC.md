# Check a task
python3 scripts/setup.py t1-stale-search
python3 scripts/grade.py t1-stale-search                     # FAIL (bug present)
git -C work/t1-stale-search apply ../../tasks/t1-stale-search/reference/fix.patch
python3 scripts/grade.py t1-stale-search                     # PASS
git -C work/t1-stale-search checkout .
# Run an agent
python3 scripts/run_agent.py t1-stale-search gemini --runs 1
