# Source Candidates

v0에서는 완전 자동 크롤러를 만들지 않지만, **X/Threads/GeekNews는 처음부터 핵심 소스**로 포함합니다. 매일 브리핑 작성 시 아래 소스 후보를 기준으로 검색/확인합니다.

## 우선순위 1 — X / Threads 실시간 트렌드

X와 Threads는 공식 발표보다 빠르게 정보가 올라오는 경우가 많으므로 v0부터 높은 비중으로 다룹니다.

### X 검색 키워드

- `site:x.com AI OpenAI Anthropic Google DeepMind OR Gemini`
- `site:x.com "AI agents" OR "coding agents" OR "agentic"`
- `site:x.com Claude OR ChatGPT OR GPT OR Gemini OR Grok OR Llama`
- `site:x.com Cursor OR Windsurf OR Devin OR "Claude Code" OR Codex`
- `site:x.com "open source" LLM OR Qwen OR DeepSeek OR Mistral`
- `site:x.com "AI benchmark" OR "SWE-bench" OR "Humanity's Last Exam"`

### Threads 검색 키워드

- `site:threads.net AI OpenAI Claude Gemini`
- `site:threads.net "AI tools" OR "AI workflow"`
- `site:threads.net ChatGPT OR Claude OR Gemini OR Grok`
- `site:threads.net "AI agents" OR "coding agents"`
- `site:threads.net "AI image" OR "AI video" OR "AI app"`

### X/Threads 수집 규칙

- 공식 발표 전 루머는 `신뢰도: 낮음`으로 표시
- 유명 연구자/개발자/창업자/기자 발언은 `신뢰도: 중간` 이상 후보
- 스크린샷만 있는 주장은 단독 근거로 Top 5에 넣지 않음
- 동일 이슈가 X/Threads 양쪽에서 반복되면 하나로 묶고 양쪽 반응을 같이 요약
- 빠르게 확산 중인 이슈라도 출처가 불분명하면 `트렌드 레이더`에만 배치

## 우선순위 2 — GeekNews / 국내 개발자 큐레이션

- GeekNews — https://news.hada.io/
- GeekNews RSS — https://feeds.feedburner.com/geeknews-feed

GeekNews는 한국어 개발자 관점에서 중요한 소스입니다. AI 관련 글뿐 아니라 개발자 도구, 스타트업, 오픈소스, 생산성 도구 중 AI 브리핑 독자에게 의미 있는 항목을 포함합니다.

### GeekNews 수집 규칙

- AI/LLM/에이전트/개발자 도구/오픈소스/스타트업 관련 항목 우선
- GeekNews에 올라온 해외 원문이 이미 전날 다뤄졌다면 중복 제외
- GeekNews 댓글/커뮤니티 맥락이 의미 있으면 `왜 중요한가`에 한국 개발자 관점을 추가

## 우선순위 3 — 공식 블로그 / 릴리스

- OpenAI Blog — https://openai.com/blog/
- Anthropic News — https://www.anthropic.com/news
- Google DeepMind Blog — https://deepmind.google/discover/blog/
- Google AI Blog — https://blog.google/technology/ai/
- Meta AI Blog — https://ai.meta.com/blog/
- Mistral AI News — https://mistral.ai/news/
- Hugging Face Blog — https://huggingface.co/blog

## 우선순위 4 — 미디어 / 뉴스

- The Verge AI — https://www.theverge.com/ai-artificial-intelligence
- TechCrunch AI — https://techcrunch.com/category/artificial-intelligence/
- VentureBeat AI — https://venturebeat.com/category/ai/
- MIT Technology Review AI — https://www.technologyreview.com/topic/artificial-intelligence/

## 우선순위 5 — 개발자 / 오픈소스 / 논문

- GitHub Trending — https://github.com/trending
- Hacker News — https://news.ycombinator.com/
- arXiv cs.AI — https://arxiv.org/list/cs.AI/recent
- arXiv cs.CL — https://arxiv.org/list/cs.CL/recent
- arXiv cs.LG — https://arxiv.org/list/cs.LG/recent

## 일일 후보 수집 비율

```text
X / Threads: 40%
공식 블로그 / 제품 발표: 25%
GeekNews / Hacker News / GitHub: 20%
미디어 / 비즈니스 / 정책: 15%
```

## v0 수집 규칙

- 공식 발표는 Top 5 후보에 우선 포함
- X/Threads 이슈는 높은 비중으로 수집하되, 신뢰도 낮은 루머는 Top 5가 아니라 트렌드 섹션에 배치
- GeekNews는 국내 개발자 관점의 필터로 사용
- 신뢰도 낮은 내용은 반드시 `공식 확인 없음` 표시
- 같은 이슈가 여러 출처에서 반복되면 하나로 묶기
- 발행 전 `data/published_items.csv`를 확인해 이미 낸 뉴스는 제외
