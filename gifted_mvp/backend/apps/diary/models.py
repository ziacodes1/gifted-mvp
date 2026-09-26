"""My Diary: the learner's private journal.

Privacy boundary — diary rows (text, mood, tags, stickers, photos) belong to the learner
only. They are never read by parent endpoints, the Passport, evidence, scoring, or any
AI prompt, and are deliberately not registered in the Django admin. Writing in the diary
never creates evidence or changes signals.

Photos live in private storage (settings.PRIVATE_MEDIA_ROOT, not the public /media/ route)
under random names, re-encoded without metadata, and are served only by owner-checked views.
"""
import os
import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone


class Mood(models.TextChoices):
    VERY_LOW = "very_low", "Very low"
    LOW = "low", "Low"
    NEUTRAL = "neutral", "Okay"
    GOOD = "good", "Good"
    GREAT = "great", "Great"


class EntrySource(models.TextChoices):
    MANUAL = "MANUAL", "Written in the diary"
    COMPANION = "COMPANION", "Saved from an AI Companion chat"


class PrivateStorage(FileSystemStorage):
    """Local files under PRIVATE_MEDIA_ROOT (read per access, so test overrides apply). No URL."""

    @property
    def base_location(self):
        return settings.PRIVATE_MEDIA_ROOT

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    def url(self, name):
        raise NotImplementedError("private files are served by owner-checked views only")


private_storage = PrivateStorage()


def attachment_path(instance, filename):
    return f"diary/{instance.entry.learner_id}/{uuid.uuid4().hex}.webp"


class DiaryEntry(models.Model):
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="diary_entries")
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(blank=True)
    mood = models.CharField(max_length=10, choices=Mood.choices, blank=True)
    tags = models.JSONField(default=list, blank=True)  # ["school", "friends"] — the learner's own words
    stickers = models.JSONField(default=list, blank=True)  # [{"id": "leaf", "slot": 0}] — decorative only
    entry_date = models.DateField(default=timezone.localdate)
    source = models.CharField(max_length=10, choices=EntrySource.choices, default=EntrySource.MANUAL)
    # The student's own Companion message this entry was saved from (explicit opt-in only).
    companion_message = models.OneToOneField(
        "companion.CompanionMessage", null=True, blank=True, on_delete=models.SET_NULL, related_name="diary_entry"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "diary_entry"
        ordering = ["-entry_date", "-created_at", "-id"]
        indexes = [models.Index(fields=["learner", "-entry_date"])]

    def __str__(self) -> str:
        return f"{self.learner_id}:{self.pk}"


class DiaryAttachment(models.Model):
    entry = models.ForeignKey(DiaryEntry, on_delete=models.CASCADE, related_name="attachments")
    image = models.FileField(storage=private_storage, upload_to=attachment_path, max_length=200)
    caption = models.CharField(max_length=120, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "diary_attachment"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.entry_id}:{self.pk}"
