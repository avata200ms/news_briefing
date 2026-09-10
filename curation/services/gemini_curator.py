"""Google Gemini API 기반 뉴스 기사 선별(큐레이션) 및 심층 요약 서비스"""

import json
import os
from typing import Any

from django.conf import settings
from google import genai
from google.genai import types


def curate_and_summarize_news(
    articles: list[dict[str, Any]],
    filtering_prompt: str,
    keyword: str
) -> dict[str, Any]:
    """
    네이버 뉴스 기사 목록(20개) 중에서 사용자의 필터링 프롬프트에 가장 적합한
    기사 3개를 선정하고, 각 기사에 대한 핵심 요약 및 인사이트를 생성합니다.

    Args:
        articles (list[dict[str, Any]]): 네이버 검색으로 수집된 20개 기사 리스트
        filtering_prompt (str): 사용자가 지정한 필터링 기준 프롬프트
        keyword (str): 원래 검색 키워드

    Returns:
        dict[str, Any]: {
            "curated_articles": [
                {
                    "original_id": 1,
                    "title": "...",
                    "url": "...",
                    "pub_date": "...",
                    "selection_reason": "선정 이유",
                    "summary_bullets": ["요약1", "요약2", "요약3"],
                    "insight": "비즈니스 시사점 및 인사이트",
                    "tags": ["태그1", "태그2", "태그3"]
                }, ...
            ],
            "overview_comment": "이번 뉴스 큐레이션 총평"
        }
    """
    api_key = getattr(settings, "GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("Google Gemini API 키가 설정되지 않았습니다. .env 파일에 GEMINI_API_KEY를 설정해주세요.")

    if not articles:
        raise ValueError("분석할 기사 목록이 비어 있습니다.")

    client = genai.Client(api_key=api_key)

    # 20개 기사 목록 포맷팅
    article_list_text = []
    for art in articles:
        article_list_text.append(
            f"[{art['id']}] 제목: {art['title']}\n    요약/본문일부: {art['description']}\n    발행일: {art['pub_date']}"
        )
    formatted_articles = "\n\n".join(article_list_text)

    prompt = f"""당신은 전문 수석 비즈니스 저널리스트이자 AI 뉴스 큐레이터입니다.
사용자가 검색한 키워드: "{keyword}"
사용자가 요청한 맞춤 필터링 기준: "{filtering_prompt}"

아래는 네이버 뉴스 검색을 통해 수집된 기사 20개의 목록입니다.

[기사 목록]
{formatted_articles}

---
[요청 작업]
1. 위 20개 기사 중에서 사용자의 "맞춤 필터링 기준"에 가장 완벽하게 부합하고 가치 있는 기사 딱 3개만 엄선하세요.
2. 엄선한 3개 기사 각각에 대해 다음 정보를 작성하세요:
   - original_id: 선택한 기사의 [번호] (정수형)
   - selection_reason: 사용자의 필터링 기준에 맞춰 이 기사를 선정한 명확한 이유 (1~2문장)
   - summary_bullets: 기사의 핵심 내용 3줄 요약 (문자열 배열, 정확히 3개 항목)
   - insight: 이 뉴스가 시장/비즈니스/실무자에게 주는 핵심 시사점 및 시각 (2~3문장)
   - tags: 핵심 키워드 태그 (3~4개 단어 배열)
3. overview_comment: 이번 큐레이션 결과에 대한 1줄 브리핑 총평.

반드시 다음 JSON 스키마 형식에 맞춰 순수 JSON으로만 응답하세요:
{{
  "overview_comment": "이번 브리핑 총평 문장",
  "curated_articles": [
    {{
      "original_id": 1,
      "selection_reason": "...",
      "summary_bullets": [
        "핵심 요약 1",
        "핵심 요약 2",
        "핵심 요약 3"
      ],
      "insight": "...",
      "tags": ["태그1", "태그2", "태그3"]
    }}
  ]
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )

        response_text = response.text.strip()
        parsed_data = json.loads(response_text)

        # 원본 기사 메타데이터(URL, 제목, 발행일 등)와 AI 요약 데이터 매핑
        article_map = {art["id"]: art for art in articles}
        curated_list = []

        for item in parsed_data.get("curated_articles", []):
            orig_id = item.get("original_id")
            orig_art = article_map.get(orig_id, {})

            curated_list.append({
                "original_id": orig_id,
                "title": orig_art.get("title", f"기사 #{orig_id}"),
                "url": orig_art.get("url", ""),
                "naver_url": orig_art.get("naver_url", ""),
                "pub_date": orig_art.get("pub_date", ""),
                "selection_reason": item.get("selection_reason", ""),
                "summary_bullets": item.get("summary_bullets", []),
                "insight": item.get("insight", ""),
                "tags": item.get("tags", []),
            })

        return {
            "overview_comment": parsed_data.get("overview_comment", "AI가 엄선한 3대 핵심 뉴스 브리핑입니다."),
            "curated_articles": curated_list,
        }

    except Exception as e:
        raise RuntimeError(f"Gemini API 기사 큐레이션 및 요약 생성 중 오류 발생: {e}") from e
