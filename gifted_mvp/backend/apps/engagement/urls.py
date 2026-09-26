from django.urls import path

from .views import EngagementOverviewView, RedeemRewardView

urlpatterns = [
    path("engagement/overview/", EngagementOverviewView.as_view(), name="engagement-overview"),
    path("engagement/rewards/<slug:key>/redeem/", RedeemRewardView.as_view(), name="engagement-redeem"),
]
