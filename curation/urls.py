"""Curation 앱 URL 라우팅 설정"""

from django.urls import path

from . import views

app_name = "curation"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/curate/", views.curate_api, name="curate_api"),
    path("api/save/", views.save_briefing_api, name="save_briefing_api"),
    path("history/", views.history_view, name="history"),
    path("api/history/<int:pk>/delete/", views.delete_briefing_api, name="delete_briefing_api"),
]
