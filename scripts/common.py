"""Shared helpers: paths and task.env parsing."""
import os
import shlex
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_task(task):
    """Read tasks/<task>/task.env (KEY=VALUE lines) into a dict."""
    cfg = {}
    for line in (ROOT / "tasks" / task / "task.env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, _, value = line.partition("=")
            cfg[key] = shlex.split(value)[0] if value else ""
    return cfg


def _load_dotenv():
    """Load KEY=VALUE lines from <repo>/.env into the environment (no extra packages needed)."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()
