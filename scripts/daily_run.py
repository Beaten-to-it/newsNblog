#!/usr/bin/env python
"""Daily AI Morning Radar pipeline — Claude-driven, Hermes-free.

Flow:
  1. (research)   claude -p with prompts/daily_briefing.md  -> briefings/{date}.md
                  + data/published_items.csv update   (skip with --skip-research)
  2. (render)     scripts/render_briefing.py {date}    -> dist/email + dist/blog
  3. (email)      scripts/send_email.py {date}         -> Gmail to recipients
  4. (site)       scripts/build_site.py                -> site/
  5. (publish)    git commit + push                    -> GitHub Pages deploy
  6. (log)        append data/daily_delivery_log.csv (status=sent) + commit/push

The LLM only produces the briefing markdown + csv row. Everything outward-facing
(email, git, logging) is deterministic here, so delivery never depends on which
model ran the research.

Usage:
  python scripts/daily_run.py                 # full pipeline for today
  python scripts/daily_run.py --date 2026-06-09
  python scripts/daily_run.py --skip-research # briefing already written
  python scripts/daily_run.py --no-send --no-push   # local dry test
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG = ROOT / "data" / "daily_delivery_log.csv"
PROMPT_FILE = ROOT / "prompts" / "daily_briefing.md"
PAGES_BASE = "https://beaten-to-it.github.io/newsNblog"


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(str(c) for c in cmd)}", flush=True)
    return subprocess.run(cmd, cwd=str(ROOT), text=True, **kw)


def already_sent(date: str) -> bool:
    if not LOG.exists():
        return False
    import csv
    with LOG.open(encoding="utf-8", newline="") as f:
        return any(r.get("date") == date and r.get("status") == "sent" for r in csv.DictReader(f))


def published_keys() -> str:
    """Return a compact list of already-published titles for the prompt context."""
    csv_path = ROOT / "data" / "published_items.csv"
    if not csv_path.exists():
        return "(none)"
    import csv as _csv
    lines = []
    with csv_path.open(encoding="utf-8", newline="") as f:
        for r in _csv.DictReader(f):
            lines.append(f"- {r.get('first_published_date','')} | {r.get('title','')} | {r.get('url','')}")
    # Only the most recent ~40 to keep the prompt bounded.
    return "\n".join(lines[-40:]) if lines else "(none)"


def find_claude() -> str:
    for c in (
        os.environ.get("CLAUDE_EXE"),
        shutil.which("claude"),
        shutil.which("claude.cmd"),
        str(Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd"),
        str(Path.home() / ".local" / "bin" / "claude.exe"),
    ):
        if c and Path(c).exists():
            return c
    return "claude"


def research(date: str) -> None:
    prompt = PROMPT_FILE.read_text(encoding="utf-8").replace("{DATE}", date)
    prompt += f"\n\n## 이미 발행된 항목 (반복 금지)\n{published_keys()}\n"
    prompt += f"\n오늘 날짜: {date}\n"
    cmd = [
        find_claude(), "-p", prompt,
        "--permission-mode", "bypassPermissions",
        "--add-dir", str(ROOT),
    ]
    res = run(cmd, capture_output=True, timeout=900)
    if res.stdout:
        print(res.stdout[-2000:])
    if res.stderr:
        print(res.stderr[-1000:], file=sys.stderr)
    if res.returncode != 0:
        raise SystemExit(f"research step failed (claude exit {res.returncode})")


def verify_briefing(date: str) -> Path:
    path = ROOT / "briefings" / f"{date}.md"
    if not path.exists():
        raise SystemExit(f"ERROR: {path} was not produced; aborting before send.")
    text = path.read_text(encoding="utf-8")
    if len(text) < 800 or "세 줄 요약" not in text:
        raise SystemExit(f"ERROR: {path} looks incomplete ({len(text)} bytes); aborting before send.")
    return path


def git(*args: str) -> subprocess.CompletedProcess:
    return run(["git", *args], capture_output=True)


def head_sha() -> str:
    r = git("rev-parse", "--short", "HEAD")
    return (r.stdout or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    ap.add_argument("--skip-research", action="store_true")
    ap.add_argument("--no-send", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--force", action="store_true", help="run even if already logged as sent")
    args = ap.parse_args()
    date = args.date

    if already_sent(date) and not args.force:
        print(f"{date} already sent; nothing to do.")
        return 0

    # 1. research
    if not args.skip_research:
        research(date)
    verify_briefing(date)

    # 2. render
    if run([PY, "scripts/render_briefing.py", date]).returncode != 0:
        raise SystemExit("render step failed")

    # 3. email
    if not args.no_send:
        if run([PY, "scripts/send_email.py", date]).returncode != 0:
            raise SystemExit("email step failed")

    # 4. site
    if run([PY, "scripts/build_site.py"]).returncode != 0:
        raise SystemExit("build_site step failed")

    # 5. publish content
    if not args.no_push:
        git("add", f"briefings/{date}.md", "data/published_items.csv")
        git("commit", "-m", f"Publish {date} AI Morning Radar")
        git("push", "origin", "main")
    sha = head_sha()
    pages_url = f"{PAGES_BASE}/posts/{date}.html"

    # 6. delivery log
    completed = datetime.now().isoformat(timespec="seconds")
    status = "rendered" if (args.no_send or args.no_push) else "sent"
    note = "claude-driven pipeline" + (" (local test)" if (args.no_send or args.no_push) else "")
    with LOG.open("a", encoding="utf-8", newline="") as f:
        f.write(f"{date},{status},,{sha},{pages_url},{completed},{note}\n")
    if not args.no_push:
        git("add", "data/daily_delivery_log.csv")
        git("commit", "-m", f"Log {date} delivery")
        git("push", "origin", "main")

    print(f"DONE {date}: status={status} sha={sha} pages={pages_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
