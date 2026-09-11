"""Curation Django Admin 설정"""

from django.contrib import admin

from .models import SavedArticleSummary, SavedBriefing


class SavedArticleSummaryInline(admin.StackedInline):
    model = SavedArticleSummary
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(SavedBriefing)
class SavedBriefingAdmin(admin.ModelAdmin):
    list_display = ("keyword", "article_count", "created_at")
    list_filter = ("created_at",)
    search_fields = ("keyword", "filter_prompt", "overview_comment")
    inlines = (SavedArticleSummaryInline,)

    def article_count(self, obj):
        return obj.articles.count()

    article_count.short_description = "저장된 기사 수"


@admin.register(SavedArticleSummary)
class SavedArticleSummaryAdmin(admin.ModelAdmin):
    list_display = ("title", "briefing", "pub_date", "created_at")
    list_filter = ("created_at", "briefing__keyword")
    search_fields = ("title", "selection_reason", "insight")
