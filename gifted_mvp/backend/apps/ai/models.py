"""Persisted AI-generated insights.

One row per (session, generation_type, input_version, language) — a Uzbek insight is
never served from the English row, and each language is generated at most once. AI rows are final; a
FALLBACK row may be upgraded in place to AI once the provider is reachable.
"""
from django.conf import settings
from django.db import models


class GenerationType(models.TextChoices):
    PROFILE_SYNTHESIS = "PROFILE_SYNTHESIS", "Profile synthesis + next step"
    PARENT_INSIGHT = "PARENT_INSIGHT", "Parent insight"


class InsightSource(models.TextChoices):
    AI = "AI", "AI"
    FALLBACK = "FALLBACK", "Deterministic fallback"


class AIInsight(models.Model):
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_insights"
    )
    session = models.ForeignKey(
        "assessments.AssessmentSession", on_delete=models.CASCADE, related_name="ai_insights"
    )
    generation_type = models.CharField(max_length=32, choices=GenerationType.choices)
    input_version = models.CharField(max_length=32)
    language = models.CharField(max_length=5, default="en")  # en | uz | ru (common.i18n.SUPPORTED)
    source = models.CharField(max_length=8, choices=InsightSource.choices)
    provider = models.CharField(max_length=32, blank=True)
    model = models.CharField(max_length=64, blank=True)
    result = models.JSONField()
    # Traceability (no prompts, no learner text): which prompt/schema produced this row, how
    # long the provider took, and — for FALLBACK rows — the safe failure category.
    prompt_version = models.CharField(max_length=16, blank=True)
    schema_version = models.CharField(max_length=16, blank=True)
    latency_ms = models.PositiveIntegerField(default=0)
    failure_reason = models.CharField(max_length=60, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_insight"
        constraints = [
            models.UniqueConstraint(
                fields=["session", "generation_type", "input_version", "language"],
                name="uniq_ai_insight_per_session_type_version_lang",
            )
        ]

    def __str__(self) -> str:
        return f"{self.learner_id}:{self.session_id}:{self.generation_type}:{self.language}:{self.source}"
