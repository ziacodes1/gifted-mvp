"""Engagement: activity events, badges, rewards.

Privacy boundary — an ActivityEvent is only (learner, type, idempotency key, points, day).
It never stores content: no diary text/mood/tags/photos, no chat text, no answers. The
leaderboard reads points only and shows a first name + initial.
"""
from django.conf import settings
from django.db import models

from .rules import EventType, RewardType


class ActivityEvent(models.Model):
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_events")
    event_type = models.CharField(max_length=32, choices=EventType.CHOICES)
    # Idempotency key, e.g. "assessment:3:session:12", "attempt:7", "entry:41". Never content.
    source_key = models.CharField(max_length=80)
    points = models.PositiveSmallIntegerField(default=0)
    occurred_on = models.DateField()  # the learner-local activity day
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "engagement_activity_event"
        ordering = ["-occurred_on", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["learner", "event_type", "source_key"], name="uniq_activity_event")
        ]
        indexes = [models.Index(fields=["occurred_on", "learner"]), models.Index(fields=["learner", "occurred_on"])]

    def __str__(self) -> str:
        return f"{self.learner_id}:{self.event_type}:{self.source_key}"


class StudentBadge(models.Model):
    """An unlocked badge. Badges are never revoked (missing days never removes one)."""

    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="badges")
    badge_key = models.CharField(max_length=40)  # engagement.rules.BADGES
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "engagement_student_badge"
        constraints = [models.UniqueConstraint(fields=["learner", "badge_key"], name="uniq_student_badge")]


class Reward(models.Model):
    key = models.SlugField(max_length=40, unique=True)
    title = models.CharField(max_length=80)
    description = models.CharField(max_length=240)
    points_required = models.PositiveIntegerField()
    reward_type = models.CharField(max_length=12, choices=RewardType.CHOICES)
    image_key = models.CharField(max_length=40)  # frontend asset key
    active = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(null=True, blank=True)  # None = unlimited
    one_per_learner = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    translations = models.JSONField(default=dict, blank=True)  # {"uz": {"title": ..., "description": ...}, "ru": {...}}

    class Meta:
        db_table = "engagement_reward"
        ordering = ["order", "points_required"]

    def __str__(self) -> str:
        return self.key


class RedemptionStatus(models.TextChoices):
    RESERVED = "RESERVED", "Reserved (awaiting the Gifted team)"
    FULFILLED = "FULFILLED", "Fulfilled"
    CANCELLED = "CANCELLED", "Cancelled"


class RewardRedemption(models.Model):
    """Spends available points; never touches earned points or leaderboard history."""

    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reward_redemptions")
    reward = models.ForeignKey(Reward, on_delete=models.PROTECT, related_name="redemptions")
    points_spent = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=RedemptionStatus.choices, default=RedemptionStatus.RESERVED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "engagement_reward_redemption"
        ordering = ["-created_at"]
