"""뉴스 큐레이션 및 요약 결과 저장용 Django 모델"""

from django.db import models


class SavedBriefing(models.Model):
    """AI 뉴스 브리핑 마스터 모델"""

    keyword = models.CharField(max_length=200, verbose_name="검색 키워드")
    filter_prompt = models.TextField(verbose_name="필터링 프롬프트")
    overview_comment = models.TextField(verbose_name="AI 총평 코멘트")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="저장 일시")

    class Meta:
        db_table = "saved_briefings"
        ordering = ("-created_at",)
        verbose_name = "저장된 뉴스 브리핑"
        verbose_name_plural = "저장된 뉴스 브리핑 목록"

    def __str__(self) -> str:
        formatted_date = self.created_at.strftime("%Y-%m-%d %H:%M")
        return f"[{formatted_date}] {self.keyword} ({self.articles.count()}건)"


class SavedArticleSummary(models.Model):
    """브리핑에 포함된 개별 뉴스 기사 및 심층 요약 모델"""

    briefing = models.ForeignKey(
        SavedBriefing,
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name="소속 브리핑",
    )
    title = models.CharField(max_length=500, verbose_name="뉴스 제목")
    url = models.URLField(max_length=1000, verbose_name="기사 원문 링크")
    pub_date = models.CharField(max_length=100, blank=True, verbose_name="발행 일시")
    selection_reason = models.TextField(verbose_name="AI 선정 이유")
    summary_bullets = models.JSONField(
        default=list,
        verbose_name="핵심 3줄 요약 목록",
        help_text="3개의 요약 문장을 담은 JSON 배열",
    )
    insight = models.TextField(verbose_name="비즈니스 인사이트 및 시사점")
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name="태그 목록",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="저장 일시")

    class Meta:
        db_table = "saved_article_summaries"
        ordering = ("id",)
        verbose_name = "기사 요약"
        verbose_name_plural = "기사 요약 목록"

    def __str__(self) -> str:
        return self.title

    @property
    def summary_text(self) -> str:
        """줄바꿈으로 연결된 요약 본문 텍스트"""
        if isinstance(self.summary_bullets, list):
            return "\n".join(f"• {b}" for b in self.summary_bullets)
        return str(self.summary_bullets)
