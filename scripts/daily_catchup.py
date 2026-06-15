#!/usr/bin/env python
"""Catch up the daily newsNblog publish job after sleep/wake.

Runs quietly when nothing is needed. Intended to be called by Windows Task
Scheduler every 15 minutes. It triggers the daily publish only when:
- local time is at or after the configured publish hour, and
- today's delivery is not fully logged yet (ALL tracks sent), and
- a recent catch-up lock is not present.
"""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import subprocess

sys.path.insert(0, str(ROOT / "scripts"))
import tracks

# Tracks the unattended scheduler publishes every morning. Single source of
# truth for both the completion gate and the daily_run --tracks argument, so the
# gate can never check a different set than what actually runs.
TRACK_KEYS = ["ai", "ax"]

LOCK = ROOT / "data" / ".daily_catchup.lock"
DAILY_RUN = ROOT / "scripts" / "daily_run.py"
PUBLISH_HOUR = 7
LOCK_TTL = timedelta(hours=3)
# daily_run runs each track's research with a 1500s (25min) timeout, sequentially
# (ai then ax), plus render/email/build/push. Two tracks can legitimately need
# ~50min, so the catch-up must allow far more than the old 20min — otherwise it
# kills daily_run mid-run (e.g. after AX research but before AX render/email),
# leaving a half-published day. 1 hour gives comfortable headroom.
RUN_TIMEOUT = 3600


def today_key(now: datetime) -> str:
    return now.strftime("%Y-%m-%d")


def _log_has_sent(log_path: Path, day: str) -> bool:
    if not log_path.exists():
        return False
    try:
        with log_path.open("r", encoding="utf-8", newline="") as f:
            return any(
                row.get("date") == day and row.get("status") == "sent"
                for row in csv.DictReader(f)
            )
    except Exception as exc:
        print(f"WARN: could not read {log_path.name}: {exc}", file=sys.stderr)
        return False


def all_sent(day: str) -> bool:
    """True only when EVERY scheduled track has a 'sent' row for ``day``.

    Keying on all tracks (not just AI) is what lets a single-track failure
    self-heal: the next catch-up re-fires daily_run, whose own per-track guard
    (daily_run.already_sent) skips the already-sent tracks and retries only the
    missing one. Keying on AI alone meant an AX-only failure was never retried.
    """
    return all(
        _log_has_sent(ROOT / tracks.get_track(k).delivery_log, day)
        for k in TRACK_KEYS
    )


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


def clear_lock() -> None:
    try:
        LOCK.unlink()
    except FileNotFoundError:
        pass


def main() -> int:
    now = datetime.now()
    day = today_key(now)

    if now.hour < PUBLISH_HOUR:
        return 0
    if all_sent(day):
        return 0
    if lock_is_recent(now):
        return 0

    write_lock(now)
    # The AI and AX tracks both run every morning (AX go-live 2026-06-14).
    cmd = [sys.executable, str(DAILY_RUN), "--date", day, "--tracks", ",".join(TRACK_KEYS)]
    print(f"{now.isoformat()} triggering catch-up publish: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=RUN_TIMEOUT
        )
    finally:
        # Clear the lock once this run returns so the next 15-min tick can retry
        # immediately if the run only partially succeeded. (If THIS process is
        # itself killed, the finally is skipped and the stale lock's 3h TTL still
        # prevents a stampede.)
        clear_lock()
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
