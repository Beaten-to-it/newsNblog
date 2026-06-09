#!/usr/bin/env python
"""Send the AI Morning Radar email via the Gmail API.

Runtime-independent: uses a stored OAuth user token (refresh_token) so it never
depends on which agent/runtime produced the briefing. The access token is
auto-refreshed and written back to the token file.

Usage:
  python scripts/send_email.py 2026-06-09
  python scripts/send_email.py 2026-06-09 --to kimhyo75@gmail.com   # test to one address
  python scripts/send_email.py 2026-06-09 --dry-run                 # render only, no send

Token resolution order:
  1. $NEWSNBLOG_GOOGLE_TOKEN
  2. <repo>/secrets/google_token.json
  3. ~/AppData/Local/hermes/google_token.json  (legacy Hermes location)
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Default recipients for the daily briefing.
RECIPIENTS = ["kimhyo75@gmail.com", "hyoya.kim@samsung.com"]


def _token_path() -> Path:
    candidates = [
        os.environ.get("NEWSNBLOG_GOOGLE_TOKEN"),
        str(ROOT / "secrets" / "google_token.json"),
        str(Path.home() / "AppData" / "Local" / "hermes" / "google_token.json"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return Path(c)
    raise SystemExit(
        "ERROR: no google_token.json found. Set NEWSNBLOG_GOOGLE_TOKEN or place "
        "the token at secrets/google_token.json."
    )


def _credentials(token_path: Path):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    data = json.loads(token_path.read_text(encoding="utf-8"))
    scopes = data.get("scopes") or ["https://www.googleapis.com/auth/gmail.send"]
    creds = Credentials.from_authorized_user_file(str(token_path), scopes)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")
    if not creds.valid:
        raise SystemExit("ERROR: stored Google token is invalid; re-authenticate.")
    return creds


def _build_message(to_addr: str, subject: str, html_body: str, text_body: str) -> dict:
    msg = MIMEText(html_body, "html", "utf-8")
    msg["To"] = to_addr
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


def main() -> int:
    ap = argparse.ArgumentParser(description="Send AI Morning Radar email")
    ap.add_argument("date", help="YYYY-MM-DD")
    ap.add_argument("--to", default="", help="Comma-separated override recipients")
    ap.add_argument("--dry-run", action="store_true", help="Do not send; just report")
    args = ap.parse_args()

    date = args.date
    html_path = ROOT / "dist" / "email" / f"{date}.html"
    txt_path = ROOT / "dist" / "email" / f"{date}.txt"
    brief_path = ROOT / "briefings" / f"{date}.md"

    if not html_path.exists():
        raise SystemExit(f"ERROR: {html_path} not found. Run render_briefing.py {date} first.")

    html_body = html_path.read_text(encoding="utf-8")
    text_body = txt_path.read_text(encoding="utf-8") if txt_path.exists() else ""

    subject = f"{date} AI Morning Radar"
    if brief_path.exists():
        first = next((l for l in brief_path.read_text(encoding="utf-8").splitlines() if l.strip()), "")
        if first:
            subject = first.lstrip("# ").strip()

    recipients = [r.strip() for r in args.to.split(",") if r.strip()] if args.to else RECIPIENTS

    if args.dry_run:
        print(f"[dry-run] subject={subject!r}")
        print(f"[dry-run] recipients={recipients}")
        print(f"[dry-run] html={html_path} ({len(html_body)} bytes)")
        return 0

    creds = _credentials(_token_path())
    from googleapiclient.discovery import build

    service = build("gmail", "v1", credentials=creds)

    sent = []
    for to_addr in recipients:
        body = _build_message(to_addr, subject, html_body, text_body)
        result = service.users().messages().send(userId="me", body=body).execute()
        sent.append({"to": to_addr, "id": result["id"]})
        print(f"sent to {to_addr}: {result['id']}")

    print(json.dumps({"status": "sent", "subject": subject, "messages": sent}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
