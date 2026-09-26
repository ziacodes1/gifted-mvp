from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.i18n import current_language
from common.permissions.roles import IsStudent

from .services import RedemptionError, backfill_learner, overview, points_summary, redeem


class EngagementOverviewView(APIView):
    """GET: streak, points, badges, weekly leaderboard, standing, rewards — one read model.
    Also derives any missing activity for this learner (idempotent, ids/timestamps only)."""

    permission_classes = [IsStudent]

    def get(self, request):
        backfill_learner(request.user)
        return Response(overview(request.user, current_language()))


class RedeemRewardView(APIView):
    """POST: reserve a reward with available points. 400 {detail: code} when not possible."""

    permission_classes = [IsStudent]
    throttle_scope = "redeem"

    def post(self, request, key):
        try:
            redemption = redeem(request.user, key)
        except RedemptionError as exc:
            return Response({"error": {"detail": str(exc), "status": 400}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "reward_key": redemption.reward.key,
                "reward_type": redemption.reward.reward_type,
                "status": redemption.status,
                "points_spent": redemption.points_spent,
                "points": points_summary(request.user),
            },
            status=status.HTTP_201_CREATED,
        )
