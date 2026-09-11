"""뉴스 큐레이션 뷰, 히스토리 뷰 및 AJAX API 엔드포인트"""

import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST

from .models import SavedArticleSummary, SavedBriefing
from .services.gemini_curator import curate_and_summarize_news
from .services.naver_news import search_naver_news


@ensure_csrf_cookie
def index(request):
    """메인 뉴스 큐레이션 대시보드 뷰"""
    return render(request, "curation/index.html")


@csrf_exempt
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


@csrf_exempt
@require_POST
def save_briefing_api(request):
    """
    요약 결과 저장 API

    Request JSON Body:
        {
            "keyword": "검색어",
            "filter_prompt": "필터링 조건",
            "overview_comment": "총평",
            "curated_articles": [
                {
                    "title": "제목",
                    "url": "링크",
                    "pub_date": "일시",
                    "selection_reason": "선정 이유",
                    "summary_bullets": ["요약1", "요약2", "요약3"],
                    "insight": "인사이트",
                    "tags": ["태그1", "태그2"]
                }, ...
            ]
        }
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "잘못된 JSON 형식입니다."}, status=400)

    keyword = data.get("keyword", "").strip()
    filter_prompt = data.get("filter_prompt", "").strip()
    overview_comment = data.get("overview_comment", "").strip()
    curated_articles = data.get("curated_articles", [])

    if not keyword or not curated_articles:
        return JsonResponse(
            {"success": False, "error": "저장할 뉴스 브리핑 데이터가 부족합니다."},
            status=400,
        )

    try:
        with transaction.atomic():
            briefing = SavedBriefing.objects.create(
                keyword=keyword,
                filter_prompt=filter_prompt,
                overview_comment=overview_comment,
            )

            article_objects = [
                SavedArticleSummary(
                    briefing=briefing,
                    title=art.get("title", ""),
                    url=art.get("url", ""),
                    pub_date=art.get("pub_date", ""),
                    selection_reason=art.get("selection_reason", ""),
                    summary_bullets=art.get("summary_bullets", []),
                    insight=art.get("insight", ""),
                    tags=art.get("tags", []),
                )
                for art in curated_articles
            ]

            SavedArticleSummary.objects.bulk_create(article_objects)

        return JsonResponse(
            {
                "success": True,
                "message": "뉴스 브리핑 및 요약 결과가 성공적으로 저장되었습니다.",
                "briefing_id": briefing.id,
                "created_at": briefing.created_at.strftime("%Y-%m-%d %H:%M"),
            }
        )

    except Exception as e:  # noqa: BLE001
        return JsonResponse(
            {"success": False, "error": f"저장 중 오류가 발생했습니다: {e!s}"},
            status=500,
        )


@ensure_csrf_cookie
@require_http_methods(["GET"])
def history_view(request):
    """
    '나의 요약 히스토리' 페이지 뷰
    저장된 브리핑 및 기사 요약 목록을 조회합니다.
    """
    query = request.GET.get("q", "").strip()
    briefings_qs = SavedBriefing.objects.prefetch_related("articles").all()

    if query:
        briefings_qs = briefings_qs.filter(keyword__icontains=query)

    return render(
        request,
        "curation/history.html",
        {
            "briefings": briefings_qs,
            "query": query,
            "total_count": briefings_qs.count(),
        },
    )


@csrf_exempt
@require_POST
def delete_briefing_api(request, pk):
    """저장된 브리핑 및 연관 기사 요약 삭제 API"""
    briefing = get_object_or_404(SavedBriefing, pk=pk)
    keyword = briefing.keyword
    briefing.delete()
    return JsonResponse(
        {
            "success": True,
            "message": f"'{keyword}' 브리핑 히스토리가 삭제되었습니다.",
        }
    )
