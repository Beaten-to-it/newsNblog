# AX 모닝 레이더 — 두 번째 트랙 파이프라인 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 "AI Morning Radar" 일일 파이프라인을 "트랙" 개념으로 일반화해, 박사연구 밀착형 "AX 모닝 레이더"를 두 번째 트랙으로 매일 생성·발송·발행한다 — AI 트랙의 경로·URL·이메일은 한 글자도 안 바꾸면서.

**Architecture:** 모든 트랙별 차이(프롬프트·폴더·CSV·수신자·사이트경로·브랜드·vault접근)를 단일 설정 모듈 `scripts/tracks.py`로 모은다. `render_briefing.py`·`send_email.py`·`build_site.py`·`daily_run.py`·`pages.yml`을 트랙 인자로 파라미터화하되, **track 기본값=`ai` + 레거시 경로 그대로** → 기존 호출(`render_briefing.py DATE`)이 안 깨진다. AX는 전부 새 하위경로(`briefings/ax/`, `dist/blog/ax/`, `site/ax/`)라 충돌 0. 발송/캐치업 게이팅은 트랙별 분리(한 트랙 실패가 다른 트랙을 막지 않음).

**Tech Stack:** Python 3.13(표준 라이브러리만 — argparse/dataclasses/pathlib), pytest 9.x, GitHub Actions(Pages), Gmail API(google-auth), headless `claude -p`.

**참조 스펙:** `docs/management-track-design.md` (§6 파이프라인 설계 확정).

---

## File Structure

| 파일 | 책임 | 변경 |
|---|---|---|
| `scripts/tracks.py` | 트랙 단일 진실원천(경로·이름·수신자·vault·브랜드). 순수·테스트 가능 | **신규** |
| `scripts/render_briefing.py` | 브리핑 md → 이메일 HTML/txt + 블로그 md. track 인자 | 수정 |
| `scripts/send_email.py` | Gmail 발송. track별 수신자·제목 | 수정 |
| `scripts/build_site.py` | 정적 사이트 빌드. 모든 트랙 각자 하위사이트로 | 수정 |
| `scripts/daily_run.py` | 오케스트레이션. 두 트랙 순차·resilient·트랙별 게이팅/로그 | 수정 |
| `prompts/management_briefing.md` | AX 리서치 프롬프트. 출력 경로 `briefings/ax/` | 수정 |
| `.github/workflows/pages.yml` | CI 렌더+빌드. AX도 렌더 | 수정 |
| `tests/test_tracks.py` | 트랙 설정·경로해석·하위호환 단위 테스트 | **신규** |
| `tests/conftest.py` | pytest가 `scripts/`를 import하도록 경로 설정 | **신규** |

**정리 대상(Task 8):** `scripts/_spike_management_run.py`, `data/_spike_management*.log`, `briefings/management/`(→ `briefings/ax/`로 이관), 일회성 작업 `newsNblog_MgmtSpike_OneShot`.

---

## Task 1: 트랙 설정 모듈 `scripts/tracks.py`

**Files:**
- Create: `scripts/tracks.py`
- Create: `tests/conftest.py`
- Test: `tests/test_tracks.py`

- [ ] **Step 1: conftest로 import 경로 설정**

Create `tests/conftest.py`:

```python
import sys
from pathlib import Path

# Allow `import tracks` etc. from scripts/ in tests.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
```

- [ ] **Step 2: 실패하는 테스트 작성**

Create `tests/test_tracks.py`:

```python
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
    # AI track must NOT live under any /ax/ subdir — existing URLs stay put.
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
    expected = ["kimhyo75@gmail.com", "hyoya.kim@samsung.com"]
    assert tracks.get_track("ai").recipients == expected
    assert tracks.get_track("ax").recipients == expected


def test_only_ax_gets_vault_add_dir():
    assert tracks.get_track("ai").add_dirs == []
    assert tracks.get_track("ax").add_dirs == ["C:/Project/myOS"]


def test_ai_brand_strings_unchanged_backward_compat():
    # These exact strings keep the live AI site/email byte-identical.
    ai = tracks.get_track("ai")
    assert ai.name == "AI Morning Radar"
    assert ai.tagline == "바쁜 사람을 위한 AI 뉴스 브리핑"
    assert ai.hero_eyebrow == "Daily AI Briefing"
    assert ai.email_footer == "Generated from newsNblog · links point to original sources"
```

- [ ] **Step 3: 테스트 실패 확인**

Run: `py -3 -m pytest tests/test_tracks.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tracks'`

- [ ] **Step 4: `scripts/tracks.py` 구현**

Create `scripts/tracks.py`:

