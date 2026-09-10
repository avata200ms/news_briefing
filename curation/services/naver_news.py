"""네이버 뉴스 검색 API 연동 서비스 모듈 (NCP NAVER API HUB 및 레거시 Developers API 동시 지원)"""

import email.utils
import html
import os
from pathlib import Path
import re
from typing import Any
import requests
from django.conf import settings
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def clean_html(raw_html: str) -> str:
    """HTML 태그 제거 및 특수문자 디코딩"""
    if not raw_html:
        return ""
    clean_text = re.sub(r"<[^>]+>", "", raw_html)
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


def get_naver_credentials() -> tuple[str, str]:
    """최신 .env 파일에서 네이버 인증키 로드"""
    load_dotenv(BASE_DIR / ".env", override=True)
    client_id = (
        os.getenv("NAVER_CLIENT_ID", "")
        or getattr(settings, "NAVER_CLIENT_ID", "")
    ).strip()
    client_secret = (
        os.getenv("NAVER_CLIENT_SECRET", "")
        or getattr(settings, "NAVER_CLIENT_SECRET", "")
    ).strip()
    return client_id, client_secret


def search_naver_news(
    query: str,
    display: int = 20,
    sort: str = "sim"
) -> list[dict[str, Any]]:
    """
    네이버 뉴스 검색 API를 호출하여 정제된 기사 목록을 반환합니다.
    1) 네이버 클라우드 플랫폼(NCP) NAVER API HUB (https://naverapihub.apigw.ntruss.com/search/v1/news)
    2) 네이버 개발자 센터 레거시 (https://openapi.naver.com/v1/search/news.json)
    두 가지 엔드포인트를 순차 시도합니다.

    Args:
        query (str): 검색 키워드
        display (int): 검색 건수 (기본값: 20)
        sort (str): 정렬 방식 ('sim': 정확도순, 'date': 최신순)

    Returns:
        list[dict[str, Any]]: 정제된 기사 데이터 리스트
    """
    client_id, client_secret = get_naver_credentials()

    if not client_id or not client_secret:
        raise ValueError(
            "네이버 API 인증 정보가 설정되지 않았습니다. .env 파일에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정해주세요."
        )

    if not query or not query.strip():
        raise ValueError("검색 키워드를 입력해주세요.")

    params = {
        "query": query.strip(),
        "display": min(max(display, 1), 100),
        "start": 1,
        "sort": sort,
    }

    # 시도할 엔드포인트 및 헤더 목록
    endpoints = [
        # 1. 네이버 클라우드 플랫폼(NCP) NAVER API HUB
        {
            "name": "NAVER Cloud Platform (NAVER API HUB)",
            "url": "https://naverapihub.apigw.ntruss.com/search/v1/news",
            "headers": {
                "X-NCP-APIGW-API-KEY-ID": client_id,
                "X-NCP-APIGW-API-KEY": client_secret,
                "User-Agent": "NewsBriefingApp/1.0",
            },
        },
        # 2. 네이버 개발자 센터 (Developers Open API)
        {
            "name": "Naver Developers Open API",
            "url": "https://openapi.naver.com/v1/search/news.json",
            "headers": {
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
                "User-Agent": "NewsBriefingApp/1.0",
            },
        },
    ]

    last_error = ""

    for ep in endpoints:
        try:
            response = requests.get(ep["url"], headers=ep["headers"], params=params, timeout=10)

            if response.status_code == 200:
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
            else:
                last_error = f"{ep['name']} 실패 (HTTP {response.status_code}): {response.text}"

        except requests.exceptions.RequestException as req_err:
            last_error = f"{ep['name']} 연결 오류: {req_err}"

    # 모든 엔드포인트 실패 시
    raise RuntimeError(f"네이버 뉴스 API 호출에 실패했습니다.\n상세: {last_error}")
