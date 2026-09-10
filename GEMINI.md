# 📰 News Briefing 프로젝트 개발 가이드

이 프로젝트는 **Python 3.12**, **Django**, 그리고 **Google Gemini API (`google-genai`)**를 기반으로 뉴스 브리핑 및 콘텐츠 자동화를 구현하는 웹 애플리케이션 프로젝트입니다.

---

## ⚡ 핵심 실행 원칙 (Critical Rules)

> [!IMPORTANT]
> **모든 Python 스크립트와 명령어 실행 시 반드시 `uv run`을 사용합니다.**
> - 메인 테스트 실행: `uv run python main.py`
> - Django 개발 서버 실행: `uv run python manage.py runserver`
> - Django 마이그레이션: `uv run python manage.py migrate`
> - 코드 린트 및 서식: `uv run ruff check --fix .`
> - 패키지 설치: `uv add <package>` (개발용: `uv add --dev <package>`)

---

## 🛠️ 기술 스택 (Tech Stack)

| 구분 | 기술 / 도구 | 용도 |
| :--- | :--- | :--- |
| **Language** | Python 3.12 (uv) | 핵심 프로그래밍 언어 및 가상환경 |
| **Web Framework** | Django | 웹 백엔드 및 관리자 대시보드/API |
| **AI / LLM** | Google Gemini API (`google-genai`) | 뉴스 분석, 요약 및 브리핑 생성 |
| **Env & Config** | `python-dotenv` | 환경 변수(`.env`) 안전 관리 |
| **Linter & Formatter** | Ruff | 코드 품질 유지 및 자동 정렬 |

---

## 📁 주요 디렉터리 및 파일 구조

```
news_Briefing/
├── .agents/
│   └── rules/
│       └── workspace-rules.md     # AI 워크스페이스 실행 규칙
├── .venv/                         # uv 가상환경 (Python 3.12)
├── .vscode/
│   ├── settings.json              # VS Code 인터프리터 & Ruff 연동
│   └── tasks.json                 # 원클릭 uv 실행 태스크
├── src/
│   └── news_briefing/             # 소스코드 패키지
├── .env.example                   # 환경 변수 설정 템플릿
├── .gitignore                     # Git 무시 목록
├── .python-version                # Python 3.12 버전 고정
├── GEMINI.md                      # 프로젝트 가이드
├── main.py                        # 루트 실행 엔트리포인트
├── pyproject.toml                 # uv 프로젝트 의존성 명세
└── README.md                      # 프로젝트 소개
```

---

## 🚀 빠른 시작 (Quick Start)

1. **환경 변수 세팅**:
   - `.env.example` 파일을 복사하여 `.env` 생성 후 API 키 입력
   ```bash
   cp .env.example .env
   ```
2. **개발 환경 검증**:
   ```bash
   uv run python main.py
   ```
3. **코드 린트 검사**:
   ```bash
   uv run ruff check .
   ```
