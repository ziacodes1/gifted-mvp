from django.urls import path

from .views import MySignalsView

urlpatterns = [
    path("signals/me/", MySignalsView.as_view(), name="signals-me"),
]