```python
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
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `py -3 -m pytest tests/test_tracks.py -v`
Expected: PASS (7 passed)

- [ ] **Step 6: 커밋**

```bash
git add scripts/tracks.py tests/conftest.py tests/test_tracks.py
git commit -m "Add track config module (ai legacy paths + ax isolated subpaths)"
```

---

## Task 2: `render_briefing.py` 트랙 파라미터화

**Files:**
- Modify: `scripts/render_briefing.py`

기존 시그니처 `render_briefing.py DATE`는 그대로 동작해야 한다(CI·daily_run이 그렇게 부름). `--track` 옵션을 추가하고 기본값 `ai`.

- [ ] **Step 1: 하위호환 베이스라인 저장 (변경 전)**

Run:
```bash
py -3 scripts/render_briefing.py 2026-06-14
cp dist/email/2026-06-14.html /tmp/ai_email_baseline.html
cp dist/blog/2026-06-14.md /tmp/ai_blog_baseline.md
```
Expected: 파일 3개 생성, 베이스라인 2개 복사됨.

- [ ] **Step 2: `render_html`에 brand/tagline 인자 추가**

In `scripts/render_briefing.py`, change the `render_html` signature and the hardcoded eyebrow.

Replace:
```python
def render_html(md: str, title: str) -> str:
```
with:
```python
def render_html(md: str, title: str, *, brand: str = "AI Morning Radar",
                tagline: str = "Generated from newsNblog · links point to original sources") -> str:
```

Replace the hardcoded eyebrow line:
```python
      <div class="eyebrow">AI Morning Radar</div>
```
with:
```python
      <div class="eyebrow">{html.escape(brand)}</div>
```

Replace the hardcoded footer line:
```python
    <div class="footer">Generated from newsNblog · links point to original sources</div>
```
with:
```python
    <div class="footer">{html.escape(tagline)}</div>
```

- [ ] **Step 3: `main()`을 track 인자로 교체**

Replace the entire `main()` in `scripts/render_briefing.py` with:

```python
def main() -> int:
    import argparse
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import tracks

    ap = argparse.ArgumentParser(description="Render a briefing to email + blog")
    ap.add_argument("--track", default="ai", choices=list(tracks.TRACKS))
    ap.add_argument("date")
    args = ap.parse_args()

    track = tracks.get_track(args.track)
    p = {k: ROOT / v for k, v in track.paths(args.date).items()}

    md = p["briefing"].read_text(encoding="utf-8")
    first = next((l for l in md.splitlines() if l.strip()), "")
    title = first.lstrip("# ").strip() if first else f"{args.date} {track.name}"

    for out in (p["email_html"], p["email_txt"], p["blog_md"]):
        out.parent.mkdir(parents=True, exist_ok=True)

    p["email_html"].write_text(
        render_html(md, title, brand=track.name, tagline=track.email_footer),
        encoding="utf-8",
    )
    p["email_txt"].write_text(md, encoding="utf-8")
    p["blog_md"].write_text(md, encoding="utf-8")

    print(f"html={p['email_html']}")
    print(f"text={p['email_txt']}")
    print(f"blog={p['blog_md']}")
    return 0
```

- [ ] **Step 4: AI 트랙 하위호환 확인 (바이트 동일)**

Run:
```bash
py -3 scripts/render_briefing.py 2026-06-14
diff /tmp/ai_blog_baseline.md dist/blog/2026-06-14.md && echo "BLOG IDENTICAL"
diff /tmp/ai_email_baseline.html dist/email/2026-06-14.html && echo "EMAIL IDENTICAL"
```
Expected: `BLOG IDENTICAL` + `EMAIL IDENTICAL` (eyebrow 텍스트가 그대로 "AI Morning Radar"라 동일).

- [ ] **Step 5: AX 트랙 렌더 동작 확인**

Run:
```bash
py -3 scripts/render_briefing.py --track ax 2026-06-14
ls dist/email/ax/2026-06-14.html dist/blog/ax/2026-06-14.md
grep -c "AX 모닝 레이더" dist/email/ax/2026-06-14.html
```
Expected: 두 파일 존재, eyebrow에 "AX 모닝 레이더" ≥1.
(주의: 이 단계는 `briefings/ax/2026-06-14.md`가 있어야 한다 — Task 7에서 `briefings/management/`를 `briefings/ax/`로 이관하므로, Task 7을 먼저 했거나 임시로 `mkdir -p briefings/ax && cp briefings/management/2026-06-14.md briefings/ax/`로 둔 상태여야 함.)

- [ ] **Step 6: 커밋**

```bash
git add scripts/render_briefing.py
git commit -m "Parameterize render_briefing by track (--track, default ai keeps legacy paths)"
```

---

## Task 3: `send_email.py` 트랙 파라미터화

**Files:**
- Modify: `scripts/send_email.py`
- Test: `tests/test_send_email.py`

`send_email.py DATE` 기본 동작 유지(=ai). `--track` 추가 → 수신자·제목·읽을 경로를 트랙 설정에서.

- [ ] **Step 1: 실패하는 테스트 작성 (순수 로직: 제목·수신자)**

Create `tests/test_send_email.py`:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import send_email
import tracks


def test_subject_falls_back_to_track_name():
    ax = tracks.get_track("ax")
    # No briefing file => subject uses "{date} {track.name}"
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
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `py -3 -m pytest tests/test_send_email.py -v`
Expected: FAIL — `AttributeError: module 'send_email' has no attribute 'subject_for'`

- [ ] **Step 3: `send_email.py`에 순수 헬퍼 추출 + `--track` 추가**

In `scripts/send_email.py`, add near the top (after `ROOT = ...`):

```python
import sys
sys.path.insert(0, str(ROOT / "scripts"))
import tracks


