#!/usr/bin/env python
"""Build a small GitHub Pages-ready static blog for AI Morning Radar."""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import tracks

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")

CSS = """
:root { color-scheme: light; --bg:#f5f7fb; --card:#fff; --text:#172033; --muted:#667085; --link:#2563eb; --line:#e7ebf3; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans KR",Arial,sans-serif; line-height:1.68; }
a { color:var(--link); text-decoration:none; font-weight:650; }
a:hover { text-decoration:underline; }
.site-header { max-width:920px; margin:0 auto; padding:28px 18px 8px; display:flex; gap:14px; align-items:baseline; }
.brand { color:#101828; font-size:20px; font-weight:800; }
.tagline { color:var(--muted); font-size:14px; }
.container { max-width:920px; margin:0 auto; padding:18px 18px 48px; }
.hero, .post, .post-list { background:var(--card); border:1px solid var(--line); border-radius:22px; padding:32px; box-shadow:0 10px 30px rgba(20,34,66,.06); }
.hero h1, .post h1 { margin-top:0; font-size:34px; line-height:1.2; }
.eyebrow { color:#5b6b86; font-size:13px; letter-spacing:.08em; text-transform:uppercase; font-weight:700; }
.post h2 { font-size:23px; margin:38px 0 14px; padding-top:22px; border-top:1px solid #edf0f6; }
.post h3 { font-size:18px; margin:28px 0 10px; }
.post ul, .post ol { padding-left:24px; }
.post li { margin:7px 0; }
blockquote { margin:16px 0 24px; padding:16px 18px; background:#eef6ff; border-left:4px solid #3b82f6; border-radius:12px; color:#153459; font-weight:650; }
hr { border:0; height:1px; background:#edf0f6; margin:28px 0; }
code { background:#f2f4f7; border-radius:6px; padding:1px 5px; font-size:.92em; }
.post-list { margin-top:18px; }
.post-list ul { list-style:none; padding:0; margin:0; }
.post-list li { display:flex; justify-content:space-between; gap:16px; padding:14px 0; border-top:1px solid #edf0f6; }
.post-list time { color:var(--muted); white-space:nowrap; }
.site-footer { max-width:920px; margin:0 auto; padding:0 18px 36px; color:var(--muted); font-size:13px; text-align:center; }
.post-toolbar { display:flex; justify-content:flex-end; gap:10px; margin:0 0 4px; }
.xlate-btn { display:inline-block; background:#2563eb; color:#ffffff; font-weight:700; text-decoration:none; padding:9px 16px; border-radius:10px; font-size:14px; }
.xlate-btn:hover { background:#1d4ed8; text-decoration:none; }
@media (max-width:640px) { .site-header { display:block; } .hero, .post, .post-list { padding:22px; border-radius:16px; } .hero h1, .post h1 { font-size:28px; } .post-list li { display:block; } }
""".strip() + "\n"


# Allow only safe URL schemes in rendered links. html.escape() does NOT neutralize
# javascript:/data:/vbscript: — the scheme is plain text and browsers decode any
# entities in href before dispatching it, so a [text](javascript:...) link from a
# (possibly hostile) fetched source would be a clickable XSS payload. Whitelist
# http/https/mailto and scheme-less (relative/anchor) URLs; neutralize the rest.
_SCHEME_RE = re.compile(r"^\s*([a-zA-Z][a-zA-Z0-9+.\-]*)\s*:")


def _safe_href(url: str) -> str:
    m = _SCHEME_RE.match(url)
    if m and m.group(1).lower() not in ("http", "https", "mailto"):
        return "#"
    return url


def inline_md(s: str) -> str:
    # Escape ONCE up front. The regex passes below run on already-escaped text,
    # so they must NOT re-escape their captured groups — doing so double-escapes
    # (e.g. &quot; -> &amp;quot;) any " < > & inside **bold**, [links], `code`.
    s = html.escape(s)
    s = LINK_RE.sub(lambda m: f'<a href="{_safe_href(m.group(2))}">{m.group(1)}</a>', s)
    s = CODE_RE.sub(lambda m: f'<code>{m.group(1)}</code>', s)
    s = BOLD_RE.sub(lambda m: f'<strong>{m.group(1)}</strong>', s)
    return s


