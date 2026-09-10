"""프로젝트 메인 실행 진입점 (uv 개발 환경 및 시스템 상태 점검용)"""

import os
import sys

from dotenv import load_dotenv

# Windows 콘솔 utf-8 인코딩 지원
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()


def main() -> None:
    print("=" * 65)
    print("📰 [News Briefing] AI 뉴스 큐레이션 개발 환경 검증")
    print("=" * 65)
    print(f"📌 Python 버전: {sys.version.split()[0]}")
    print(f"📌 가상환경 경로: {sys.prefix}")
    print("📌 실행 모드: uv run 가상환경 연동")

    # Django 및 Gemini API 라이브러리 로드 테스트
    try:
        import django
        from google import genai  # noqa: F401

        print(f"✅ Django 프레임워크: v{django.__version__}")
        print("✅ Google GenAI SDK (Gemini API) 로드 성공")
    except ImportError as e:
        print(f"⚠️ 패키지 로드 오류: {e}")

    # 환경 변수 체크
    gemini_key = os.getenv("GEMINI_API_KEY")
    naver_id = os.getenv("NAVER_CLIENT_ID")
    naver_secret = os.getenv("NAVER_CLIENT_SECRET")

    print("-" * 65)
    print("🔑 환경 변수(.env) 설정 상태:")
    print(f"   - GEMINI_API_KEY: {'[설정 완료]' if gemini_key else '[미설정] (.env 파일에 설정 필요)'}")
    print(f"   - NAVER_CLIENT_ID: {'[설정 완료]' if naver_id else '[미설정] (.env 파일에 설정 필요)'}")
    print(f"   - NAVER_CLIENT_SECRET: {'[설정 완료]' if naver_secret else '[미설정] (.env 파일에 설정 필요)'}")
    print("-" * 65)
    print("💡 웹 대시보드 서버 실행 명령어:")
    print("   uv run python manage.py runserver")
    print("=" * 65)


if __name__ == "__main__":
    main()
