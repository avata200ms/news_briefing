"""뉴스 큐레이션 뷰 및 AJAX API 엔드포인트"""

import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .services.gemini_curator import curate_and_summarize_news
from .services.naver_news import search_naver_news


@ensure_csrf_cookie
def index(request):
    """메인 뉴스 큐레이션 대시보드 뷰"""
    return render(request, "curation/index.html")


@require_POST
def curate_api(request):
    """
    네이버 뉴스 검색 및 Gemini AI 기사 3건 선별/요약 비동기 API

    Request JSON Body:
        {
            "keyword": "검색어",
            "filter_prompt": "필터링 프롬프트",
            "sort": "sim" or "date" (기본값: "sim")
        }
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "잘못된 JSON 요청입니다."}, status=400)

    keyword = data.get("keyword", "").strip()
    filter_prompt = data.get("filter_prompt", "").strip()
    sort = data.get("sort", "sim").strip()

    if not keyword:
        return JsonResponse({"success": False, "error": "검색 키워드를 입력해주세요."}, status=400)

    if not filter_prompt:
        return JsonResponse({"success": False, "error": "필터링 프롬프트를 입력해주세요."}, status=400)

    try:
        # 1. 네이버 뉴스 20건 검색
        articles = search_naver_news(query=keyword, display=20, sort=sort)
        if not articles:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"'{keyword}'에 대한 검색 결과가 존재하지 않습니다.",
                },
                status=404,
            )

        # 2. Gemini AI 3건 엄선 및 심층 요약
        curated_result = curate_and_summarize_news(
            articles=articles,
            filtering_prompt=filter_prompt,
            keyword=keyword,
        )

        return JsonResponse(
            {
                "success": True,
                "keyword": keyword,
                "filter_prompt": filter_prompt,
                "total_articles_count": len(articles),
                "all_articles": articles,
                "overview_comment": curated_result.get("overview_comment", ""),
                "curated_articles": curated_result.get("curated_articles", []),
            }
        )

    except ValueError as ve:
        return JsonResponse({"success": False, "error": str(ve)}, status=400)
    except Exception as e:  # noqa: BLE001
        return JsonResponse(
            {"success": False, "error": f"처리 중 오류가 발생했습니다: {e!s}"},
            status=500,
        )