def subject_for(track, date: str, briefing_text: str) -> str:
    first = next((l for l in briefing_text.splitlines() if l.strip()), "")
    if first:
        return first.lstrip("# ").strip()
    return f"{date} {track.name}"


def resolve_recipients(track, override: str) -> list[str]:
    if override:
        return [r.strip() for r in override.split(",") if r.strip()]
    return list(track.recipients)
```

Then replace the body of `main()` from the `ap = argparse...` block through recipient resolution so it uses the track. Replace:

```python
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
```

with:

```python
    ap = argparse.ArgumentParser(description="Send a daily briefing email")
    ap.add_argument("date", help="YYYY-MM-DD")
    ap.add_argument("--track", default="ai", choices=list(tracks.TRACKS))
    ap.add_argument("--to", default="", help="Comma-separated override recipients")
    ap.add_argument("--dry-run", action="store_true", help="Do not send; just report")
    args = ap.parse_args()

    date = args.date
    track = tracks.get_track(args.track)
    p = track.paths(date)
    html_path = ROOT / p["email_html"]
    txt_path = ROOT / p["email_txt"]
    brief_path = ROOT / p["briefing"]

    if not html_path.exists():
        raise SystemExit(f"ERROR: {html_path} not found. Run render_briefing.py --track {track.key} {date} first.")

    html_body = html_path.read_text(encoding="utf-8")
    text_body = txt_path.read_text(encoding="utf-8") if txt_path.exists() else ""

    briefing_text = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
    subject = subject_for(track, date, briefing_text)
    recipients = resolve_recipients(track, args.to)
```

(The module-level `RECIPIENTS` constant in send_email.py is now unused — leave it or delete it; `resolve_recipients` uses `track.recipients`.)

- [ ] **Step 4: 테스트 통과 확인**

Run: `py -3 -m pytest tests/test_send_email.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: dry-run 스모크 (AI·AX 둘 다, 발송 안 함)**

Run:
```bash
py -3 scripts/send_email.py 2026-06-14 --dry-run
py -3 scripts/send_email.py --track ax 2026-06-14 --dry-run
```
Expected: AI는 `subject='2026-06-14 AI Morning Radar'`·recipients 2인; AX는 `subject='2026-06-14 AX 모닝 레이더'`·recipients 2인. **실제 발송 없음.**

- [ ] **Step 6: 커밋**

```bash
git add scripts/send_email.py tests/test_send_email.py
git commit -m "Parameterize send_email by track (per-track recipients + subject)"
```

---

## Task 4: `build_site.py` 모든 트랙 빌드

**Files:**
- Modify: `scripts/build_site.py`

AI는 `site/` 루트(기존 그대로), AX는 `site/ax/` 독립 하위사이트. 각 트랙은 자기 `dist/blog/<...>`만 읽는다.

- [ ] **Step 1: 하위호환 베이스라인 (변경 전)**

Run:
```bash
py -3 scripts/build_site.py
cp site/index.html /tmp/ai_site_index_baseline.html
cp site/posts/2026-06-14.html /tmp/ai_post_baseline.html
```
Expected: 빌드 성공, 베이스라인 복사.

- [ ] **Step 2: `page()`·hero·brand를 트랙 인자로**

In `scripts/build_site.py`, replace the module-level path constants:
```python
POSTS_DIR = ROOT / "dist" / "blog"
SITE_DIR = ROOT / "site"
SITE_POSTS = SITE_DIR / "posts"
```
with:
```python
import sys
sys.path.insert(0, str(ROOT / "scripts"))
import tracks
```

