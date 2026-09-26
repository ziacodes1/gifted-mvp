from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessments.services.scoring import SCORING_VERSION
from apps.engagement.rules import EventType
from apps.engagement.services import local_day, safe_record
from apps.passports.services import sync_passport
from apps.questions.models import MULTI_SELECT_TYPES, Question, QuestionOption
from common.i18n import label
from common.permissions.roles import IsStudent

from .models import Assessment, AssessmentResponse, AssessmentSession, SessionStatus
from .serializers import (
    AnswerInputSerializer,
    AssessmentDetailSerializer,
    AssessmentListSerializer,
    AssessmentSessionSerializer,
)
from .services.scoring import complete_session


class AssessmentListView(generics.ListAPIView):
    serializer_class = AssessmentListSerializer
    permission_classes = [IsStudent]
    queryset = Assessment.objects.filter(is_active=True).order_by("id")


class AssessmentDetailView(generics.RetrieveAPIView):
    serializer_class = AssessmentDetailSerializer
    permission_classes = [IsStudent]
    queryset = Assessment.objects.filter(is_active=True).order_by("id")


class AssessmentStartView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, pk):
        assessment = get_object_or_404(Assessment, pk=pk, is_active=True)
        session = (
            AssessmentSession.objects.filter(
                learner=request.user, assessment=assessment, status=SessionStatus.IN_PROGRESS
            )
            .order_by("-started_at")
            .first()
        )
        if session is None:
            session = AssessmentSession.objects.create(
                learner=request.user,
                assessment=assessment,
                status=SessionStatus.IN_PROGRESS,
                assessment_version=assessment.version,
                scoring_version=SCORING_VERSION,
            )
        return Response(
            AssessmentSessionSerializer(session).data,
            status=status.HTTP_200_OK if session.responses.exists() else status.HTTP_201_CREATED,
        )


def _validate_selection(question: Question, options: list[QuestionOption]) -> None:
    if question.type not in MULTI_SELECT_TYPES:
        if len(options) != 1:
            raise ValidationError("Choose one answer.")
        return
    lo, hi = question.content.get("min", 1), question.content.get("max", len(options))
    if not lo <= len(options) <= hi:
        raise ValidationError(f"Choose between {lo} and {hi} answers.")
    if len(options) > 1 and any(o.content.get("exclusive") for o in options):
        raise ValidationError("'None of these yet' can't be combined with other answers.")


def _get_owned_session(request, session_id) -> AssessmentSession:
    return get_object_or_404(AssessmentSession, pk=session_id, learner=request.user)


class AssessmentSessionDetailView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, pk):
        session = _get_owned_session(request, pk)
        return Response(AssessmentSessionSerializer(session).data)


class AssessmentSessionAnswerView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, pk):
        session = _get_owned_session(request, pk)
        if session.status == SessionStatus.COMPLETED:
            raise ValidationError("This session is already completed.")

        payload = AnswerInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        question_id = payload.validated_data["question_id"]
        question = get_object_or_404(
            Question, pk=question_id, section__assessment=session.assessment_id, is_active=True
        )
        options = list(QuestionOption.objects.filter(question=question, id__in=payload.validated_data["ids"]))
        if len(options) != len(payload.validated_data["ids"]):
            raise ValidationError("Unknown option for this question.")
        _validate_selection(question, options)

        response, _ = AssessmentResponse.objects.get_or_create(session=session, question=question)
        response.selected_options.set(options)
        response.save(update_fields=["updated_at"])
        # Assessment work makes the day active (no points; one event per session per day).
        safe_record(
            request.user, EventType.ASSESSMENT_PROGRESS, f"session:{session.id}:day:{local_day().isoformat()}"
        )

        total = sum(
            s.questions.filter(is_active=True).count() for s in session.assessment.sections.all()
        )
        answered = session.responses.count()
        session.progress = round(answered / total * 100) if total else 0
        session.save(update_fields=["progress"])

        return Response(
            {"progress": session.progress, "answered_count": answered, "total_questions": total}
        )


class AssessmentSessionCompleteView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, pk):
        session = _get_owned_session(request, pk)
        if session.status == SessionStatus.COMPLETED:
            raise ValidationError("This session is already completed.")

        total = sum(
            s.questions.filter(is_active=True).count() for s in session.assessment.sections.all()
        )
        answered = session.responses.count()
        if answered < total:
            raise ValidationError(
                f"Answer all questions before completing ({answered}/{total} answered)."
            )

        results = complete_session(session)
        sync_passport(request.user, session)
        safe_record(
            request.user, EventType.ASSESSMENT_COMPLETED, f"assessment:{session.assessment_id}:session:{session.id}"
        )

        signals_payload = [
            {
                "key": r.key,
                "label": r.label,
                "category": r.category,
                "score": r.score,
                "confidence": r.confidence,
            }
            for r in results
        ]

        return Response(
            {
                "session_id": session.id,
                "status": session.status,
                "signals": signals_payload,
                "top_signals": signals_payload[:3],
                "exposure_note": label("text", "exposure_note"),
                "ai_ready": True,
            }
        )