def render_markdown(md: str) -> str:
    body: list[str] = []
    in_ul = False
    in_ol = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            body.append("</ul>")
            in_ul = False
        if in_ol:
            body.append("</ol>")
            in_ol = False

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line:
            close_lists()
            continue
        if line == "---":
            close_lists()
            body.append("<hr>")
        elif line.startswith("# "):
            close_lists()
            body.append(f"<h1>{inline_md(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            close_lists()
            body.append(f"<h2>{inline_md(line[3:].strip())}</h2>")
        elif line.startswith("### "):
            close_lists()
            body.append(f"<h3>{inline_md(line[4:].strip())}</h3>")
        elif line.startswith("> "):
            close_lists()
            body.append(f"<blockquote>{inline_md(line[2:].strip())}</blockquote>")
        elif re.match(r"^\d+\.\s+", line):
            if not in_ol:
                close_lists()
                body.append("<ol>")
                in_ol = True
            item = re.sub(r"^\d+\.\s+", "", line)
            body.append(f"<li>{inline_md(item)}</li>")
        elif line.lstrip().startswith("- "):
            if not in_ul:
                close_lists()
                body.append("<ul>")
                in_ul = True
            body.append(f"<li>{inline_md(line.lstrip()[2:].strip())}</li>")
        else:
            close_lists()
            body.append(f"<p>{inline_md(line.strip())}</p>")
    close_lists()
    return "\n".join(body)


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
    """Render a page using relative links so project GitHub Pages paths work.

    GitHub project pages are served under /newsNblog/, so root-absolute
    links like /assets/style.css point at the account root and break.
    """
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(description, quote=True)}">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="{html.escape(css_href, quote=True)}">
</head>
<body>
  <header class="site-header">
    <a class="brand" href="{html.escape(home_href, quote=True)}">{html.escape(brand)}</a>
    <span class="tagline">{html.escape(tagline)}</span>
  </header>
  <main class="container">
    {content}
  </main>
  <footer class="site-footer">Generated by newsNblog · Original sources linked in each item</footer>
</body>
</html>
"""


def build_track(track: "tracks.Track") -> list[Path]:
    posts_dir = ROOT / track.blog_dir
    site_dir = ROOT / track.site_dir
    site_posts = site_dir / "posts"
    site_posts.mkdir(parents=True, exist_ok=True)
    (site_dir / "assets").mkdir(parents=True, exist_ok=True)

    # Renderable Korean translation pages, keyed by date. A file that is empty or
    # the NO_FOREIGN_SOURCES sentinel is treated as "no translation" so the post
    # button and the translation page stay in lockstep (no button -> no page,
    # and never a button pointing at a missing page).
    xlate_dir = ROOT / track.translations_dir
    translations: dict[str, str] = {}
    if xlate_dir.exists():
        for tp in xlate_dir.glob("*.md"):
            if tp.name.startswith("_"):
                continue
            txt = tp.read_text(encoding="utf-8").strip()
            if txt and txt != "NO_FOREIGN_SOURCES":
                translations[tp.stem] = txt + "\n"

    posts = []
    for md_path in sorted(posts_dir.glob("*.md"), reverse=True):
        if md_path.name.startswith("_"):
            continue  # skip spike/backup artifacts like _2026-06-14.v1...
        date = md_path.stem
        md = md_path.read_text(encoding="utf-8")
        title = md.splitlines()[0].lstrip("# ").strip() if md.splitlines() else date
        toolbar = (
            f'<div class="post-toolbar"><a class="xlate-btn" '
            f'href="../translated/{date}.html">🌐 원문 한국어로 자세히</a></div>\n'
            if date in translations else ""
        )
        content = f'<article class="post">\n{toolbar}{render_markdown(md)}\n</article>'
        (site_posts / f"{date}.html").write_text(
            page(title, content, brand=track.name, tagline=track.tagline,
                 description=title, css_href="../assets/style.css", home_href="../index.html"),
            encoding="utf-8",
        )
        posts.append((date, title, f"posts/{date}.html"))

    # Translation pages: same template/CSS as posts, with a back-link to the post.
    written_xlate: list[Path] = []
    site_xlate = site_dir / "translated"
    if translations:
        site_xlate.mkdir(parents=True, exist_ok=True)
        for date, tmd in sorted(translations.items(), reverse=True):
            lines = tmd.splitlines()
            ttitle = lines[0].lstrip("# ").strip() if lines else f"{date} {track.name}"
            back = (f'<div class="post-toolbar"><a class="xlate-btn" '
                    f'href="../posts/{date}.html">← 브리핑으로 돌아가기</a></div>\n')
            tcontent = f'<article class="post">\n{back}{render_markdown(tmd)}\n</article>'
            out = site_xlate / f"{date}.html"
            out.write_text(
                page(ttitle, tcontent, brand=track.name, tagline=track.tagline,
                     description=ttitle, css_href="../assets/style.css", home_href="../index.html"),
                encoding="utf-8",
            )
            written_xlate.append(out)
    # Drop stale translated pages whose source md no longer exists, so a removed
    # translation can't leave an orphan in the local site/ tree. (CI builds from a
    # clean checkout, so production is unaffected either way.)
    if site_xlate.exists():
        for hp in site_xlate.glob("*.html"):
            if hp.stem not in translations:
                hp.unlink()

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
        page(track.name, index_content, brand=track.name, tagline=track.tagline, description=track.name),
        encoding="utf-8",
    )
    (site_dir / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    return [site_dir / "index.html", *(site_posts.glob("*.html")), *written_xlate,
            site_dir / "assets" / "style.css"]


def main() -> int:
    written = []
    built = 0
    for key in tracks.ORDER:
        track = tracks.get_track(key)
        if not (ROOT / track.blog_dir).exists():
            continue  # track has no rendered posts yet
        written += build_track(track)
        built += 1
    for path in written:
        print(path.relative_to(ROOT))
    print(f"built {len(written)} files across {built} tracks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
