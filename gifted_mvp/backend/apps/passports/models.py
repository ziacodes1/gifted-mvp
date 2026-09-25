"""Gifted Passport — a thin aggregate over trusted evidence.

Signal scores are NOT copied here: they live in `signals.LearnerSignal` and the
AI interpretation in `ai.AIInsight`. The Passport row only records the
learner's passport identity, lifecycle state and which evidence it last
reflected, so the page can say "updated" / "version" honestly.
"""
from django.conf import settings
from django.db import models


class PassportStatus(models.TextChoices):
    EMPTY = "EMPTY", "Empty"
    EMERGING = "EMERGING", "Emerging"
    GROWING = "GROWING", "Growing"  # reserved: needs mission / real-world evidence


class Passport(models.Model):
    learner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="passport"
    )
    status = models.CharField(
        max_length=10, choices=PassportStatus.choices, default=PassportStatus.EMPTY
    )
    version = models.PositiveIntegerField(default=0)  # +1 each time new evidence is reflected
    source_session = models.ForeignKey(
        "assessments.AssessmentSession",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    last_evidence_id = models.PositiveBigIntegerField(null=True, blank=True)  # newest Evidence reflected
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "passports_passport"

    @property
    def passport_number(self) -> str:
        return f"GP-{self.created_at:%Y}-{self.pk:04d}"

    def __str__(self) -> str:
        return f"{self.passport_number} ({self.status})"
