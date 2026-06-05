# Kanban Workflow

newsNblog 작업은 Hermes Kanban board `newsnblog`에서 추적한다.

## Board

```bash
hermes kanban --board newsnblog list
```

## 현재 원칙

- 작업이 깨지거나 중단되어도 이어갈 수 있도록 Kanban 카드로 관리한다.
- 사용자 입력이 필요한 단계는 `blocked` 상태로 둔다.
- 선행 작업이 끝나야 하는 작업은 parent dependency로 묶는다.
- v0에서는 앱/DB/자동 게시 구현보다 브리핑 실험 운영을 우선한다.

## 초기 카드

- `t_615657a2` — `collect: newsNblog briefing preferences`
  - 상태: blocked
  - 이유: 사용자 선호 데이터 필요
- `t_99a75e0c` — `setup: persist user preferences for v0`
  - parent: `t_615657a2`
- `t_b6bc3787` — `briefing: produce day 1 AI Morning Radar`
  - parent: `t_615657a2`
- `t_0e6f552a` — `feedback: record day 1 response`
  - parent: `t_615657a2`

## 자주 쓰는 명령

```bash
# 보드 보기
hermes kanban --board newsnblog list

# 카드 상세 보기
hermes kanban --board newsnblog show <task_id>

# 카드 이벤트 따라가기
hermes kanban --board newsnblog tail <task_id>

# 사용자 입력이 해결된 카드 unblock
hermes kanban --board newsnblog unblock <task_id>

# 작업 완료 처리
hermes kanban --board newsnblog complete <task_id> "summary"
```

## 다음 액션

사용자가 브리핑 선호 데이터를 제공하거나 기본값 사용을 승인하면:

1. `docs/user-preferences.md`를 작성한다.
2. `t_615657a2`를 완료 또는 unblock한다.
3. Day 1 briefing 카드를 진행한다.
