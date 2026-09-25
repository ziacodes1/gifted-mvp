from django.urls import path

from .views import ParentChildInsightView, ParentChildOverviewView, ParentChildrenView, ParentConnectView

urlpatterns = [
    path("parent/children/", ParentChildrenView.as_view(), name="parent-children"),
    path("parent/children/connect/", ParentConnectView.as_view(), name="parent-connect"),
    path("parent/children/<int:learner_id>/overview/", ParentChildOverviewView.as_view(), name="parent-child-overview"),
    path("parent/children/<int:learner_id>/insight/", ParentChildInsightView.as_view(), name="parent-child-insight"),
]
