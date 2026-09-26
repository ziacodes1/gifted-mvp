from django.urls import path

from .views import NudgesSeenView, SparkActionView, TodayView

urlpatterns = [
    path("today/", TodayView.as_view(), name="today"),
    path("today/spark/", SparkActionView.as_view(), name="today-spark"),
    path("today/nudges/seen/", NudgesSeenView.as_view(), name="today-nudges-seen"),
]
