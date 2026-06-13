#!/usr/bin/env python
"""Re-authenticate the Google OAuth user token used by the daily pipeline.

The daily run sends mail via a stored refresh token at secrets/google_token.json.
When Google revokes that refresh token (e.g. an OAuth consent screen left in
"Testing" status expires refresh tokens after 7 days), send_email.py dies with
`invalid_grant: Token has been expired or revoked` and the whole pipeline aborts
before the email/site/commit steps. Run this once to mint a fresh token.

This opens a browser for an interactive Google login, so it MUST be run by a
human — not headless. In a Claude Code session, prefix it with `!`:

    ! py -3 -m pip install --quiet google-auth-oauthlib
    ! py -3 scripts/reauth_google.py

It reuses the existing client_secret_*.json and preserves whatever scopes the
current token already grants, then writes the new credentials back to
secrets/google_token.json (the path send_email.py reads).
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN_PATH = ROOT / "secrets" / "google_token.json"

# Full scope set the pipeline's token has historically carried. Used as a
# fallback if the existing token file can't be read for its scopes.
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/contacts.readonly",
]


def client_secret_file() -> str:
    matches = sorted(glob.glob(str(ROOT / "client_secret_*.json")))
    if not matches:
        sys.exit(
            "ERROR: no client_secret_*.json found in the repo root. "
            "Download the OAuth client (Desktop app) from Google Cloud Console first."
        )
    return matches[0]


def existing_scopes() -> list[str]:
    if TOKEN_PATH.exists():
        try:
            scopes = json.loads(TOKEN_PATH.read_text(encoding="utf-8")).get("scopes")
            if scopes:
                return scopes
        except (ValueError, OSError):
            pass
    return DEFAULT_SCOPES


def main() -> int:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ModuleNotFoundError:
        sys.exit(
            "ERROR: google-auth-oauthlib is not installed.\n"
            "Run:  py -3 -m pip install google-auth-oauthlib"
        )

    secret = client_secret_file()
    scopes = existing_scopes()
    print(f"client_secret: {Path(secret).name}")
    print(f"scopes ({len(scopes)}):")
    for s in scopes:
        print(f"  - {s}")
    print("\nOpening browser for Google login... approve the consent screen.\n")

    flow = InstalledAppFlow.from_client_secrets_file(secret, scopes)
    # access_type=offline + prompt=consent forces Google to return a NEW
    # refresh_token (otherwise a re-consent may omit it).
    creds = flow.run_local_server(
        port=0, access_type="offline", prompt="consent"
    )

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    print(f"\nOK: new token written to {TOKEN_PATH}")
    print("Now re-run:  py -3 scripts/daily_run.py --date 2026-06-13")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
