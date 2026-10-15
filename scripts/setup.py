#!/usr/bin/env python3
"""Clone a task's upstream repo at its pinned commit into work/<task> and install deps.

usage: python3 scripts/setup.py <task>
"""
import argparse
import shutil
import subprocess

from common import ROOT, load_task


def setup(task):
    cfg = load_task(task)
    work = ROOT / "work" / task
    if work.exists():
        shutil.rmtree(work)
    work.parent.mkdir(exist_ok=True)
    subprocess.run(["git", "clone", "-q", "--filter=blob:none", cfg["REPO"], str(work)], check=True)
    subprocess.run(["git", "checkout", "-q", cfg["COMMIT"]], cwd=work, check=True)
    # Remove the upstream repo's own AI-agent instructions/hooks so every agent starts from the same neutral state.
    agent_files = [".claude", "CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursor", ".cursorrules",
                   ".github/copilot-instructions.md", ".gemini"]
    subprocess.run(["git", "rm", "-rq", "--ignore-unmatch", *agent_files], cwd=work, check=True)
    subprocess.run(["git", "-c", "user.email=eval@local", "-c", "user.name=eval", "commit", "-qm",
                    "eval: remove upstream agent config", "--allow-empty"], cwd=work, check=True)
    # install commands use shell syntax (cd, &&), so run through the shell
    subprocess.run(cfg["INSTALL"], cwd=work, shell=True, check=True)
    print(f"setup done for {task}: {work}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    setup(ap.parse_args().task)
