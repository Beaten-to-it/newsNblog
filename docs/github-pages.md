# GitHub Pages Publishing

이 프로젝트의 블로그는 GitHub Pages 정적 사이트로 게시한다.

## 현재 게시 URL

- Repository: https://github.com/Beaten-to-it/newsNblog
- GitHub Pages: https://beaten-to-it.github.io/newsNblog/
- Day 1 post: https://beaten-to-it.github.io/newsNblog/posts/2026-06-05.html

검증 결과:

```text
GitHub Pages HTTP status: 200 OK
필수 섹션 확인: 세 줄 요약, AI UseCase
```

## 현재 생성된 파일

- 사이트 빌더: `scripts/build_site.py`
- GitHub Pages 워크플로: `.github/workflows/pages.yml`
- 로컬 사이트 출력: `site/`
- 블로그 원본: `dist/blog/YYYY-MM-DD.md`

## 로컬 빌드

```bash
cd /c/Project/newsNblog
python scripts/render_briefing.py 2026-06-05
python scripts/build_site.py
```

결과:

```text
site/index.html
site/posts/2026-06-05.html
site/assets/style.css
```

## GitHub Pages 설정 방식

이 프로젝트는 GitHub Actions로 `site/` 폴더를 Pages artifact로 배포한다.
GitHub 저장소에서 아래 설정이 필요하다.

```text
Settings → Pages → Build and deployment → Source: GitHub Actions
```

그 후 `main` 브랜치에 push하면 `.github/workflows/pages.yml`이 실행되고 Pages에 배포된다.

## 보안 주의

OAuth client secret JSON은 절대 GitHub에 올리면 안 된다.
현재 `.gitignore`에 아래 패턴을 추가했다.

```text
client_secret*.json
google_client_secret.json
google_token.json
```

작업 전 반드시 확인:

```bash
git status --short
```

`client_secret_...json` 파일이 보이면 안 된다.

## 아직 필요한 것

이 환경에는 `gh` CLI가 설치되어 있지 않고, Git remote도 아직 없다.
따라서 원격 저장소 생성/푸시는 아래 중 하나로 진행해야 한다.

1. 사용자가 GitHub에서 직접 저장소 생성 후 remote URL 제공
2. `gh` CLI 설치/인증 후 여기서 저장소 생성
3. HTTPS/SSH remote를 사용자가 직접 설정

## 추천 저장소 설정

- 저장소명: `newsNblog` 또는 `ai-morning-radar`
- 공개 여부: 블로그 공개 목적이면 Public, 실험 중이면 Private + Pages 가능 여부 확인
- 기본 브랜치: `main`
- Pages Source: GitHub Actions
