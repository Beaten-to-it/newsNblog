#!/usr/bin/env python
"""Catch up the daily newsNblog publish job after sleep/wake.

Runs quietly when nothing is needed. Intended to be called by Windows Task
Scheduler every 15 minutes. It triggers the Hermes cron job only when:
- local time is at or after the configured publish hour, and
- today's successful delivery is not logged yet, and
- a recent catch-up lock is not present.
"""
from __future__ import annotations

import csv
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "data" / "daily_delivery_log.csv"
LOCK = ROOT / "data" / ".daily_catchup.lock"
DAILY_RUN = ROOT / "scripts" / "daily_run.py"
PUBLISH_HOUR = 7
LOCK_TTL = timedelta(hours=3)


def today_key(now: datetime) -> str:
    return now.strftime("%Y-%m-%d")


def already_sent(day: str) -> bool:
    if not LOG.exists():
        return False
    try:
        with LOG.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return any(row.get("date") == day and row.get("status") == "sent" for row in reader)
    except Exception as exc:
        print(f"WARN: could not read delivery log: {exc}", file=sys.stderr)
        return False


def lock_is_recent(now: datetime) -> bool:
    if not LOCK.exists():
        return False
    try:
        ts = datetime.fromisoformat(LOCK.read_text(encoding="utf-8").strip())
    except Exception:
        return False
    return now - ts < LOCK_TTL


def write_lock(now: datetime) -> None:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(now.isoformat(), encoding="utf-8")


def main() -> int:
    now = datetime.now()
    day = today_key(now)

    if now.hour < PUBLISH_HOUR:
        return 0
    if already_sent(day):
        return 0
    if lock_is_recent(now):
        return 0

    write_lock(now)
    # AX track is validated but not yet auto-published. Until a human flips this
    # to "ai,ax" (AX go-live), the unattended scheduler runs the AI track only.
    cmd = [sys.executable, str(DAILY_RUN), "--date", day, "--tracks", "ai"]
    print(f"{now.isoformat()} triggering catch-up publish: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=1200)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
