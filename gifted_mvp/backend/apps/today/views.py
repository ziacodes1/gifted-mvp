from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions.roles import IsStudent

from .models import SparkStatus
from .services import SparkActionError, mark_nudges_seen, set_spark_status, today_overview


class TodayView(APIView):
    """GET: today's Spark, a motivation key and in-app nudges (one payload, no AI call)."""

    permission_classes = [IsStudent]

    def get(self, request):
        return Response(today_overview(request.user))


class SparkActionSerializer(serializers.Serializer):
    spark_key = serializers.CharField(max_length=40)
    action = serializers.ChoiceField(choices=["complete", "dismiss", "restore"])


class SparkActionView(APIView):
    """POST {spark_key, action}: complete (mini challenges; idempotent) · dismiss · restore."""

    permission_classes = [IsStudent]

    def post(self, request):
        data = SparkActionSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        target = {"complete": SparkStatus.DONE, "dismiss": SparkStatus.DISMISSED, "restore": SparkStatus.NEW}[
            data.validated_data["action"]
        ]
        try:
            set_spark_status(request.user, data.validated_data["spark_key"], target)
        except SparkActionError as exc:
            return Response({"error": {"detail": str(exc), "status": 400}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(today_overview(request.user))


class NudgesSeenView(APIView):
    permission_classes = [IsStudent]

    def post(self, request):
        mark_nudges_seen(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
