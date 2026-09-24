"""Deterministic signal taxonomy + accumulated learner scores.

Scores are never produced by an LLM — they come only from
`apps.assessments.services.scoring`. This module just stores the taxonomy
and the result.
"""
from django.conf import settings
from django.db import models


class SignalCategory(models.TextChoices):
    INTEREST = "INTEREST", "Interest"
    APTITUDE = "APTITUDE", "Aptitude"
    WORK_STYLE = "WORK_STYLE", "Work style"
    VALUE = "VALUE", "Value"
    EXPOSURE = "EXPOSURE", "Exposure"


class Signal(models.Model):
    key = models.SlugField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    category = models.CharField(max_length=16, choices=SignalCategory.choices, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "signals_signal"

    def __str__(self) -> str:
        return f"{self.category}:{self.key}"


class ResponseSignalMap(models.Model):
    """Deterministic contribution: picking `option` counts toward `signal`."""

    option = models.ForeignKey(
        "questions.QuestionOption", on_delete=models.CASCADE, related_name="signal_maps"
    )
    signal = models.ForeignKey(Signal, on_delete=models.CASCADE, related_name="option_maps")
    weight = models.DecimalField(max_digits=4, decimal_places=2, default=1)

    class Meta:
        db_table = "signals_response_map"
        unique_together = ("option", "signal")

    def __str__(self) -> str:
        return f"{self.option_id}->{self.signal.key}:{self.weight}"


class Confidence(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"


class LearnerSignal(models.Model):
    """Accumulated, current score per (learner, signal) — updated in place so
    retakes refine evidence rather than duplicating rows.
    """

    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="signals"
    )
    signal = models.ForeignKey(Signal, on_delete=models.CASCADE, related_name="learner_scores")
    score = models.PositiveSmallIntegerField(default=0)  # 0-100
    confidence = models.CharField(max_length=8, choices=Confidence.choices, default=Confidence.LOW)
    evidence_count = models.PositiveSmallIntegerField(default=0)
    # How many answered questions could have shown this signal (denominator of `score`).
    opportunity_count = models.PositiveSmallIntegerField(default=0)
    source_session = models.ForeignKey(
        "assessments.AssessmentSession", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "signals_learner_signal"
        unique_together = ("learner", "signal")
        ordering = ["-score"]

    def __str__(self) -> str:
        return f"{self.learner_id}:{self.signal.key}={self.score}"
