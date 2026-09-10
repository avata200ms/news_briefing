"""프로젝트 메인 실행 진입점 (uv 개발 환경 검증용)"""
import os
import sys

from dotenv import load_dotenv

# Windows 콘솔 utf-8 인코딩 지원
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()


def main() -> None:
    print("=" * 60)
    print("🚀 [News Briefing] uv 기반 파이썬 개발 환경이 정상 구동되었습니다!")
    print(f"📌 Python 버전: {sys.version.split()[0]}")
    print(f"📌 가상환경 경로: {sys.prefix}")
    print("📌 실행 모드: uv run 가상환경 연동")

    # Django 및 Gemini API 라이브러리 로드 테스트
    try:
        import django
        from google import genai  # noqa: F401

        print(f"✅ Django 버전: {django.__version__}")
        print("✅ Google GenAI SDK (Gemini API) 로드 성공")
    except ImportError as e:
        print(f"⚠️ 패키지 로드 오류: {e}")

    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print("🔑 GEMINI_API_KEY 감지됨 (설정 완료)")
    else:
        print("💡 GEMINI_API_KEY 미설정 (.env 파일에 설정 필요)")

    print("=" * 60)


if __name__ == "__main__":
    main()
