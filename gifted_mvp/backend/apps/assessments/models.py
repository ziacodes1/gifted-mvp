from django.conf import settings
from django.db import models


class Assessment(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "assessments_assessment"

    def __str__(self) -> str:
        return self.title


class AssessmentSection(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "assessments_section"
        ordering = ["order", "id"]
        unique_together = ("assessment", "slug")

    def __str__(self) -> str:
        return f"{self.assessment.slug}:{self.slug}"


class SessionStatus(models.TextChoices):
    NOT_STARTED = "NOT_STARTED", "Not started"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    COMPLETED = "COMPLETED", "Completed"


class AssessmentSession(models.Model):
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assessment_sessions"
    )
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="sessions")
    status = models.CharField(
        max_length=16, choices=SessionStatus.choices, default=SessionStatus.IN_PROGRESS
    )
    progress = models.PositiveSmallIntegerField(default=0)  # 0-100
    scoring_version = models.CharField(max_length=20, default="v1")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "assessments_session"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.learner_id}:{self.assessment.slug}:{self.status}"


class AssessmentResponse(models.Model):
    session = models.ForeignKey(AssessmentSession, on_delete=models.CASCADE, related_name="responses")
    question = models.ForeignKey("questions.Question", on_delete=models.CASCADE, related_name="+")
    # Most types pick one option; MULTI_SELECT may pick several.
    selected_options = models.ManyToManyField("questions.QuestionOption", related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "assessments_response"
        unique_together = ("session", "question")

    def __str__(self) -> str:
        return f"{self.session_id}:{self.question_id}"