Change `page()` to accept brand/tagline. Replace the hardcoded header block in `page()`:
```python
  <header class="site-header">
    <a class="brand" href="{html.escape(home_href, quote=True)}">AI Morning Radar</a>
    <span class="tagline">바쁜 사람을 위한 AI 뉴스 브리핑</span>
  </header>
```
with:
```python
  <header class="site-header">
    <a class="brand" href="{html.escape(home_href, quote=True)}">{html.escape(brand)}</a>
    <span class="tagline">{html.escape(tagline)}</span>
  </header>
```
and add `brand` + `tagline` params to `page()`:
```python
def page(
    title: str,
    content: str,
    *,
    brand: str = "AI Morning Radar",
    tagline: str = "바쁜 사람을 위한 AI 뉴스 브리핑",
    description: str = "AI Morning Radar",
    css_href: str = "assets/style.css",
    home_href: str = "index.html",
) -> str:
```

- [ ] **Step 3: `main()`을 트랙 루프로 교체**

Replace `main()` in `scripts/build_site.py` with a version that builds each track into its own `site_dir`. Replace the existing `main()` body up to (but not including) the CSS writing, with a loop. Full replacement of `main()`:

```python
def build_track(track) -> list:
    posts_dir = ROOT / track.blog_dir
    site_dir = ROOT / track.site_dir
    site_posts = site_dir / "posts"
    site_posts.mkdir(parents=True, exist_ok=True)
    (site_dir / "assets").mkdir(parents=True, exist_ok=True)

    posts = []
    for md_path in sorted(posts_dir.glob("*.md"), reverse=True):
        if md_path.name.startswith("_"):
            continue  # skip spike/backup artifacts like _2026-06-14.v1...
        date = md_path.stem
        md = md_path.read_text(encoding="utf-8")
        title = md.splitlines()[0].lstrip("# ").strip() if md.splitlines() else date
        content = f'<article class="post">\n{render_markdown(md)}\n</article>'
        (site_posts / f"{date}.html").write_text(
            page(title, content, brand=track.name, tagline=track.tagline,
                 description=title, css_href="../assets/style.css", home_href="../index.html"),
            encoding="utf-8",
        )
        posts.append((date, title, f"posts/{date}.html"))

    items = "\n".join(
        f'<li><a href="{href}">{html.escape(title)}</a><time>{date}</time></li>'
        for date, title, href in posts
    ) or "<li>아직 게시물이 없습니다.</li>"
    index_content = f"""
<section class="hero">
  <p class="eyebrow">{html.escape(track.hero_eyebrow)}</p>
  <h1>{html.escape(track.name)}</h1>
  <p>{html.escape(track.hero_blurb)}</p>
</section>
<section class="post-list">
  <h2>브리핑 아카이브</h2>
  <ul>{items}</ul>
</section>
"""
    (site_dir / "index.html").write_text(
        page(track.name, index_content, brand=track.name, tagline=track.tagline),
        encoding="utf-8",
    )
    (site_dir / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    return [site_dir / "index.html", *(site_posts.glob("*.html")), site_dir / "assets" / "style.css"]


def main() -> int:
    written = []
    for key in tracks.ORDER:
        track = tracks.get_track(key)
        if not (ROOT / track.blog_dir).exists():
            continue  # track has no rendered posts yet
        written += build_track(track)
    for path in written:
        print(path.relative_to(ROOT))
    print(f"built {len(written)} files across {len(tracks.ORDER)} tracks")
    return 0
```

- [ ] **Step 4: CSS를 모듈 상수로 승격**

The existing `css = """..."""` block inside the old `main()` must become a module-level constant `CSS` so `build_track` can reuse it. Move the CSS string to module level (after the regexes) as:
```python
CSS = """
:root { color-scheme: light; ... }
...
""".strip() + "\n"
```
(use the exact same CSS content currently in `build_site.py`).

- [ ] **Step 5: AI 루트 사이트 하위호환 확인**

Run:
```bash
py -3 scripts/build_site.py
diff /tmp/ai_site_index_baseline.html site/index.html && echo "INDEX IDENTICAL"
diff /tmp/ai_post_baseline.html site/posts/2026-06-14.html && echo "POST IDENTICAL"
```
Expected: 두 줄 IDENTICAL. AI 트랙의 `hero_eyebrow`("Daily AI Briefing")·`hero_blurb`·`tagline`·`email_footer`를 Task 1에서 기존값 그대로 박아뒀으므로 바이트 동일이 **설계상 보장**된다. 만약 diff가 나면 `tracks.py`의 AI 값이 기존 `build_site.py`/`render_briefing.py` 하드코딩 문자열과 정확히 일치하는지부터 확인.

