#!/usr/bin/env python
"""Render AI Morning Radar markdown to simple HTML email and blog markdown.

No external dependencies. This is intentionally small for v0.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def inline_md(s: str) -> str:
    # Escape ONCE up front. The regex passes below run on already-escaped text,
    # so they must NOT re-escape their captured groups — doing so double-escapes
    # (e.g. &quot; -> &amp;quot;) any " < > & inside **bold**, [links], `code`.
    s = html.escape(s)
    s = LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', s)
    s = CODE_RE.sub(lambda m: f'<code>{m.group(1)}</code>', s)
    s = BOLD_RE.sub(lambda m: f'<strong>{m.group(1)}</strong>', s)
    return s


def render_html(md: str, title: str, *, brand: str = "AI Morning Radar",
                tagline: str = "Generated from newsNblog · links point to original sources") -> str:
    body = []
    in_ul = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            body.append('</ul>')
            in_ul = False

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line:
            close_ul()
            continue
        if line == '---':
            close_ul()
            body.append('<hr>')
            continue
        if line.startswith('# '):
            close_ul()
            body.append(f'<h1>{inline_md(line[2:].strip())}</h1>')
        elif line.startswith('## '):
            close_ul()
            body.append(f'<h2>{inline_md(line[3:].strip())}</h2>')
        elif line.startswith('### '):
            close_ul()
            body.append(f'<h3>{inline_md(line[4:].strip())}</h3>')
        elif line.startswith('> '):
            close_ul()
            body.append(f'<blockquote>{inline_md(line[2:].strip())}</blockquote>')
        elif line.lstrip().startswith('- '):
            if not in_ul:
                body.append('<ul>')
                in_ul = True
            item = line.lstrip()[2:].strip()
            body.append(f'<li>{inline_md(item)}</li>')
        else:
            close_ul()
            body.append(f'<p>{inline_md(line.strip())}</p>')
    close_ul()

    return f'''<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    body {{ margin:0; padding:0; background:#f5f7fb; color:#172033; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans KR",Arial,sans-serif; line-height:1.62; }}
    .wrap {{ max-width:680px; margin:0 auto; padding:28px 14px 48px; }}
    .card {{ background:#ffffff; border:1px solid #e7ebf3; border-radius:18px; padding:28px; box-shadow:0 10px 30px rgba(20,34,66,.06); }}
    .eyebrow {{ color:#5b6b86; font-size:13px; letter-spacing:.08em; text-transform:uppercase; margin-bottom:8px; }}
    h1 {{ font-size:28px; line-height:1.25; margin:0 0 22px; color:#101828; }}
    h2 {{ font-size:20px; margin:34px 0 14px; padding-top:18px; border-top:1px solid #edf0f6; color:#18243a; }}
    h3 {{ font-size:17px; margin:26px 0 10px; color:#22314f; }}
    p {{ margin:10px 0; }}
    ul {{ padding-left:22px; margin:10px 0 18px; }}
    li {{ margin:7px 0; }}
    a {{ color:#2563eb; text-decoration:none; font-weight:600; }}
    a:hover {{ text-decoration:underline; }}
    blockquote {{ margin:14px 0 22px; padding:16px 18px; background:#eef6ff; border-left:4px solid #3b82f6; border-radius:12px; color:#153459; font-weight:600; }}
    hr {{ border:0; height:1px; background:#edf0f6; margin:28px 0; }}
    code {{ background:#f2f4f7; border-radius:6px; padding:1px 5px; font-size:.92em; }}
    .footer {{ margin-top:18px; color:#667085; font-size:12px; text-align:center; }}
    @media (max-width:520px) {{ .card {{ padding:20px; border-radius:14px; }} h1 {{ font-size:24px; }} h2 {{ font-size:18px; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="eyebrow">{html.escape(brand)}</div>
      {''.join(body)}
    </div>
    <div class="footer">{html.escape(tagline)}</div>
  </div>
</body>
</html>
'''


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


if __name__ == '__main__':
    raise SystemExit(main())
