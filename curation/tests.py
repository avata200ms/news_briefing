"""Curation 앱 단위 및 통합 테스트"""

import json
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase
from django.urls import reverse

from curation.models import SavedArticleSummary, SavedBriefing
from curation.services.gemini_curator import curate_and_summarize_news
from curation.services.naver_news import clean_html, format_pubdate, search_naver_news


class CurationUnitTests(TestCase):
    def test_clean_html(self):
        raw = "<b>네이버</b> 뉴스 &quot;AI&quot; &amp; 클라우드 &lt;최신&gt;"
        expected = '네이버 뉴스 "AI" & 클라우드 <최신>'
        self.assertEqual(clean_html(raw), expected)

    def test_format_pubdate(self):
        raw_date = "Wed, 10 Sep 2026 09:30:00 +0900"
        formatted = format_pubdate(raw_date)
        self.assertEqual(formatted, "2026-09-10 09:30")

    @patch("curation.services.naver_news.requests.get")
    def test_search_naver_news_mock(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "title": "<b>인공지능</b> 신기술 발표",
                    "originallink": "https://news.example.com/1",
                    "link": "https://naver.news/1",
                    "description": "최신 <b>AI</b> 트렌드 소개",
                    "pubDate": "Wed, 10 Sep 2026 10:00:00 +0900",
                }
            ]
        }
        mock_get.return_value = mock_response

        # with mock settings
        with self.settings(NAVER_CLIENT_ID="test_id", NAVER_CLIENT_SECRET="test_secret"):
            articles = search_naver_news(query="인공지능", display=1)
            self.assertEqual(len(articles), 1)
            self.assertEqual(articles[0]["title"], "인공지능 신기술 발표")
            self.assertEqual(articles[0]["description"], "최신 AI 트렌드 소개")

    @patch("google.genai.Client")
    def test_gemini_curate_mock(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_model_response = MagicMock()
        mock_model_response.text = """
        {
            "overview_comment": "비즈니스 혁신 중심의 AI 뉴스 브리핑입니다.",
            "curated_articles": [
                {
                    "original_id": 1,
                    "selection_reason": "실제 매출 발생 B2B 기업 사례를 구체적으로 다룸",
                    "summary_bullets": [
                        "기사 핵심 요약 첫 번째 줄",
                        "기사 핵심 요약 두 번째 줄",
                        "기사 핵심 요약 세 번째 줄"
                    ],
                    "insight": "스타트업의 수익화 모델 확립에 중요한 시사점 제공",
                    "tags": ["AI수익화", "B2BSaaS", "스타트업"]
                }
            ]
        }
        """
        mock_client.models.generate_content.return_value = mock_model_response

        articles = [
            {
                "id": 1,
                "title": "AI 기업 수익화 성공",
                "description": "B2B SaaS 모델로 흑자 전환",
                "url": "https://news.example.com/1",
                "naver_url": "https://naver.news/1",
                "pub_date": "2026-09-10 10:00",
            }
        ]

        with self.settings(GEMINI_API_KEY="test_gemini_key"):
            result = curate_and_summarize_news(
                articles=articles,
                filtering_prompt="수익화 사례 위주로 골라줘",
                keyword="AI 기업",
            )
            self.assertEqual(result["overview_comment"], "비즈니스 혁신 중심의 AI 뉴스 브리핑입니다.")
            self.assertEqual(len(result["curated_articles"]), 1)
            self.assertEqual(result["curated_articles"][0]["title"], "AI 기업 수익화 성공")
            self.assertEqual(len(result["curated_articles"][0]["summary_bullets"]), 3)


class CurationViewAndModelTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index_page(self):
        response = self.client.get(reverse("curation:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "News Briefing")
        self.assertContains(response, "검색 키워드")
        self.assertContains(response, "결과 저장하기")

    def test_api_validation_error(self):
        # Empty keyword
        response = self.client.post(
            reverse("curation:curate_api"),
            data=json.dumps({"keyword": "", "filter_prompt": "테스트"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])

    def test_save_briefing_api(self):
        payload = {
            "keyword": "생성형 AI",
            "filter_prompt": "수익화 모델 중심",
            "overview_comment": "수익화 중심 브리핑 총평입니다.",
            "curated_articles": [
                {
                    "title": "생성형 AI로 연매출 100억 달성",
                    "url": "https://news.example.com/ai-revenue",
                    "pub_date": "2026-09-11 12:00",
                    "selection_reason": "구체적인 매출 지표 제시",
                    "summary_bullets": ["첫째 줄 요약", "둘째 줄 요약", "셋째 줄 요약"],
                    "insight": "초기 기업의 빠른 PMF 달성 전략",
                    "tags": ["AI", "매출", "스타트업"],
                }
            ],
        }

        response = self.client.post(
            reverse("curation:save_briefing_api"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("briefing_id", data)

        # DB 검증
        self.assertEqual(SavedBriefing.objects.count(), 1)
        briefing = SavedBriefing.objects.first()
        self.assertEqual(briefing.keyword, "생성형 AI")
        self.assertEqual(briefing.articles.count(), 1)

        art = briefing.articles.first()
        self.assertEqual(art.title, "생성형 AI로 연매출 100억 달성")
        self.assertEqual(len(art.summary_bullets), 3)

    def test_history_page(self):
        # 1. 빈 상태 확인
        response = self.client.get(reverse("curation:history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "아직 저장된 뉴스 브리핑이 없습니다")

        # 2. 데이터 생성 후 확인
        briefing = SavedBriefing.objects.create(
            keyword="양자컴퓨팅",
            filter_prompt="최신 기술 돌파구",
            overview_comment="양자컴퓨팅 혁신 요약입니다.",
        )
        SavedArticleSummary.objects.create(
            briefing=briefing,
            title="양자 우위 실현 기사",
            url="https://example.com/quantum",
            pub_date="2026-09-11 10:00",
            selection_reason="획기적 알고리즘 증명",
            summary_bullets=["양자 큐비트 수 증가", "에러율 감소", "상용화 가속"],
            insight="암호화 및 신약 개발 혁신",
            tags=["양자", "하드웨어"],
        )

        response = self.client.get(reverse("curation:history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "양자컴퓨팅")
        self.assertContains(response, "양자 우위 실현 기사")
        self.assertContains(response, "양자 큐비트 수 증가")

    def test_delete_briefing_api(self):
        briefing = SavedBriefing.objects.create(
            keyword="삭제대상",
            filter_prompt="테스트",
            overview_comment="삭제할 브리핑입니다.",
        )
        SavedArticleSummary.objects.create(
            briefing=briefing,
            title="삭제될 기사",
            url="https://example.com/delete",
            selection_reason="테스트",
            summary_bullets=["요약"],
            insight="인사이트",
        )

        self.assertEqual(SavedBriefing.objects.count(), 1)
        self.assertEqual(SavedArticleSummary.objects.count(), 1)

        # 삭제 API 호출
        response = self.client.post(reverse("curation:delete_briefing_api", kwargs={"pk": briefing.pk}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        # DB 삭제 확인
        self.assertEqual(SavedBriefing.objects.count(), 0)
        self.assertEqual(SavedArticleSummary.objects.count(), 0)
