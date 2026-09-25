from django.urls import path

from .views import ProfileSynthesisView

urlpatterns = [
    path("ai/profile-synthesis/", ProfileSynthesisView.as_view(), name="ai-profile-synthesis"),
]