- [ ] **Step 6: AX 하위사이트 생성 확인**

Run:
```bash
ls site/ax/index.html site/ax/posts/2026-06-14.html site/ax/assets/style.css
grep -c "AX 모닝 레이더" site/ax/index.html
```
Expected: 세 파일 존재, AX 브랜드 ≥1. (Task 7 이후 `dist/blog/ax/`에 렌더물이 있어야 함.)

- [ ] **Step 7: 커밋**

```bash
git add scripts/build_site.py tests/ scripts/tracks.py
git commit -m "Build a separate /ax/ sub-site per track; AI root output unchanged"
```

---

## Task 5: `daily_run.py` 두 트랙 오케스트레이션

**Files:**
- Modify: `scripts/daily_run.py`

핵심 요구: (1) 트랙별 게이팅·로그 분리, (2) 한 트랙 실패가 다른 트랙을 막지 않음(resilient), (3) AX 리서치에 vault `--add-dir`, (4) 사이트 빌드·push는 성공한 트랙들 묶어 1회.

- [ ] **Step 1: `research`·`already_sent`·`published_keys`를 트랙 인자로**

In `scripts/daily_run.py`, add `import tracks` (after `PY = sys.executable`):
```python
sys.path.insert(0, str(ROOT / "scripts"))
import tracks
```

Replace `already_sent(date)`:
```python
def already_sent(track, date: str) -> bool:
    log = ROOT / track.delivery_log
    if not log.exists():
        return False
    import csv
    with log.open(encoding="utf-8", newline="") as f:
        return any(r.get("date") == date and r.get("status") == "sent" for r in csv.DictReader(f))
```

Replace `published_keys()` to read the track CSV:
```python
def published_keys(track) -> str:
    csv_path = ROOT / track.published_csv
    if not csv_path.exists():
        return "(none)"
    import csv as _csv
    lines = []
    with csv_path.open(encoding="utf-8", newline="") as f:
        for r in _csv.DictReader(f):
            lines.append(f"- {r.get('first_published_date','')} | {r.get('title','')} | {r.get('url','')}")
    return "\n".join(lines[-40:]) if lines else "(none)"
```

Replace `research(date)` to take a track and inject its `add_dirs`:
```python
def research(track, date: str) -> None:
    prompt = (ROOT / track.prompt).read_text(encoding="utf-8").replace("{DATE}", date)
    prompt += f"\n\n## 이미 발행된 항목 (반복 금지)\n{published_keys(track)}\n"
    prompt += f"\n오늘 날짜: {date}\n"
    cmd = [find_claude(), "-p", prompt, "--permission-mode", "bypassPermissions",
           "--add-dir", str(ROOT)]
    for d in track.add_dirs:
        cmd += ["--add-dir", d]
    env = {**os.environ, "CLAUDE_INSIGHT_THROTTLE_MIN": "1000000"}
    res = run(cmd, capture_output=True, timeout=1500, env=env)
    if res.stdout:
        print(res.stdout[-2000:])
    if res.stderr:
        print(res.stderr[-1000:], file=sys.stderr)
    if res.returncode != 0:
        raise SystemExit(f"research step failed for track {track.key} (claude exit {res.returncode})")
```

Replace `verify_briefing(date)` to use the track path:
```python
def verify_briefing(track, date: str) -> Path:
    path = ROOT / track.paths(date)["briefing"]
    if not path.exists():
        raise SystemExit(f"ERROR: {path} was not produced; aborting track {track.key}.")
    text = path.read_text(encoding="utf-8")
    if len(text) < 800 or "세 줄 요약" not in text:
        raise SystemExit(f"ERROR: {path} looks incomplete ({len(text)} bytes); aborting track {track.key}.")
    return path
```

- [ ] **Step 2: per-track 처리 함수 추가**

Add a function that runs research→render→email for ONE track and returns whether it produced sendable content. Insert before `main()`:

```python
def run_track(track, date: str, *, skip_research: bool, no_send: bool) -> bool:
    """Returns True if the track produced a briefing ready to publish."""
    if not skip_research:
        research(track, date)
    verify_briefing(track, date)
    if run([PY, "scripts/render_briefing.py", "--track", track.key, date]).returncode != 0:
        raise SystemExit(f"render step failed for track {track.key}")
    if not no_send:
        if run([PY, "scripts/send_email.py", "--track", track.key, date]).returncode != 0:
            raise SystemExit(f"email step failed for track {track.key}")
    return True
```

