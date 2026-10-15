#!/usr/bin/env python3
"""Run an AI agent on a task N times and log PASS/FAIL per run.

usage: python3 scripts/run_agent.py <task> <agent> [--runs N] [--timeout SEC]
example: python3 scripts/run_agent.py t1-stale-search gemini --runs 5

Results: results/results.jsonl (one line per run) and results/<task>/<agent>/run-N.diff
"""
import argparse
import json
import re
import subprocess
import time

from common import ROOT
from grade import grade

# How to launch each agent. {prompt} is the contents of the task's prompt.md.
AGENTS = {
    "gemini": lambda p, m: ["gemini", "--skip-trust", "-y"] + (["-m", m] if m else []) + ["-p", p],
    "claude": lambda p, m: ["claude", "-p", p, "--dangerously-skip-permissions"] + (["--model", m] if m else []),
    "codex": lambda p, m: ["codex", "exec", "--sandbox", "workspace-write"] + (["-m", m] if m else []) + [p],
    "agy": lambda p, m: ["agy", "-p", p, "--dangerously-skip-permissions"] + (["--model", m] if m else []),
    "noop": lambda p, m: ["true"],  # does nothing; used to test this script
}

TEST_FILE = re.compile(r"(\.test\.|\.spec\.|/__tests__/|/test/)")


def sh(cmd, cwd=None, timeout=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def agent_cmd(a, prompt):
    cmd = AGENTS[a.agent](prompt, a.model)
    if a.agent == "codex" and a.effort:
        cmd = cmd[:2] + ["-c", f"model_reasoning_effort={a.effort}"] + cmd[2:]
    return cmd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("agent", choices=AGENTS)
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--start", type=int, default=1, help="first run number (to resume after an interruption)")
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--retries", type=int, default=3, help="re-run if the agent crashes (503, network)")
    ap.add_argument("--model", default=None, help="e.g. gemini-2.5-flash")
    ap.add_argument("--effort", default=None, help="codex only: reasoning effort, e.g. high")
    a = ap.parse_args()

    work = ROOT / "work" / a.task
    if not work.exists():
        raise SystemExit(f"{work} missing. Run: ./scripts/setup.sh {a.task}")
    prompt = (ROOT / "tasks" / a.task / "prompt.md").read_text().strip()
    out_dir = ROOT / "results" / a.task / (a.agent + (f"-{a.model}" if a.model else "") + (f"-effort-{a.effort}" if a.effort else ""))
    out_dir.mkdir(parents=True, exist_ok=True)
    log = ROOT / "results" / "results.jsonl"

    # record exactly which model/version ran (evidence for the report)
    model_used, version = a.model, None
    if a.agent == "claude":
        cmd = ["claude", "-p", "Which model are you? Answer with the model id only."]
        if a.model:
            cmd += ["--model", a.model]
        try:
            model_used = sh(cmd, timeout=120).stdout.strip().splitlines()[-1]
            version = sh(["claude", "--version"], timeout=30).stdout.strip()
        except Exception as e:
            print("could not read model id:", e)
    if a.agent == "codex":
        version = sh(["codex", "--version"], timeout=30).stdout.strip()
    print(f"agent={a.agent} model={model_used} version={version}")

    for n in range(a.start, a.runs + 1):
        for attempt in range(1, a.retries + 2):
            # 1. reset to the buggy state
            sh(["git", "checkout", "."], cwd=work)
            sh(["git", "clean", "-fd"], cwd=work)

            # 2. run the agent inside the task folder (it never sees tasks/ or hidden tests)
            start = time.time()
            timed_out = False
            log_file = out_dir / f"run-{n}.log"
            try:
                # stream the agent's output live to the screen and to the log file
                with log_file.open("w") as lf:
                    proc = subprocess.Popen(agent_cmd(a, prompt), cwd=work, stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT, text=True, bufsize=1)
                    deadline = time.time() + a.timeout
                    for line in proc.stdout:
                        print("  |", line, end="")
                        lf.write(line)
                        if time.time() > deadline:
                            proc.kill()
                            raise subprocess.TimeoutExpired(proc.args, a.timeout)
                    agent_rc = proc.wait()
            except subprocess.TimeoutExpired:
                timed_out, agent_rc = True, -1
                print("agent timed out")
            secs = round(time.time() - start, 1)

            # 3. record what it changed
            changed = sh(["git", "diff", "--name-only"], cwd=work).stdout.split()
            (out_dir / f"run-{n}.diff").write_text(sh(["git", "diff"], cwd=work).stdout)

            # 4. grade with the hidden test
            passed = grade(a.task, work)

            rec = {
                "task": a.task, "agent": a.agent, "model": model_used, "effort": a.effort, "version": version, "run": n,
                "status": "agent_error" if (timed_out or agent_rc != 0) else ("pass" if passed else "fail"),
                "passed": passed,
                "seconds": secs, "agent_exit": agent_rc, "timed_out": timed_out,
                "files_changed": changed,
                "edited_tests": [f for f in changed if TEST_FILE.search(f)],
            }
            with log.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            print(f"run {n}/{a.runs}: {rec['status'].upper()}  {secs}s  files={changed}")
            if rec["status"] != "agent_error" or attempt > a.retries:
                break
            print(f"agent crashed (attempt {attempt}); waiting 60s then retrying...")
            time.sleep(60)

    sh(["git", "checkout", "."], cwd=work)  # leave the repo clean


if __name__ == "__main__":
    main()