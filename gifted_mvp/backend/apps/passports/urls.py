from django.urls import path

from .views import MyPassportView

urlpatterns = [
    path("passport/", MyPassportView.as_view(), name="passport-me"),
]