- [ ] **Step 3: `main()` 재작성 — 두 트랙 resilient + 묶음 push**

Replace `main()` in `scripts/daily_run.py` with:

```python
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
        track = tracks.get_track(key)
        if already_sent(track, date) and not args.force:
            print(f"[{key}] {date} already sent; skipping.")
            continue
        try:
            if run_track(track, date, skip_research=args.skip_research, no_send=args.no_send):
                done.append(track)
        except SystemExit as e:
            # Resilient: one track failing must not block the others.
            print(f"[{key}] FAILED: {e}", file=sys.stderr)

    if not done:
        print("No track produced content; nothing to publish.")
        return 0

    # Build the whole site (every track with rendered posts) once.
    if run([PY, "scripts/build_site.py"]).returncode != 0:
        raise SystemExit("build_site step failed")

    # Publish content for successful tracks in one commit + push.
    if not args.no_push:
        add_paths = []
        for t in done:
            add_paths += [t.briefings_dir + f"/{date}.md", t.published_csv]
        git("add", *add_paths)
        git("commit", "-m", f"Publish {date} [{', '.join(t.key for t in done)}]")
        git("push", "origin", "main")
    sha = head_sha()

    # Per-track delivery log + commit.
    completed = datetime.now().isoformat(timespec="seconds")
    status = "rendered" if (args.no_send or args.no_push) else "sent"
    for t in done:
        pages_url = f"{PAGES_BASE}/{t.pages_path}posts/{date}.html"
        with (ROOT / t.delivery_log).open("a", encoding="utf-8", newline="") as f:
            f.write(f"{date},{status},,{sha},{pages_url},{completed},claude-driven pipeline\n")
    if not args.no_push:
        git("add", *[t.delivery_log for t in done])
        git("commit", "-m", f"Log {date} delivery [{', '.join(t.key for t in done)}]")
        git("push", "origin", "main")

    for t in done:
        print(f"DONE {date} [{t.key}]: status={status} pages={PAGES_BASE}/{t.pages_path}posts/{date}.html")
    return 0
```

- [ ] **Step 4: 각 트랙 delivery_log에 헤더 보장**

`already_sent` uses `csv.DictReader`, so each per-track log needs a header row. The AI log already has one. Create the AX log header so DictReader has field names:

Run:
```bash
[ -f data/daily_delivery_log_ax.csv ] || printf 'date,status,message_id,sha,pages_url,completed,note\n' > data/daily_delivery_log_ax.csv
cat data/daily_delivery_log_ax.csv
```
Expected: header row present.

- [ ] **Step 5: 전체 dry-run (발송·push 없음) — 두 트랙**

Run:
```bash
py -3 scripts/daily_run.py --date 2026-06-14 --skip-research --no-send --no-push
```
Expected: AI·AX 둘 다 render 단계 통과, build_site가 site/ 와 site/ax/ 둘 다 생성, "No track / DONE" 로그. 실제 발송·push 없음.
(주의: `--skip-research`라 `briefings/2026-06-14.md` 와 `briefings/ax/2026-06-14.md` 둘 다 존재해야 함 — Task 7 이관 완료 전이면 AX는 verify에서 실패하고 AI만 처리됨, 그래도 resilient하게 진행되는지 확인.)

- [ ] **Step 6: 커밋**

```bash
git add scripts/daily_run.py data/daily_delivery_log_ax.csv
git commit -m "Run both tracks in daily_run: per-track gating/log, resilient, vault add-dir for ax"
```

---

## Task 6: GitHub Pages CI(`pages.yml`) — AX 렌더 추가

**Files:**
- Modify: `.github/workflows/pages.yml`

CI는 push마다 `briefings/*.md`만 렌더한다. AX(`briefings/ax/*.md`)도 렌더해야 `/ax/`가 배포된다. `build_site.py`는 이미 모든 트랙을 빌드하므로 빌드 스텝은 그대로.

- [ ] **Step 1: 렌더 스텝에 AX 루프 추가**

In `.github/workflows/pages.yml`, replace the "Render email/blog artifacts" step:
```yaml
      - name: Render email/blog artifacts
        shell: bash
        run: |
          for f in briefings/*.md; do
            d="$(basename "$f" .md)"
            python scripts/render_briefing.py "$d"
          done
```
with:
```yaml
      - name: Render email/blog artifacts (all tracks)
        shell: bash
        run: |
          for f in briefings/*.md; do
            [ -e "$f" ] || continue
            d="$(basename "$f" .md)"
            python scripts/render_briefing.py "$d"
          done
          for f in briefings/ax/*.md; do
            [ -e "$f" ] || continue
            b="$(basename "$f" .md)"
            case "$b" in _*) continue;; esac   # skip spike/backup artifacts
            python scripts/render_briefing.py --track ax "$b"
          done
```

