from pathlib import Path
import pytest
import tracks


def test_get_track_ai_and_ax():
    assert tracks.get_track("ai").key == "ai"
    assert tracks.get_track("ax").key == "ax"


def test_unknown_track_raises():
    with pytest.raises(KeyError):
        tracks.get_track("nope")


def test_default_track_is_ai():
    assert tracks.get_track().key == "ai"


def test_ai_uses_legacy_paths_backward_compat():
    ai = tracks.get_track("ai")
    p = ai.paths("2026-06-14")
    assert p["briefing"] == Path("briefings/2026-06-14.md")
    assert p["email_html"] == Path("dist/email/2026-06-14.html")
    assert p["blog_md"] == Path("dist/blog/2026-06-14.md")
    assert ai.site_dir == "site"
    assert "ax" not in str(p["email_html"])


def test_ax_uses_isolated_subpaths():
    ax = tracks.get_track("ax")
    p = ax.paths("2026-06-14")
    assert p["briefing"] == Path("briefings/ax/2026-06-14.md")
    assert p["email_html"] == Path("dist/email/ax/2026-06-14.html")
    assert p["blog_md"] == Path("dist/blog/ax/2026-06-14.md")
    assert ax.site_dir == "site/ax"
    assert ax.published_csv == "data/published_items_ax.csv"
    assert ax.delivery_log == "data/daily_delivery_log_ax.csv"


def test_recipients_same_two_for_both():
    expected = ("kimhyo75@gmail.com", "hyoya.kim@samsung.com")
    assert tracks.get_track("ai").recipients == expected
    assert tracks.get_track("ax").recipients == expected


def test_only_ax_gets_vault_add_dir():
    assert tracks.get_track("ai").add_dirs == ()
    assert tracks.get_track("ax").add_dirs == ("C:/Project/myOS",)


def test_ai_brand_strings_unchanged_backward_compat():
    # These exact strings keep the live AI site/email byte-identical.
    ai = tracks.get_track("ai")
    assert ai.name == "AI Morning Radar"
    assert ai.tagline == "바쁜 사람을 위한 AI 뉴스 브리핑"
    assert ai.hero_eyebrow == "Daily AI Briefing"
    assert ai.email_footer == "Generated from newsNblog · links point to original sources"
