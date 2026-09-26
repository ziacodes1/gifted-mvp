from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions.roles import IsStudent

from .models import DiaryAttachment, DiaryEntry, EntrySource, Mood
from .services import (
    MAX_BODY_CHARS,
    InvalidPhoto,
    add_photo,
    clean_stickers,
    clean_tags,
    companion_draft,
    create_entry,
    entry_detail,
    entry_summary,
    overview,
    photo_payload,
)


def _owned_entry(request, pk) -> DiaryEntry:
    # 404 (not 403) for other learners' entries: don't leak existence.
    return get_object_or_404(DiaryEntry.objects.prefetch_related("attachments"), pk=pk, learner=request.user)


def _owned_photo(request, pk) -> DiaryAttachment:
    return get_object_or_404(DiaryAttachment.objects.select_related("entry"), pk=pk, entry__learner=request.user)


class EntryInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=120, required=False, allow_blank=True)
    body = serializers.CharField(max_length=MAX_BODY_CHARS, required=False, allow_blank=True, trim_whitespace=False)
    mood = serializers.ChoiceField(choices=Mood.choices, required=False, allow_blank=True, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=60), required=False, max_length=20)
    stickers = serializers.ListField(child=serializers.DictField(), required=False, max_length=20)
    entry_date = serializers.DateField(required=False)
    companion_message_id = serializers.IntegerField(required=False, min_value=1)

    def validate(self, attrs):
        if "mood" in attrs:
            attrs["mood"] = attrs["mood"] or ""
        if "tags" in attrs:
            attrs["tags"] = clean_tags(attrs["tags"])
        if "stickers" in attrs:
            attrs["stickers"] = clean_stickers(attrs["stickers"])
        if "body" in attrs:
            attrs["body"] = attrs["body"].strip()
        return attrs


class DiaryOverviewView(APIView):
    """GET: progress (1 entry = 1 page), recent entries, the open-book pages and this week's moods."""

    permission_classes = [IsStudent]

    def get(self, request):
        return Response(overview(request.user))


class EntryListView(ListAPIView):
    """GET: the learner's entries, newest first (paginated; `?source=COMPANION` for Diary moments).
    POST: create — manual, or from a Companion message the learner chose to save."""

    permission_classes = [IsStudent]

    def get_queryset(self):
        qs = DiaryEntry.objects.filter(learner=self.request.user).prefetch_related("attachments")
        source = self.request.query_params.get("source")
        return qs.filter(source=source) if source in EntrySource.values else qs

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.get_queryset())
        return self.get_paginated_response([entry_summary(e) for e in page])

    def post(self, request):
        data = EntryInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        values = dict(data.validated_data)
        if not (values.get("title", "").strip() or values.get("body")):
            raise serializers.ValidationError({"body": "Write a title or a few words first."})
        entry, created = create_entry(request.user, values)
        entry = _owned_entry(request, entry.pk)
        return Response(entry_detail(entry), status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class EntryDetailView(APIView):
    permission_classes = [IsStudent]

    def get(self, request, pk):
        return Response(entry_detail(_owned_entry(request, pk)))

    def patch(self, request, pk):
        entry = _owned_entry(request, pk)
        data = EntryInputSerializer(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        values = dict(data.validated_data)
        values.pop("companion_message_id", None)  # the link is set once, at creation
        for field, value in values.items():
            setattr(entry, field, value)
        if not (entry.title.strip() or entry.body):
            raise serializers.ValidationError({"body": "Write a title or a few words first."})
        entry.save()
        return Response(entry_detail(_owned_entry(request, pk)))

    def delete(self, request, pk):
        _owned_entry(request, pk).delete()  # photos are removed from disk by a signal
        return Response(status=status.HTTP_204_NO_CONTENT)


class EntryPhotosView(APIView):
    """POST multipart {file, caption?}: add a photo (JPEG/PNG/WebP, ≤ 5 MB, max 4 per entry)."""

    permission_classes = [IsStudent]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        entry = _owned_entry(request, pk)
        upload = request.FILES.get("file")
        if upload is None:
            raise serializers.ValidationError({"file": "Choose a photo."})
        try:
            photo = add_photo(entry, upload, str(request.data.get("caption", "")))
        except InvalidPhoto as exc:  # code: too_large | not_an_image | unsupported_type | too_many
            raise serializers.ValidationError({"file": str(exc)}) from exc
        return Response(photo_payload(photo), status=status.HTTP_201_CREATED)


class PhotoDetailView(APIView):
    """GET: the image bytes (owner only; private cache). PATCH {caption}. DELETE."""

    permission_classes = [IsStudent]

    def get(self, request, pk):
        photo = _owned_photo(request, pk)
        response = FileResponse(photo.image.open("rb"), content_type="image/webp")
        response["Cache-Control"] = "private, max-age=3600"
        response["X-Content-Type-Options"] = "nosniff"
        return response

    def patch(self, request, pk):
        photo = _owned_photo(request, pk)
        photo.caption = str(request.data.get("caption", ""))[:120]
        photo.save(update_fields=["caption"])
        return Response(photo_payload(photo))

    def delete(self, request, pk):
        _owned_photo(request, pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompanionDraftSerializer(serializers.Serializer):
    message_id = serializers.IntegerField(min_value=1)


class CompanionDraftView(APIView):
    """POST {message_id}: after the student clicks "Add to My Diary". Returns an editor prefill
    built from their own message (no AI call, nothing saved), or the entry already saved from it."""

    permission_classes = [IsStudent]

    def post(self, request):
        data = CompanionDraftSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(companion_draft(request.user, data.validated_data["message_id"]))
