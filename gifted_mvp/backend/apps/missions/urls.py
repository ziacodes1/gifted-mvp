from django.urls import path

from .views import (
    MissionAttemptAnswerView,
    MissionAttemptCompleteView,
    MissionAttemptDetailView,
    MissionDetailView,
    MissionListView,
    MissionStartView,
    RecommendedMissionView,
)

urlpatterns = [
    path("missions/", MissionListView.as_view(), name="mission-list"),
    path("missions/recommended/", RecommendedMissionView.as_view(), name="mission-recommended"),
    path("missions/<slug:slug>/", MissionDetailView.as_view(), name="mission-detail"),
    path("missions/<slug:slug>/start/", MissionStartView.as_view(), name="mission-start"),
    path("mission-attempts/<int:pk>/", MissionAttemptDetailView.as_view(), name="mission-attempt-detail"),
    path("mission-attempts/<int:pk>/answer/", MissionAttemptAnswerView.as_view(), name="mission-attempt-answer"),
    path("mission-attempts/<int:pk>/complete/", MissionAttemptCompleteView.as_view(), name="mission-attempt-complete"),
]
