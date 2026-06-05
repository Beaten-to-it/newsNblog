# User Preferences — AI Morning Radar v0

사용자가 `기본값으로 시작`을 승인했으므로, v0는 아래 기본값으로 운영한다.

## 1. 브리핑 시간 / 기준 기간

- 발행 시간: 매일 오전 8시 KST 기준
- 대상 기간: 최근 24시간
- 날짜 표기: KST 기준 `YYYY-MM-DD`

## 2. 언어와 톤

- 언어: 한국어
- 톤: 개발자/창업자 관점의 간결한 해설형
- 스타일:
  - `한 줄 요약` 대신 `세 줄 요약`으로 시작
  - 단순 링크 모음보다 `왜 중요한가`를 반드시 포함
  - `AI UseCase` 섹션을 포함해 실제 활용 아이디어를 짧게 제시
  - 루머와 공식 확인 정보, 중복 체크는 내부적으로 구분하되 독자용 본문에는 `신뢰도`, `중복 여부` 라벨을 노출하지 않음
  - 과장된 표현보다 맥락 중심
  - 5분 안에 읽을 수 있는 밀도

## 3. 관심 주제 우선순위

1. AI 에이전트
2. AI 코딩 도구
3. OpenAI / Anthropic / Google / xAI 모델 업데이트
4. 오픈소스 LLM
5. AI 스타트업 / 제품 / 투자
6. 멀티모달 / 이미지 / 비디오 생성 AI
7. 논문 / 벤치마크
8. 기업용 AI / 생산성 도구
9. 한국 개발자 커뮤니티 반응
10. 규제 / 저작권 / 정책 — 큰 뉴스만

## 4. X / Threads 추적 키워드

- AI agents
- coding agents
- agentic workflow
- Claude Code
- OpenAI
- Anthropic
- Claude
- ChatGPT
- GPT
- Gemini
- Grok
- Llama
- Qwen
- DeepSeek
- Mistral
- Cursor
- Windsurf
- Devin
- SWE-bench
- multimodal AI
- AI video
- AI image
- open source LLM
- AI benchmark

## 5. X / Threads 계정

- v0에서는 지정 계정 없이 검색 기반으로 시작한다.
- Day 1~Day 7 피드백에서 반복적으로 좋은 출처가 나오면 v1 후보에 추가한다.

## 6. GeekNews

- GeekNews는 v0부터 필수 소스로 포함한다.
- GeekNews URL: https://news.hada.io/
- RSS: https://feeds.feedburner.com/geeknews-feed
- GeekNews는 한국 개발자 관점 필터로 사용한다.

## 7. 중복 기준

기본값: **보통 기준**

- 같은 발표의 단순 재보도는 제외한다.
- 같은 URL은 제외한다.
- 제목만 다르고 핵심 내용이 같은 X/Threads 논의는 제외한다.
- 벤치마크, 가격, 개발자 반응, 논란, 실제 사용 후기 등 새 정보가 있으면 `후속` 또는 `업데이트`로 포함할 수 있다.
- 발행 후 핵심 항목은 `data/published_items.csv`에 기록한다.

## 8. 제외 / 낮은 우선순위

- CEO 트윗 하나만 근거인 미확인 루머는 Top 5에 넣지 않는다.
- 스크린샷만 있는 주장은 단독 근거로 Top 5에 넣지 않는다.
- 규제/정책은 큰 변화가 있을 때만 다룬다.
- 단순 투자 유치 뉴스는 AI 업계 흐름상 의미가 있을 때만 다룬다.

## 9. 브리핑 구성 우선순위

후보 수집 비율 기준:

```text
X / Threads 실시간 트렌드: 40%
공식 블로그 / 제품 발표: 25%
GeekNews / Hacker News / GitHub: 20%
주요 미디어 / 정책 / 비즈니스: 15%
```

최종 선정은 신뢰도, 중요도, 새로움, 사용자 관심도를 함께 본다.

## 10. v0 제약

v0에서는 아래를 하지 않는다.

- 블로그 자동 게시
- 이메일 자동 발송
- 좋아요 버튼/폼/자동 피드백 수집 구현
- 추천 알고리즘
- 데이터베이스
- 관리자 페이지
- 사용자 계정

v0의 목표는 7일 동안 끝나는 브리핑 실험이다.
