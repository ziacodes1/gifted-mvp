from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessments.models import AssessmentSession, SessionStatus
from common.permissions.roles import IsStudent

from .services.profile_synthesis import get_or_create_profile_insight


class ProfileSynthesisInputSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(required=False, min_value=1)


class ProfileSynthesisView(APIView):
    """POST: get-or-generate the learner's profile insight for a completed session.

    Idempotent — repeated calls return the persisted insight. Scores are never
    accepted from the client; the backend re-derives them from stored responses.
    """

    permission_classes = [IsStudent]

    def post(self, request):
        data = ProfileSynthesisInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        session_id = data.validated_data.get("session_id")

        owned = AssessmentSession.objects.filter(learner=request.user).select_related("assessment")
        if session_id:
            session = get_object_or_404(owned, pk=session_id)
            if session.status != SessionStatus.COMPLETED:
                raise ValidationError("Complete the assessment before generating a profile.")
        else:
            session = (
                owned.filter(status=SessionStatus.COMPLETED).order_by("-completed_at").first()
            )
            if session is None:
                raise NotFound("No completed assessment yet.")

        insight = get_or_create_profile_insight(session)
        return Response(
            {
                "session_id": session.id,
                "source": insight.source,
                "profile": insight.result["profile"],
                "next_step": insight.result["next_step"],
                "generated_at": insight.updated_at,
            }
        )
