from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.i18n import current_language
from common.permissions.roles import IsStudent

from .models import CompanionConversation
from .services import (
    MAX_MESSAGE_CHARS,
    CompanionUnavailable,
    companion_overview,
    dismiss_diary_offer,
    send_message,
    start_conversation,
)

LIST_LIMIT = 30


def _diary_entry_id(user_message):
    try:
        return user_message.diary_entry.id if user_message else None
    except ObjectDoesNotExist:
        return None


def message_payload(m) -> dict:
    data = {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at}
    if m.role == "ASSISTANT":
        # The offer refers to the student's own message this turn answered; saving it is a
        # separate, explicit action in My Diary.
        data["diary"] = {
            "offer": m.diary_offer,
            "student_message_id": m.reply_to_id,
            "entry_id": _diary_entry_id(m.reply_to),
        }
    return data


def conversation_summary(c) -> dict:
    return {"id": c.id, "title": c.title, "created_at": c.created_at, "updated_at": c.updated_at}


def _owned(request, pk) -> CompanionConversation:
    # 404 (not 403) for other learners' conversations: don't leak existence.
    return get_object_or_404(CompanionConversation, pk=pk, learner=request.user)


class CompanionOverviewView(APIView):
    """GET: 'About you' card + state-aware suggested prompts. Never calls a model."""

    permission_classes = [IsStudent]

    def get(self, request):
        return Response(companion_overview(request.user, current_language()))


class ConversationListView(APIView):
    permission_classes = [IsStudent]

    def get(self, request):
        rows = CompanionConversation.objects.filter(learner=request.user, messages__isnull=False).distinct()
        return Response([conversation_summary(c) for c in rows.order_by("-updated_at", "-id")[:LIST_LIMIT]])

    def post(self, request):
        conversation, created = start_conversation(request.user)
        return Response(
            {**conversation_summary(conversation), "messages": []},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ConversationDetailView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, pk):
        conversation = _owned(request, pk)
        return Response(
            {
                **conversation_summary(conversation),
                "messages": [
                    message_payload(m) for m in conversation.messages.select_related("reply_to__diary_entry")
                ],
            }
        )


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=MAX_MESSAGE_CHARS, trim_whitespace=True)
    client_id = serializers.UUIDField()


class ConversationMessagesView(APIView):
    """POST {content, client_id}: the learner's message + the Companion's reply.

    Idempotent per client_id (a retry returns the stored pair, 200). If no reply could be
    produced, nothing is stored and the response is 503 `companion_unavailable` — never a
    fake answer and never provider details."""

    permission_classes = [IsStudent]
    throttle_scope = "companion"

    def post(self, request, pk):
        conversation = _owned(request, pk)
        data = SendMessageSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            turn = send_message(
                conversation, data.validated_data["content"], data.validated_data["client_id"], current_language()
            )
        except CompanionUnavailable:
            # Same envelope as common.exceptions; the frontend shows its own localized copy.
            return Response(
                {"error": {"detail": "companion_unavailable", "status": 503}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        conversation.refresh_from_db(fields=["title", "updated_at"])
        return Response(
            {
                "conversation": conversation_summary(conversation),
                "user_message": message_payload(turn.user),
                "assistant_message": message_payload(turn.assistant),
            },
            status=status.HTTP_201_CREATED if turn.created else status.HTTP_200_OK,
        )


class DismissDiaryOfferView(APIView):
    """POST: "Keep only in chat" — hides the diary offer on one of the learner's assistant turns."""

    permission_classes = [IsStudent]

    def post(self, request, pk):
        if not dismiss_diary_offer(request.user, pk):
            raise Http404
        return Response(status=status.HTTP_204_NO_CONTENT)
