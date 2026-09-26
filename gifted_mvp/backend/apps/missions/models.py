"""Missions: short real-world challenges that explore (never prove) emerging signals.

Content is server-driven (`MissionStep.content` JSON rendered by type). What a
mission can say about a learner is defined up-front and deterministically in
`MissionSignalMap` — never by an LLM, and never exposed to the client.
"""
from django.conf import settings
from django.db import models

from apps.evidence.models import EvidenceKind


class Difficulty(models.TextChoices):
    BEGINNER = "BEGINNER", "Beginner"
    INTERMEDIATE = "INTERMEDIATE", "Intermediate"


class Mission(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=80, unique=True)
    short_description = models.CharField(max_length=300)
    context = models.TextField(blank=True)
    difficulty = models.CharField(max_length=16, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    estimated_minutes = models.PositiveSmallIntegerField(default=8)  # upper bound
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    # Presentation + matching hints: focus_areas, activity_label, time_label, match_keywords.
    metadata = models.JSONField(default=dict, blank=True)
    # {"uz": {...}, "ru": {...}} — localized overrides of the English fields (see common.i18n).
    translations = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "missions_mission"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.slug


class StepType(models.TextChoices):
    CONTEXT = "CONTEXT", "Context"
    MULTI_SELECT = "MULTI_SELECT", "Choose several"
    BUDGET = "BUDGET", "Prioritize within a budget"
    SINGLE_CHOICE = "SINGLE_CHOICE", "Choose one"
    REFLECTION = "REFLECTION", "Reflection"


class MissionStep(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="steps")
    key = models.SlugField(max_length=40)
    type = models.CharField(max_length=16, choices=StepType.choices)
    title = models.CharField(max_length=150)
    prompt = models.TextField(blank=True)
    content = models.JSONField(default=dict, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    # {"uz": {...}, "ru": {...}} — localized overrides of the English fields (see common.i18n).
    translations = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "missions_step"
        ordering = ["order", "id"]
        unique_together = ("mission", "key")

    def __str__(self) -> str:
        return f"{self.mission.slug}:{self.key}"


class MissionSignalMap(models.Model):
    """Deterministic evidence rule.

    - step=None             → applies when the mission is completed
    - step set, option_key="" → applies when that step is answered
    - step set, option_key    → applies when that option/field was chosen/filled
    """

    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="signal_maps")
    step = models.ForeignKey(MissionStep, on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    option_key = models.CharField(max_length=40, blank=True)
    signal = models.ForeignKey("signals.Signal", on_delete=models.CASCADE, related_name="+")
    kind = models.CharField(max_length=12, choices=EvidenceKind.choices)
    weight = models.DecimalField(max_digits=4, decimal_places=2)
    observation = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "missions_signal_map"

    def __str__(self) -> str:
        return f"{self.mission.slug}:{self.step_id}:{self.option_key}->{self.signal_id}"


class AttemptStatus(models.TextChoices):
    NOT_STARTED = "NOT_STARTED", "Not started"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    COMPLETED = "COMPLETED", "Completed"


class MissionAttempt(models.Model):
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mission_attempts"
    )
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="attempts")
    status = models.CharField(max_length=12, choices=AttemptStatus.choices, default=AttemptStatus.IN_PROGRESS)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "missions_attempt"
        # MVP: one attempt per learner per mission (a completed mission is evidence once).
        unique_together = ("learner", "mission")

    def __str__(self) -> str:
        return f"{self.learner_id}:{self.mission.slug}:{self.status}"


class MissionResponse(models.Model):
    attempt = models.ForeignKey(MissionAttempt, on_delete=models.CASCADE, related_name="responses")
    step = models.ForeignKey(MissionStep, on_delete=models.CASCADE, related_name="+")
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "missions_response"
        unique_together = ("attempt", "step")

    def __str__(self) -> str:
        return f"{self.attempt_id}:{self.step_id}"
