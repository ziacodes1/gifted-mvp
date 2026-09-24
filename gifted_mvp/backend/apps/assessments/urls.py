from django.urls import path

from .views import (
    AssessmentDetailView,
    AssessmentListView,
    AssessmentSessionAnswerView,
    AssessmentSessionCompleteView,
    AssessmentSessionDetailView,
    AssessmentStartView,
)

urlpatterns = [
    path("assessments/", AssessmentListView.as_view(), name="assessment-list"),
    path("assessments/<int:pk>/", AssessmentDetailView.as_view(), name="assessment-detail"),
    path("assessments/<int:pk>/start/", AssessmentStartView.as_view(), name="assessment-start"),
    path(
        "assessment-sessions/<int:pk>/",
        AssessmentSessionDetailView.as_view(),
        name="assessment-session-detail",
    ),
    path(
        "assessment-sessions/<int:pk>/answer/",
        AssessmentSessionAnswerView.as_view(),
        name="assessment-session-answer",
    ),
    path(
        "assessment-sessions/<int:pk>/complete/",
        AssessmentSessionCompleteView.as_view(),
        name="assessment-session-complete",
    ),
]
