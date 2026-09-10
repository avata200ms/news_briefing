"""네이버 뉴스 검색 Open API 연동 서비스 모듈"""

import email.utils
import html
import os
import re
from typing import Any

import requests
from django.conf import settings


def clean_html(raw_html: str) -> str:
    """HTML 태그 제거 및 특수문자 디코딩"""
    if not raw_html:
        return ""
    # HTML 태그 제거 (<b>, </b> 등)
    clean_text = re.sub(r"<[^>]+>", "", raw_html)
    # HTML 엔티티 디코딩 (&quot;, &amp;, &lt;, &gt; 등)
    clean_text = html.unescape(clean_text)
    return clean_text.strip()


def format_pubdate(pubdate_str: str) -> str:
    """네이버 pubDate 문자열(RFC 2822)을 가독성 높은 날짜 형식으로 변환"""
    if not pubdate_str:
        return ""
    try:
        dt = email.utils.parsedate_to_datetime(pubdate_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return pubdate_str


def search_naver_news(
    query: str,
    display: int = 20,
    sort: str = "sim"
) -> list[dict[str, Any]]:
    """
    네이버 뉴스 검색 API를 호출하여 정제된 기사 목록 20개를 반환합니다.

    Args:
        query (str): 검색할 키워드
        display (int): 검색 건수 (기본값: 20)
        sort (str): 정렬 방식 ('sim': 정확도순, 'date': 최신순)

    Returns:
        list[dict[str, Any]]: 정제된 기사 데이터 리스트
    """
    client_id = getattr(settings, "NAVER_CLIENT_ID", "") or os.getenv("NAVER_CLIENT_ID", "")
    client_secret = getattr(settings, "NAVER_CLIENT_SECRET", "") or os.getenv("NAVER_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        raise ValueError(
            "네이버 API 인증 정보가 설정되지 않았습니다. .env 파일에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정해주세요."
        )

    if not query or not query.strip():
        raise ValueError("검색 키워드를 입력해주세요.")

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id.strip(),
        "X-Naver-Client-Secret": client_secret.strip(),
        "User-Agent": "NewsBriefingApp/1.0",
    }
    params = {
        "query": query.strip(),
        "display": min(max(display, 1), 100),
        "start": 1,
        "sort": sort,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 401 or response.status_code == 403:
            raise ValueError("네이버 API 인증에 실패했습니다. Client ID 및 Client Secret을 확인해주세요.")
        elif response.status_code != 200:
            raise RuntimeError(f"네이버 검색 API 호출 실패 (HTTP {response.status_code}): {response.text}")

        data = response.json()
        raw_items = data.get("items", [])

        articles = []
        for idx, item in enumerate(raw_items, start=1):
            title = clean_html(item.get("title", ""))
            description = clean_html(item.get("description", ""))
            link = item.get("originallink") or item.get("link", "")
            naver_link = item.get("link", "")
            pub_date = format_pubdate(item.get("pubDate", ""))

            articles.append({
                "id": idx,
                "title": title,
                "description": description,
                "url": link,
                "naver_url": naver_link,
                "pub_date": pub_date,
            })

        return articles

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"네이버 API 네트워크 요청 중 오류가 발생했습니다: {e}")
