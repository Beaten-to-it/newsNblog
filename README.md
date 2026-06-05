# newsNblog

AI 뉴스 브리핑 + 블로그 아카이브 실험 프로젝트입니다.

이 프로젝트의 첫 목표는 제품을 완성하는 것이 아니라, **7일 동안 끝나는 실험**으로 매일 아침 받아볼 만한 AI 브리핑 포맷을 찾는 것입니다.

## v0 원칙

- 기간: 7일
- 목표: 매일 1회 AI 브리핑을 만들고, 실제로 읽을 가치가 있는지 확인
- X/Threads: 처음부터 핵심 소스로 포함하고 비중을 높게 둠
- GeekNews: 처음부터 국내 개발자 큐레이션 소스로 포함
- 중복 방지: 한 번 낸 뉴스는 `data/published_items.csv`에 기록하고 재발행하지 않음
- 전달: 우선 Markdown 파일 + Hermes 대화방 응답 기준
- 블로그: 자동 게시하지 않고 Markdown 아카이브로만 저장
- 피드백: 좋아요/버튼/DB 없이, 사용자가 대화에서 주는 피드백만 수동 기록
- 자동화: 검증 후 추가

## 디렉터리

```text
briefings/              # 매일 생성되는 브리핑 Markdown
sources/                # 수집할 뉴스 소스 목록과 후보 링크
templates/              # 브리핑 템플릿
data/feedback.csv       # 일별 피드백 기록
data/published_items.csv # 발행 이력 및 중복 방지 기록
docs/                   # 실험 설계/의사결정 문서
.hermes/plans/          # Hermes 작업 계획
```

## 시작 방법

1. `docs/v0-experiment.md`를 읽고 7일 실험 범위를 확인합니다.
2. `docs/user-preferences.md`를 읽고 사용자의 기본 선호값을 확인합니다.
3. 브리핑 작성 전 `data/published_items.csv`를 확인해서 중복 뉴스를 제외합니다.
4. `sources/source-candidates.md` 기준으로 X/Threads/GeekNews/공식 블로그/미디어를 확인합니다.
5. 매일 `templates/daily-briefing.md`를 복사해서 `briefings/YYYY-MM-DD.md`를 만듭니다.
6. 발행한 항목을 `data/published_items.csv`에 추가합니다.
7. 브리핑을 읽은 뒤 `data/feedback.csv`에 피드백을 기록합니다.
8. 7회차가 끝나면 `docs/v0-retrospective.md`에 결론을 정리합니다.

## v0 완료 조건

- [ ] 7개의 일일 브리핑 작성
- [ ] 각 브리핑에 대한 피드백 기록
- [ ] 발행한 주요 뉴스가 `data/published_items.csv`에 기록됨
- [ ] 중복 뉴스가 체감상 줄었는지 판단
- [ ] X/Threads 비중이 적절했는지 판단
- [ ] GeekNews 포함이 유용했는지 판단
- [ ] 유지할 섹션 / 버릴 섹션 / 추가할 섹션 결정
- [ ] v1에서 자동화할 항목 1~3개만 선정
