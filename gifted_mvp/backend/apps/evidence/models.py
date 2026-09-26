"""Generic, source-agnostic evidence.

Any activity (assessment, mission, future virtual lab / opportunity / real-world
activity) records what it deterministically observed as one `Evidence` row plus
`SignalEvidence` contributions. Evidence never overwrites assessment scores in
`LearnerSignal`: it sits alongside them so the Passport can say *where* its
picture comes from.
"""
from django.conf import settings
from django.db import models


class EvidenceSource(models.TextChoices):
    ASSESSMENT = "ASSESSMENT", "Assessment"
    MISSION = "MISSION", "Exploration mission"
    VIRTUAL_LAB = "VIRTUAL_LAB", "Virtual lab"
    OPPORTUNITY = "OPPORTUNITY", "Opportunity"
    REAL_WORLD = "REAL_WORLD", "Real-world activity"
    RESOURCE = "RESOURCE", "Learning resource"


class EvidenceKind(models.TextChoices):
    """What a contribution is evidence *of*. None of these is proof of ability."""

    INTEREST = "INTEREST", "Interest"
    EXPOSURE = "EXPOSURE", "Exposure"
    ENGAGEMENT = "ENGAGEMENT", "Engagement"
    DECISION = "DECISION", "Decision-making"
    REASONING = "REASONING", "Reasoning"
    REFLECTION = "REFLECTION", "Reflection"


class Evidence(models.Model):
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="evidence"
    )
    source_type = models.CharField(max_length=16, choices=EvidenceSource.choices, db_index=True)
    # PK of the producing record (AssessmentSession, MissionAttempt, ...). A plain
    # id + type keeps this generic without GenericForeignKey machinery.
    source_id = models.PositiveBigIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)  # deterministic observations
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "evidence_evidence"
        ordering = ["-created_at"]
        constraints = [
            # One evidence record per producing activity → idempotent completion.
            models.UniqueConstraint(fields=["source_type", "source_id"], name="uniq_evidence_per_source")
        ]

    def __str__(self) -> str:
        return f"{self.learner_id}:{self.source_type}:{self.source_id}"


class SignalEvidence(models.Model):
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name="contributions")
    signal = models.ForeignKey("signals.Signal", on_delete=models.CASCADE, related_name="evidence")
    kind = models.CharField(max_length=12, choices=EvidenceKind.choices)
    # Small, bounded contribution (0-1 per activity). Deliberately not a score.
    weight = models.DecimalField(max_digits=4, decimal_places=2)
    observation = models.CharField(max_length=300, blank=True)

    class Meta:
        db_table = "evidence_signal_evidence"
        unique_together = ("evidence", "signal")

    def __str__(self) -> str:
        return f"{self.evidence_id}->{self.signal_id}:{self.kind}:{self.weight}"