- [ ] **Step 2: 워크플로 YAML 유효성 확인**

Run:
```bash
py -3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/pages.yml',encoding='utf-8')); print('YAML OK')"
```
Expected: `YAML OK`. (pyyaml 미설치면 `py -3 -m pip install pyyaml` 후 재실행, 또는 육안 확인.)

- [ ] **Step 3: 커밋**

```bash
git add .github/workflows/pages.yml
git commit -m "CI: render AX track briefings so /ax/ sub-site deploys"
```

---

## Task 7: AX 프롬프트 출력 경로 + 스파이크 폴더 이관

**Files:**
- Modify: `prompts/management_briefing.md`
- Move: `briefings/management/*` → `briefings/ax/`

- [ ] **Step 1: 프롬프트 출력 경로를 `briefings/ax/`로**

In `prompts/management_briefing.md`, replace all occurrences of `briefings/management/` with `briefings/ax/` (the "완료 조건" path, the BRIEFING_WRITTEN marker, and the "디렉터리 ... 없으면 만들어라" line).

Run to verify none remain:
```bash
grep -c "briefings/management" prompts/management_briefing.md
```
Expected: `0`.

- [ ] **Step 1b: AX 프롬프트에 dedup CSV append 지시 추가**

The AI prompt instructs the model to append newly-covered items to `data/published_items.csv` (for cross-day dedup). The AX prompt currently has NO such instruction, so `data/published_items_ax.csv` would never be populated and AX would lose day-to-day dedup. Add an equivalent section to `prompts/management_briefing.md` (place it near "네가 할 일", mirroring the AI prompt's CSV section):

```markdown
## published_items_ax.csv append (중복 방지)

이번에 새로 다룬 핵심 항목을 `data/published_items_ax.csv`에 append 한다.
헤더: `canonical_key,first_published_date,title,url,source,section,tags,notes`
- `canonical_key`: 소문자-하이픈 슬러그 + `-{DATE}` 접미사 (예: `salesforce-ai-layoffs-2026-06-14`)
- `tags`는 세미콜론 구분, 콤마 포함 값은 큰따옴표로 감쌀 것.
- 위 "이미 발행된 항목" 목록에 있는 건 반복하지 않는다.
```

Verify the CSV exists with a header (daily_run gating/published_keys read it):
```bash
[ -f data/published_items_ax.csv ] || printf 'canonical_key,first_published_date,title,url,source,section,tags,notes\n' > data/published_items_ax.csv
```

- [ ] **Step 2: 검증용 브리핑만 이관(백업·스파이크 변형 제외)**

Run:
```bash
mkdir -p briefings/ax
git mv briefings/management/2026-06-14.md briefings/ax/2026-06-14.md 2>/dev/null || cp briefings/management/2026-06-14.md briefings/ax/2026-06-14.md
ls briefings/ax/
```
Expected: `briefings/ax/2026-06-14.md` 존재. (`_v1`/`_v2` 백업은 옮기지 않음 — Task 8에서 삭제.)

- [ ] **Step 3: 커밋**

```bash
git add prompts/management_briefing.md briefings/ax/2026-06-14.md
git commit -m "Point AX prompt at briefings/ax/; migrate validated briefing"
```

---

## Task 8: 스파이크 잔여물·일회성 작업 정리

**Files:**
- Delete: `scripts/_spike_management_run.py`, `data/_spike_management*.log`, `briefings/management/` (백업 포함)

- [ ] **Step 1: 일회성 예약 작업 제거**

Run (PowerShell):
```powershell
Unregister-ScheduledTask -TaskName newsNblog_MgmtSpike_OneShot -Confirm:$false -ErrorAction SilentlyContinue
Get-ScheduledTask -TaskName newsNblog_MgmtSpike_OneShot -ErrorAction SilentlyContinue
```
Expected: 두 번째 명령이 아무것도 출력하지 않음(작업 삭제됨).

- [ ] **Step 2: 스파이크 파일 삭제**

Run:
```bash
rm -f scripts/_spike_management_run.py data/_spike_management*.log
rm -rf briefings/management
ls briefings/ | grep -c management || echo "management gone"
```
Expected: `management gone`.

- [ ] **Step 3: 커밋**

```bash
git add -A
git commit -m "Remove management-track spike artifacts (superseded by ax pipeline)"
```

---

## Task 9: 엔드투엔드 검증 (실발송 1회 + 발행)

**Files:** 없음(실행만)

이미 발행된 AI 트랙은 건드리지 않도록 `--force`는 쓰지 않는다. 오늘 날짜로 AX만 처음으로 실제 발송·발행해 본다.

- [ ] **Step 1: AX 단독 실행(리서치→발송→발행)**

Run:
```bash
py -3 scripts/daily_run.py --tracks ax
```
Expected: AX 리서치(claude -p, vault 접근)→render→email 2인 발송→build_site→`Publish {today} [ax]` 커밋·push→`data/daily_delivery_log_ax.csv`에 sent 1행→`Log {today} delivery [ax]` 커밋·push. 콘솔에 `DONE {today} [ax]: ... pages=.../ax/posts/{today}.html`.

- [ ] **Step 2: 메일·사이트 확인**

- 받은편지함에 "{today} AX 모닝 레이더" 수신 확인(2인).
- GitHub Actions(pages.yml) 성공 후: `https://beaten-to-it.github.io/newsNblog/ax/` 랜딩 + `https://beaten-to-it.github.io/newsNblog/ax/posts/{today}.html` 200.

Run:
```bash
gh run watch "$(gh run list --workflow=pages.yml -L1 --json databaseId -q '.[0].databaseId')" --exit-status
curl -s -o /dev/null -w "%{http_code}\n" "https://beaten-to-it.github.io/newsNblog/ax/posts/$(date +%F).html"
```
Expected: 워크플로 success, HTTP `200`.

- [ ] **Step 3: AI 트랙 무손상 회귀 확인**

Run:
```bash
curl -s -o /dev/null -w "%{http_code}\n" "https://beaten-to-it.github.io/newsNblog/posts/2026-06-14.html"
curl -s -o /dev/null -w "%{http_code}\n" "https://beaten-to-it.github.io/newsNblog/"
```
Expected: 둘 다 `200` — 기존 AI URL이 그대로 살아있음.

- [ ] **Step 4: 전체 테스트 스위트**

Run: `py -3 -m pytest tests/ -v`
Expected: 전부 PASS.

- [ ] **Step 5: 다음날 무인 실행 확인(관찰)**

다음 아침 기존 일일 스케줄이 `daily_run.py`(인자 없음=두 트랙)를 돌려 AI·AX 둘 다 자동 발행되는지 `data/daily_delivery_log*.csv`와 메일로 확인.

---

## Self-Review 메모

- **스펙 커버리지:** §6 표의 모든 행(프롬프트·폴더·CSV·사이트·URL·제목·수신자) → Task 1 설정 + Task 2~6 반영. 연구 렌즈 vault 접근 → Task 5 `research()` add_dirs. 트랙별 게이팅 → Task 5. CI 배포 → Task 6. 하위호환(AI 불변) → Task 2·4의 baseline diff 단계로 강제 검증.
- **하위호환 리스크 1곳:** Task 4 Step 5에서 AI 루트 index의 hero 문구가 기존과 달라지면 diff 실패 → 그 경우 `tracks.py`에 hero 문구 필드를 추가해 AI엔 기존값을 박는 보정 지침을 같은 스텝에 명시함.
- **인터페이스 일관성:** `Track.paths(date)` 키(`briefing/email_html/email_txt/blog_md`)를 render/send/daily_run에서 동일하게 사용. `--track` 기본값 `ai`로 모든 스크립트 통일.

## 알려진 후속 (이번 범위 밖 — 배송 멱등성 강화)

Task 5 코드리뷰에서 드러난, **기존 단일 트랙 파이프라인에도 있던** 선재(pre-existing) 약점. 이번 기능(트랙 추가)의 범위가 아니라 별도 하드닝 과제로 분리한다:
- **이메일-후-로그 재발송 창:** 이메일은 `run_track`에서 발송되고 배송 로그는 `build_site` 이후에 기록됨. `build_site`가 실패하면 로그가 안 남아 다음 실행에서 재발송 위험. (이번에 git push 실패는 raise로 시끄럽게 처리하도록 보강함. build_site는 결정론적 로컬이라 실패 확률 낮음.)
- **SystemExit를 트랙 실패 제어흐름으로 사용:** 회복 가능한 트랙 실패와 치명적 중단이 같은 예외 타입. 장기적으로 `TrackError` 분리 권장.
- **research 중도 실패 시 `published_items*.csv` 더티:** 발송 안 됐는데 dedup 행이 남을 수 있음. dedup이 다음 실행에서 중복 억제하므로 무해하나 인지 필요.

→ 위 3건은 두 트랙 공통의 "배송 멱등성" 리팩터로 묶어 후속 처리.
