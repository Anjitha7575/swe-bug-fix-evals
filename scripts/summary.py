#!/usr/bin/env python3
"""Print pass counts and run times per task and model from results/results.jsonl.

usage: python3 scripts/summary.py
Uses the latest 5 finished runs (pass/fail) per task+model. Crashed runs
(agent_error) are counted separately. A missing model name means the default
model (Opus 5.5) from before we recorded model names.
"""
import json
import statistics
from collections import defaultdict

from common import ROOT

rows = defaultdict(list)
errors = defaultdict(int)
for line in (ROOT / "results" / "results.jsonl").read_text().splitlines():
    r = json.loads(line)
    if r["agent"] != "claude":
        continue
    key = (r["task"], r.get("model") or "claude-opus-5-5")
    if r["status"] == "agent_error":
        errors[key] += 1
    else:
        rows[key].append(r)

print(f"{'task':28} {'model':18} {'pass':6} {'median s':9} {'min-max s':11} {'total min':9} {'crashes'}")
for key in sorted(rows):
    last = rows[key][-5:]
    secs = [r["seconds"] for r in last]
    passed = sum(r["status"] == "pass" for r in last)
    print(f"{key[0]:28} {key[1]:18} {passed}/{len(last):<4} {statistics.median(secs):<9.0f} "
          f"{min(secs):.0f}-{max(secs):.0f}".ljust(11) + f" {sum(secs)/60:<9.1f} {errors[key]}")