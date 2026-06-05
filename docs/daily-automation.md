# Daily Automation

매일 아침 7시에 AI Morning Radar를 생성하고 발행한다.

## 스케줄

```text
0 7 * * *
```

기준: 이 Windows/Hermes 환경의 로컬 시간.

## 자동 작업 범위

매일 cron job은 다음을 수행한다.

1. `C:\Project\newsNblog`에서 작업한다.
2. 최근 24시간/어제 기준 주요 AI 뉴스를 조사한다.
3. X/Threads/GeekNews/공식 블로그/개발자 커뮤니티/주요 미디어를 반영한다.
4. `data/published_items.csv`를 확인해 이미 다룬 뉴스는 반복하지 않는다.
5. 새 브리핑을 `briefings/YYYY-MM-DD.md`에 작성한다.
6. `data/published_items.csv`를 업데이트한다.
7. `python scripts/render_briefing.py YYYY-MM-DD`를 실행해 메일/블로그 산출물을 만든다.
8. Gmail API로 HTML 메일을 발송한다.
9. GitHub에 commit/push한다.
10. GitHub Actions Pages 배포가 성공했는지 확인한다.
11. 모든 단계가 성공하면 `data/daily_delivery_log.csv`에 `status=sent` 성공 로그를 남긴다.

## 발송 대상

```text
kimhyo75@gmail.com
hyoya.kim@samsung.com
```

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

## 운영 주의

- Google OAuth token과 GitHub gh 인증이 이 환경에 저장되어 있어야 한다.
- Hermes cron은 gateway/scheduler가 실행 중이어야 동작한다.
- 터미널을 닫아도 실행하려면 `hermes gateway install` / `hermes gateway start`로 서비스화되어 있어야 한다.

## 절전/깨움 보완 실행

PC가 07:00에 절전 상태라면 정기 cron이 실행되지 않을 수 있다. 이를 보완하기 위해 Windows Scheduled Task 두 개를 추가한다.

```text
newsNblog_Daily_Catchup          # 15분마다 체크
newsNblog_Daily_Catchup_OnWake   # Windows 절전 해제 이벤트 직후 체크
```

두 작업은 모두 아래 스크립트를 실행한다.

```text
C:\Project\newsNblog\scripts\daily_catchup.cmd
C:\Project\newsNblog\scripts\daily_catchup.py
```

캐치업 스크립트는 다음 조건일 때만 Hermes cron job을 즉시 실행한다.

1. 현재 시간이 07:00 이후
2. `data/daily_delivery_log.csv`에 오늘 `status=sent` 로그가 없음
3. 최근 3시간 내 캐치업 lock이 없음

따라서 절전에서 깨어났을 때 이미 오늘 발송이 끝났으면 아무것도 하지 않고, 아직 발송되지 않았다면 자동으로 보완 발행한다.
