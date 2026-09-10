---
trigger: always_on
---

# 📌 Workspace Rules: News Briefing Project

## 1. 🚀 파이썬 실행 및 가상환경 원칙 (CRITICAL)
- **모든 파이썬 스크립트, 도구, 서버 실행 시 반드시 `uv run` 접두사를 사용합니다.**
  - 예: `uv run python main.py`
  - 예: `uv run python manage.py <command>`
  - 예: `uv run ruff check .`
  - 시스템 전역 `python` 명령어를 단독으로 직접 호출하지 않고, 반드시 프로젝트의 `uv` 가상환경(`.venv`)을 통하도록 합니다.
- 새 패키지 추가 시 `uv add <package>` (개발용: `uv add --dev <package>`)를 사용합니다.

## 2. 🛠️ 기술 스택 및 아키텍처
- **Python 버전**: 3.12 (가상환경: `.venv`)
- **Web Framework**: Django 6.x
- **AI / LLM SDK**: Google GenAI SDK (`google-genai` / `GEMINI_API_KEY`)
- **환경 변수 관리**: `python-dotenv` 및 `.env` 파일 사용 (API 키 및 SECRET_KEY 등 절대 하드코딩 금지)
- **코드 품질**: Ruff (`uv run ruff check --fix .`)

## 3. 🌐 Windows 환경 호환성
- Windows 콘솔 출력 시 cp949 인코딩 충돌 방지를 위해 `sys.stdout.reconfigure(encoding="utf-8")` 안전장치를 엔트리포인트에 적용합니다.
- 파일 경로는 Windows 및 크로스 플랫폼 호환을 위해 `pathlib.Path` 또는 `os.path`를 사용합니다.

## 4. 🤖 AI 협업 및 커뮤니케이션
- 응답 및 설명은 항상 한국어로 작성합니다.
- 오류 발생 시 자율적으로 원인을 분석하고 해결 방안을 적용한 후 보고합니다.
