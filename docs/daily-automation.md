# Daily Automation

매일 아침 7시에 AI Morning Radar를 생성하고 발행한다.
**실행 엔진은 Claude Code(headless `claude -p`)이며, Hermes에 의존하지 않는다.**

## 구조

```
Windows 예약작업 (07시 cron + 절전 깨움 + 15분 캐치업)
  └─ scripts/daily_catchup_hidden.vbs   (콘솔 숨김 런처)
       └─ scripts/daily_catchup.cmd     (py -3 로 실행, 로그 redirect)
            └─ scripts/daily_catchup.py  (게이팅: 7시 이후·미발송·lock)
                 └─ scripts/daily_run.py (결정론적 파이프라인)
```

`daily_run.py` 단계:

1. **research** — `claude -p`(`prompts/daily_briefing.md` 프롬프트)로 최근 24시간 AI 뉴스를 조사해
   `briefings/{date}.md` 작성 + `data/published_items.csv` 갱신. **LLM은 이 산출물만 만든다.**
2. **render** — `scripts/render_briefing.py {date}` → `dist/email`, `dist/blog`
3. **email** — `scripts/send_email.py {date}` → Gmail API로 수신자에게 발송
4. **site** — `scripts/build_site.py` → `site/`
5. **publish** — git commit + push → GitHub Actions가 Pages 배포
6. **log** — `data/daily_delivery_log.csv`에 `status=sent` 기록 후 commit/push

이메일·git·로깅 같은 외부 동작은 모두 `daily_run.py`에서 결정론적으로 처리한다.
따라서 어떤 모델이 리서치를 하든 발송 파이프라인은 깨지지 않는다.

## 스케줄

```text
0 7 * * *   (로컬 시간 기준, Windows 예약작업)
```

## 인증

- **Claude:** 구독 OAuth(`~/.claude.json`)를 그대로 사용한다. headless `claude -p`가 자동 갱신.
  무인 실행에서 재로그인이 필요해지면 한 번 `claude` 로그인하거나 `ANTHROPIC_API_KEY`로 전환한다.
- **Gmail:** OAuth 사용자 토큰(`secrets/google_token.json`, `gmail.send` 스코프 + refresh_token)을 사용한다.
  access token은 `send_email.py`가 자동 갱신해 다시 저장한다. 토큰 탐색 순서:
  `$NEWSNBLOG_GOOGLE_TOKEN` → `secrets/google_token.json` → 레거시 Hermes 경로.
- **GitHub:** Windows 자격 증명 관리자에 저장된 git 자격으로 push.

## Python 런타임

`daily_catchup.cmd`는 `py -3`(시스템 Python313)로 실행한다 — Hermes venv가 아니라 실제 설치된
Python을 쓰므로 Hermes를 제거해도 동작한다. 필요한 패키지:

```text
google-api-python-client
google-auth
```

## 발송 대상

```text
kimhyo75@gmail.com
hyoya.kim@samsung.com
```

`scripts/send_email.py`의 `RECIPIENTS` 상수에서 관리한다.

## 블로그

- Repository: https://github.com/Beaten-to-it/newsNblog
- GitHub Pages: https://beaten-to-it.github.io/newsNblog/

## 포맷 원칙

- 한국어
- 세 줄 요약으로 시작
- 제목에 직접 링크
- GeekNews 같은 집계형 소스는 개별 항목 링크 제공
- 각 뉴스마다 `왜 중요한가` 포함
- `AI UseCase` 섹션 포함
- 독자용 본문에 `신뢰도`, `중복 여부`, 내부 발행 이력, 좋아요/폼 피드백을 노출하지 않음

## 절전/깨움 보완 실행

PC가 07:00에 절전 상태라면 정기 예약작업이 실행되지 않을 수 있다. 이를 보완하기 위해
Windows 예약작업 두 개를 둔다.

```text
newsNblog_Daily_Catchup          # 15분마다 체크
newsNblog_Daily_Catchup_OnWake   # Windows 절전 해제 이벤트 직후 체크
```

캐치업(`daily_catchup.py`)은 다음 조건일 때만 `daily_run.py`를 실행한다.

1. 현재 시간이 07:00 이후
2. `data/daily_delivery_log.csv`에 오늘 `status=sent` 로그가 없음
3. 최근 3시간 내 캐치업 lock이 없음

## 수동 실행

```bash
# 전체(리서치 포함)
py -3 scripts/daily_run.py --date 2026-06-09

# 리서치는 사람이 하고 파이프라인만(브리핑이 이미 있을 때)
py -3 scripts/daily_run.py --date 2026-06-09 --skip-research

# 로컬 테스트(발송·push 없이)
py -3 scripts/daily_run.py --date 2026-06-09 --skip-research --no-send --no-push

# 메일 1통 테스트(본인에게만)
py -3 scripts/send_email.py 2026-06-09 --to kimhyo75@gmail.com
```

## 레거시 (Hermes)

이전에는 Hermes cron job(`3917d9f92061`)이 발행을 담당했으나, 게이트웨이 프로세스가 죽거나
런타임(Codex) 토큰이 만료되면 무인 실행이 멈추는 문제가 있었다. 현재 이 job은 `paused` 상태이며
실행 경로는 위 Claude 기반 파이프라인으로 대체되었다.
