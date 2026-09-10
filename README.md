# 📰 News Briefing (AI 뉴스 브리핑 시스템)

Python 3.12, Django, Google Gemini API를 활용한 뉴스 브리핑 및 콘텐츠 자동화 프로젝트입니다.

---

## 🚀 빠른 시작

### 1. 환경 변수 설정
`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 Google Gemini API 키를 입력합니다:
```bash
cp .env.example .env
```

### 2. 가상환경 실행 검증
모든 Python 실행은 `uv run` 명령어를 사용합니다:
```bash
uv run python main.py
```

### 3. 코드 품질 검사 (Ruff)
```bash
uv run ruff check .
```
