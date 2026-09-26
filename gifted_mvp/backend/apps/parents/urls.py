from django.urls import path

from .views import (
    ParentChildInsightView,
    ParentChildOverviewView,
    ParentChildrenView,
    ParentConnectView,
    StudentParentAccessView,
    StudentParentCodeView,
    StudentParentLinkView,
)

urlpatterns = [
    path("parent/children/", ParentChildrenView.as_view(), name="parent-children"),
    path("parent/children/connect/", ParentConnectView.as_view(), name="parent-connect"),
    path("parent/children/<int:learner_id>/overview/", ParentChildOverviewView.as_view(), name="parent-child-overview"),
    path("parent/children/<int:learner_id>/insight/", ParentChildInsightView.as_view(), name="parent-child-insight"),
    path("parent-access/", StudentParentAccessView.as_view(), name="student-parent-access"),
    path("parent-access/code/", StudentParentCodeView.as_view(), name="student-parent-code"),
    path("parent-access/parents/<int:parent_id>/", StudentParentLinkView.as_view(), name="student-parent-link"),
]
