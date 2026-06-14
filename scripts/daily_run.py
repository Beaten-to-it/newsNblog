#!/usr/bin/env python
"""Daily pipeline orchestrator — processes ALL configured tracks (ai, ax, …).

Flow per track:
  1. (research)   claude -p with track's prompt -> briefings/{track}/{date}.md
                  + track's published_csv update   (skip with --skip-research)
  2. (render)     scripts/render_briefing.py --track {key} {date}
  3. (email)      scripts/send_email.py --track {key} {date}
Then, once for all done tracks:
  4. (site)       scripts/build_site.py
  5. (publish)    git commit + push (briefings + published csvs)
  6. (log)        append per-track delivery logs + commit/push

Resilience: a failing track (research/verify/render/email) is caught and logged;
the remaining tracks continue unaffected.

Usage:
  python scripts/daily_run.py                 # full pipeline, all tracks, today
  python scripts/daily_run.py --date 2026-06-09
  python scripts/daily_run.py --tracks ai     # single track
  python scripts/daily_run.py --skip-research # briefings already written
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

# Scheduled-task consoles on Windows default to cp949, which crashes on any
# non-cp949 char (e.g. em-dash) the moment we print. Force utf-8 so logging a
# command or the prompt never aborts the pipeline.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
sys.path.insert(0, str(ROOT / "scripts"))
import tracks

PAGES_BASE = "https://beaten-to-it.github.io/newsNblog"


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    # Don't dump multi-KB prompt bodies into the log; show only short args.
    shown = [c if len(str(c)) <= 120 else f"<{len(str(c))} chars>" for c in cmd]
    print(f"$ {' '.join(str(c) for c in shown)}", flush=True)
    # text=True decodes child output with the cp949 locale on Windows, which
    # crashes the reader thread on utf-8/Korean bytes. Force utf-8 here too.
    kw.setdefault("encoding", "utf-8")
    kw.setdefault("errors", "replace")
    return subprocess.run(cmd, cwd=str(ROOT), text=True, **kw)


def already_sent(track, date: str) -> bool:
    log = ROOT / track.delivery_log
    if not log.exists():
        return False
    import csv
    with log.open(encoding="utf-8", newline="") as f:
        return any(r.get("date") == date and r.get("status") == "sent" for r in csv.DictReader(f))


def published_keys(track) -> str:
    """Return a compact list of already-published titles for the prompt context."""
    csv_path = ROOT / track.published_csv
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


def research(track, date: str) -> None:
    prompt = (ROOT / track.prompt).read_text(encoding="utf-8").replace("{DATE}", date)
    prompt += f"\n\n## 이미 발행된 항목 (반복 금지)\n{published_keys(track)}\n"
    prompt += f"\n오늘 날짜: {date}\n"
    cmd = [find_claude(), "-p", prompt, "--permission-mode", "bypassPermissions",
           "--add-dir", str(ROOT)]
    for d in track.add_dirs:
        cmd += ["--add-dir", d]
    # Headless runs get a fresh session_id every time, so the global Stop hook
    # (insight harvest) would fire its one-shot block on every nightly run.
    # The hook reads this env var; a huge throttle disables it for this child only.
    env = {**os.environ, "CLAUDE_INSIGHT_THROTTLE_MIN": "1000000"}
    res = run(cmd, capture_output=True, timeout=1500, env=env)
    if res.stdout:
        print(res.stdout[-2000:])
    if res.stderr:
        print(res.stderr[-1000:], file=sys.stderr)
    if res.returncode != 0:
        raise SystemExit(f"research step failed for track {track.key} (claude exit {res.returncode})")


def verify_briefing(track, date: str) -> Path:
    path = ROOT / track.paths(date)["briefing"]
    if not path.exists():
        raise SystemExit(f"ERROR: {path} was not produced; aborting track {track.key}.")
    text = path.read_text(encoding="utf-8")
    if len(text) < 800 or "세 줄 요약" not in text:
        raise SystemExit(f"ERROR: {path} looks incomplete ({len(text)} bytes); aborting track {track.key}.")
    return path


def git(*args: str) -> subprocess.CompletedProcess:
    return run(["git", *args], capture_output=True)


def head_sha() -> str:
    r = git("rev-parse", "--short", "HEAD")
    return (r.stdout or "").strip()


def run_track(track, date: str, *, skip_research: bool, no_send: bool) -> None:
    """Run research/verify/render/email for one track; raises SystemExit on failure."""
    if not skip_research:
        research(track, date)
    verify_briefing(track, date)
    if run([PY, "scripts/render_briefing.py", "--track", track.key, date]).returncode != 0:
        raise SystemExit(f"render step failed for track {track.key}")
    if not no_send:
        if run([PY, "scripts/send_email.py", "--track", track.key, date]).returncode != 0:
            raise SystemExit(f"email step failed for track {track.key}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    ap.add_argument("--tracks", default=",".join(tracks.ORDER),
                    help="comma-separated track keys to run")
    ap.add_argument("--skip-research", action="store_true")
    ap.add_argument("--no-send", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    date = args.date
    keys = [k.strip() for k in args.tracks.split(",") if k.strip()]

    done = []   # tracks that produced publishable content this run
    for key in keys:
        try:
            track = tracks.get_track(key)
            if already_sent(track, date) and not args.force:
                print(f"[{key}] {date} already sent; skipping.")
                continue
            run_track(track, date, skip_research=args.skip_research, no_send=args.no_send)
            done.append(track)
        except SystemExit as e:
            print(f"[{key}] FAILED: {e}", file=sys.stderr)
        except Exception as e:
            print(f"[{key}] FAILED: {e}", file=sys.stderr)

    if not done:
        print("No track produced content; nothing to publish.")
        return 0

    if run([PY, "scripts/build_site.py"]).returncode != 0:
        raise SystemExit("build_site step failed")

    if not args.no_push:
        add_paths = []
        for t in done:
            add_paths += [t.briefings_dir + f"/{date}.md", t.published_csv]
        git("add", *add_paths)
        c = git("commit", "-m", f"Publish {date} [{', '.join(t.key for t in done)}]")
        if c.returncode != 0:
            raise SystemExit(f"publish commit failed: {(c.stderr or c.stdout or '').strip()[:300]}")
        pu = git("push", "origin", "main")
        if pu.returncode != 0:
            raise SystemExit(f"publish push failed: {(pu.stderr or pu.stdout or '').strip()[:300]}")
    sha = head_sha()

    completed = datetime.now().isoformat(timespec="seconds")
    status = "rendered" if (args.no_send or args.no_push) else "sent"
    for t in done:
        pages_url = f"{PAGES_BASE}/{t.pages_path}posts/{date}.html"
        with (ROOT / t.delivery_log).open("a", encoding="utf-8", newline="") as f:
            f.write(f"{date},{status},,{sha},{pages_url},{completed},claude-driven pipeline\n")
    if not args.no_push:
        git("add", *[t.delivery_log for t in done])
        c = git("commit", "-m", f"Log {date} delivery [{', '.join(t.key for t in done)}]")
        if c.returncode != 0:
            raise SystemExit(f"log commit failed: {(c.stderr or c.stdout or '').strip()[:300]}")
        pu = git("push", "origin", "main")
        if pu.returncode != 0:
            raise SystemExit(f"log push failed: {(pu.stderr or pu.stdout or '').strip()[:300]}")

    for t in done:
        print(f"DONE {date} [{t.key}]: status={status} pages={PAGES_BASE}/{t.pages_path}posts/{date}.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
