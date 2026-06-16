# Blog Translation Pages — Design (2026-06-17)

## Goal
For each blog post (AI track + AX track) whose cited **source articles are in a
foreign language**, offer a **translate button next to the post title**. Clicking
it opens a **separate, pre-generated page** that renders the foreign source
articles' content as a **long-form Korean write-up** (deeper than the briefing's
3-line summaries). Pages must be styled like the rest of the site (readable, not
raw text). Translation is done by **Claude** (not Codex — Codex translation
quality is insufficient per the user).

## Scope (confirmed with user)
- One translate button **per post** (next to the post `<h1>`), one translated
  page per post.
- The translated page covers **all** foreign-language-sourced items in that post.
- Korean-sourced items are excluded (reader can read the native source directly).
- If a post has **no** foreign-language sources, **no** translation file is
  generated and **no** button appears.
- Applies going forward; past posts have no translation files (optional backfill later).
- Email behavior unchanged: the email links to the post page; the translate
  button lives only on the blog page.

## Architecture (Approach A: separate content tree + Claude pipeline step)

### Content & routing
- Source markdown: `translations/{trackkey}/{date}.md` (`translations/ai/…`, `translations/ax/…`).
- Rendered page: `site/{pages_path}translated/{date}.html`
  - AI: `site/translated/{date}.html`  → `…/newsNblog/translated/{date}.html`
  - AX: `site/ax/translated/{date}.html` → `…/newsNblog/ax/translated/{date}.html`
- `tracks.Track` gains: `translations_dir` (property → `translations/{key}`),
  `translated_md(date)`, `translated_url(date)`. `PAGES_BASE` already the single
  source of truth in tracks.py.

### Generation (`daily_run.translate(track, date)`) — Claude
- Re-introduce `find_claude()` (research now uses Codex; translation uses Claude).
- `claude -p <prompt> --permission-mode bypassPermissions --add-dir ROOT`, with
  `CLAUDE_INSIGHT_THROTTLE_MIN` set (suppress the global Stop hook on nightly
  runs), longer timeout (~1800s) since it fetches multiple articles.
- Prompt: read `briefings/{track}/{date}.md`; identify items whose **source is a
  non-Korean language**; for each, **WebFetch the source URL** and write a
  long-form Korean exposition; assemble into `translations/{key}/{date}.md`
  mirroring the briefing's markdown style (headings + source links).
  - **Anti-fabrication:** paywalled/blocked sources (e.g. WSJ 401, businesswire
    bot-block) → do not invent; use what's accessible + the briefing's existing
    info, and mark "원문 접근 제한". (Aligns with vault `paper-note-hallucination-audit`.)
  - If there are **no** foreign-language sources, output exactly
    `NO_FOREIGN_SOURCES`. `translate()` then removes/skips the file → no page/button.
- **Resilience:** translation failure must NOT block delivery. `translate()` is
  wrapped in try/except inside `run_track`; a failure logs a warning and the
  track still publishes (email already sent before this step).

### Rendering (`build_site.py`)
- `build_track` additionally globs `translations/{key}/*.md` → renders each to
  `site/{pages_path}translated/{date}.html` via the existing `page()` + CSS, with
  a "← 브리핑으로 돌아가기" link back to `../posts/{date}.html`.
- In the **post** rendering loop: if `translations/{key}/{date}.md` exists, inject
  a toolbar with the translate button (`../translated/{date}.html`) above the
  article title.
- New CSS: `.post-toolbar` (right-aligned) + `.xlate-btn` (button styling).

### Pipeline placement & publish
- `run_track`: research(Codex) → verify → render → email → **translate(Claude)**.
  (After email so a slow/failed translation never delays or blocks delivery.)
- `main()` publish commit also `git add translations/{key}/{date}.md` for each
  done track **when the file exists**.
- CI (`pages.yml`) unchanged: its `build_site` step renders committed
  `translations/` into the deployed site. (Translation *generation* is local —
  CI cannot run Claude.)

## Button placement (post page)
```
┌────────────────────────────────────────────────────┐
│ 2026-06-17 AI Morning Radar      [🌐 원문 한국어로 자세히] │
│ ──────────────────────────────────────────────────  │
│ ## 1. 세 줄 요약 ...                                   │
```

## Edge cases
- Mixed Korean + foreign sources in one post → translate only the foreign items.
- All-Korean post → no file, no button.
- Paywalled / bot-blocked source → partial + "원문 접근 제한" note, never fabricate.
- HTML-escaping in the rendered translated page reuses the existing
  escape-once-then-regex `inline_md` (no double-escape; same as posts).

## Out of scope
- Backfilling translations for past posts (06-05…06-16).
- Adding the translate link into the email.
- Non-Korean target languages (target is always Korean expansion of foreign source).

## Verification plan
- Live test `translate()` on a **past** date with foreign sources (e.g. 2026-06-16)
  so today's in-progress briefing edits are untouched; confirm fetch + Korean
  quality + no fabrication.
- `build_site` renders the translated page and the post button correctly
  (relative links resolve, CSS applied).
- Adversarial multi-dimension review (correctness, build/CI, edge cases,
  styling/UX, HTML-injection) via a workflow; fix confirmed findings.
