#!/usr/bin/env python
"""Single source of truth for per-track configuration.

A "track" is one daily briefing stream (research prompt -> briefing -> email +
blog). The `ai` track keeps the ORIGINAL legacy paths so existing GitHub Pages
URLs and emails never change; the `ax` track lives entirely under isolated
subpaths (briefings/ax, dist/blog/ax, site/ax) so the two never collide.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

RECIPIENTS = ["kimhyo75@gmail.com", "hyoya.kim@samsung.com"]


@dataclass(frozen=True)
class Track:
    key: str
    name: str               # brand + email subject suffix
    tagline: str            # site header tagline / email eyebrow
    prompt: str             # research prompt file (relative to repo root)
    briefings_dir: str      # where {date}.md briefings live
    published_csv: str      # dedup DB
    delivery_log: str       # per-track delivery log (gating)
    email_dir: str          # dist email output dir
    blog_dir: str           # dist blog output dir
    site_dir: str           # static site output dir
    pages_path: str         # URL path under the Pages base, e.g. "" or "ax/"
    hero_eyebrow: str       # site landing hero eyebrow (kept exact for ai = byte-identical)
    hero_blurb: str         # site landing hero paragraph
    email_footer: str       # email footer line (kept exact for ai = byte-identical)
    recipients: list[str] = field(default_factory=lambda: list(RECIPIENTS))
    add_dirs: list[str] = field(default_factory=list)  # extra --add-dir for research

    def paths(self, date: str) -> dict[str, Path]:
        return {
            "briefing": Path(self.briefings_dir) / f"{date}.md",
            "email_html": Path(self.email_dir) / f"{date}.html",
            "email_txt": Path(self.email_dir) / f"{date}.txt",
            "blog_md": Path(self.blog_dir) / f"{date}.md",
        }


AI = Track(
    key="ai",
    name="AI Morning Radar",
    tagline="바쁜 사람을 위한 AI 뉴스 브리핑",
    prompt="prompts/daily_briefing.md",
    briefings_dir="briefings",
    published_csv="data/published_items.csv",
    delivery_log="data/daily_delivery_log.csv",
    email_dir="dist/email",
    blog_dir="dist/blog",
    site_dir="site",
    pages_path="",
    hero_eyebrow="Daily AI Briefing",
    hero_blurb="AI 뉴스, X/Threads 트렌드, GeekNews 개발자 관점, 세 줄 요약과 AI UseCase를 아침에 빠르게 읽는 브리핑입니다.",
    email_footer="Generated from newsNblog · links point to original sources",
)

AX = Track(
    key="ax",
    name="AX 모닝 레이더",
    tagline="AI 전환·조직변화·경영 연구 밀착 브리핑",
    prompt="prompts/management_briefing.md",
    briefings_dir="briefings/ax",
    published_csv="data/published_items_ax.csv",
    delivery_log="data/daily_delivery_log_ax.csv",
    email_dir="dist/email/ax",
    blog_dir="dist/blog/ax",
    site_dir="site/ax",
    pages_path="ax/",
    hero_eyebrow="Daily Briefing",
    hero_blurb="AI 전환·조직 변화·변화 저항을 축으로, 경영·MIS/DX를 곁들인 연구 밀착형 일일 브리핑입니다.",
    email_footer="Generated from newsNblog · AX 모닝 레이더",
    add_dirs=["C:/Project/myOS"],
)

TRACKS: dict[str, Track] = {AI.key: AI, AX.key: AX}
ORDER = ["ai", "ax"]  # processing order in daily_run


def get_track(key: str = "ai") -> Track:
    return TRACKS[key]
