from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.evidence.models import Evidence, EvidenceSource
from apps.passports.services import current_next_step, passport_snapshot
from common.permissions.roles import IsStudent

from .models import AttemptStatus, Mission, MissionAttempt, MissionStep
from .serializers import MissionDetailSerializer, attempt_payload, mission_summary
from .services import complete_attempt, featured_mission, match_mission, save_response, start_attempt


def _my_attempts(user) -> dict[int, MissionAttempt]:
    return {a.mission_id: a for a in MissionAttempt.objects.filter(learner=user)}


def _with_attempt(mission: Mission, attempt: MissionAttempt | None) -> dict:
    return {
        **mission_summary(mission),
        "my_attempt": {"id": attempt.id, "status": attempt.status} if attempt else None,
    }


class MissionListView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        attempts = _my_attempts(request.user)
        missions = Mission.objects.filter(is_active=True)
        return Response([_with_attempt(m, attempts.get(m.id)) for m in missions])


class RecommendedMissionView(APIView):
    """The mission to explore next. `match` is RECOMMENDED only when the saved
    next-step recommendation actually points in this mission's direction."""

    permission_classes = [IsStudent]

    def get(self, request):
        mission = featured_mission()
        if mission is None:
            return Response(None)
        attempt = MissionAttempt.objects.filter(learner=request.user, mission=mission).first()
        return Response(
            {**_with_attempt(mission, attempt), "match": match_mission(current_next_step(request.user), mission)}
        )


class MissionDetailView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, slug):
        mission = get_object_or_404(Mission.objects.prefetch_related("steps"), slug=slug, is_active=True)
        attempt = MissionAttempt.objects.filter(learner=request.user, mission=mission).first()
        data = MissionDetailSerializer(mission).data
        data["my_attempt"] = {"id": attempt.id, "status": attempt.status} if attempt else None
        data["match"] = match_mission(current_next_step(request.user), mission)
        return Response(data)


class MissionStartView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, slug):
        mission = get_object_or_404(Mission, slug=slug, is_active=True)
        attempt, created = start_attempt(request.user, mission)
        return Response(_attempt_response(attempt), status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


def _owned_attempt(request, pk) -> MissionAttempt:
    # 404 (not 403) for other learners' attempts: don't leak existence.
    return get_object_or_404(
        MissionAttempt.objects.select_related("mission").prefetch_related("mission__steps", "responses"),
        pk=pk,
        learner=request.user,
    )


def _attempt_response(attempt: MissionAttempt) -> dict:
    evidence = None
    if attempt.status == AttemptStatus.COMPLETED:
        evidence = Evidence.objects.filter(source_type=EvidenceSource.MISSION, source_id=attempt.id).first()
    return attempt_payload(attempt, evidence)


class MissionAttemptDetailView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, pk):
        return Response(_attempt_response(_owned_attempt(request, pk)))


class AnswerInput(serializers.Serializer):
    step_id = serializers.IntegerField()
    response = serializers.JSONField()


class MissionAttemptAnswerView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, pk):
        attempt = _owned_attempt(request, pk)
        payload = AnswerInput(data=request.data)
        payload.is_valid(raise_exception=True)
        step = get_object_or_404(MissionStep, pk=payload.validated_data["step_id"], mission=attempt.mission)
        save_response(attempt, step, payload.validated_data["response"])
        attempt = _owned_attempt(request, pk)
        return Response(_attempt_response(attempt))


class MissionAttemptCompleteView(APIView):
    """Idempotent: completing twice returns the same evidence (`evidence_created` false)."""

    permission_classes = [IsStudent]

    def post(self, request, pk):
        attempt = _owned_attempt(request, pk)
        evidence, created = complete_attempt(attempt)
        attempt = _owned_attempt(request, pk)
        return Response(
            {**attempt_payload(attempt, evidence), "evidence_created": created, "passport": passport_snapshot(request.user)}
        )
