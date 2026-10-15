#!/usr/bin/env python3
"""Check a task is fair: empty patch must FAIL, reference fix must PASS (and naive patch must FAIL, if one exists).
Leaves work/<task> clean afterwards.

usage: python3 scripts/validate.py <task>
"""
import argparse
import subprocess
import sys

from common import ROOT
from grade import grade


def reset(work):
    subprocess.run(["git", "checkout", "."], cwd=work, capture_output=True)
    subprocess.run(["git", "clean", "-fd"], cwd=work, capture_output=True)


def with_patch(task, work, patch):
    reset(work)
    subprocess.run(["git", "apply", str(patch)], cwd=work, check=True)
    ok = grade(task, work)
    reset(work)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    task = ap.parse_args().task
    work = ROOT / "work" / task
    results = []

    reset(work)
    results.append(("empty patch", "FAIL", "PASS" if grade(task, work) else "FAIL"))
    ref = ROOT / "tasks" / task / "reference" / "fix.patch"
    results.append(("reference fix", "PASS", "PASS" if with_patch(task, work, ref) else "FAIL"))
    naive = ROOT / "tasks" / task / "controls" / "naive.patch"
    if naive.exists():
        results.append(("naive patch", "FAIL", "PASS" if with_patch(task, work, naive) else "FAIL"))
    reset(work)

    bad = False
    for name, want, got in results:
        mark = "ok" if want == got else "WRONG"
        bad |= want != got
        print(f"{name:14} expected {want}  got {got}  {mark}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
