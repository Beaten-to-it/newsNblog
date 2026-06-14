import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import send_email
import tracks


def test_subject_falls_back_to_track_name():
    ax = tracks.get_track("ax")
    subj = send_email.subject_for(ax, "2026-06-14", briefing_text="")
    assert subj == "2026-06-14 AX 모닝 레이더"


def test_subject_uses_briefing_first_line_when_present():
    ai = tracks.get_track("ai")
    subj = send_email.subject_for(ai, "2026-06-14", briefing_text="# 2026-06-14 AI Morning Radar\n\n...")
    assert subj == "2026-06-14 AI Morning Radar"


def test_recipients_default_from_track():
    ax = tracks.get_track("ax")
    assert send_email.resolve_recipients(ax, override="") == ["kimhyo75@gmail.com", "hyoya.kim@samsung.com"]
    assert send_email.resolve_recipients(ax, override="a@b.com, c@d.com") == ["a@b.com", "c@d.com"]
