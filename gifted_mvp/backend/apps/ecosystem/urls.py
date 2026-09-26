from django.urls import path

from . import views

urlpatterns = [
    path("resources/", views.ResourceListView.as_view(), name="resources"),
    path("resources/<slug:slug>/", views.ResourceDetailView.as_view(), name="resource-detail"),
    path("resources/<slug:slug>/action/", views.ResourceActionView.as_view(), name="resource-action"),
    path("learning-paths/<slug:slug>/", views.LearningPathView.as_view(), name="learning-path"),
    path("opportunities/", views.OpportunityListView.as_view(), name="opportunities"),
    path("opportunities/<slug:slug>/", views.OpportunityDetailView.as_view(), name="opportunity-detail"),
    path("opportunities/<slug:slug>/action/", views.OpportunityActionView.as_view(), name="opportunity-action"),
    path("community/", views.CommunityView.as_view(), name="community"),
    path("community/circles/<slug:slug>/", views.CircleView.as_view(), name="community-circle"),
    path("community/posts/", views.PostCreateView.as_view(), name="community-posts"),
    path("community/posts/<int:post_id>/report/", views.PostReportView.as_view(), name="community-report"),
    path("ecosystem/for-you/", views.ForYouView.as_view(), name="ecosystem-for-you"),
]
