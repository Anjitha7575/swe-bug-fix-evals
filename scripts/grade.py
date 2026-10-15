#!/usr/bin/env python3
"""Copy the task's hidden test into a work dir, run it, print PASS or FAIL.

usage: python3 scripts/grade.py <task> [workdir]   (workdir defaults to work/<task>)
exit code 0 = PASS, 1 = FAIL
"""
import argparse
import shutil
import subprocess
import sys

from common import ROOT, load_task


def grade(task, work=None):
    cfg = load_task(task)
    work = work or ROOT / "work" / task
    dest = work / cfg["HIDDEN_DEST"]
    shutil.copy(ROOT / "tasks" / task / "hidden" / cfg["HIDDEN_SRC"], dest)
    try:
        r = subprocess.run(cfg["TEST"], cwd=work, shell=True, capture_output=True, text=True)
    finally:
        dest.unlink(missing_ok=True)
    (work / ".grade.log").write_text(r.stdout + r.stderr)
    return r.returncode == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("workdir", nargs="?")
    a = ap.parse_args()
    from pathlib import Path
    ok = grade(a.task, Path(a.workdir).resolve() if a.workdir else None)
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)
