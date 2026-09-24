"""Reusable question content library. Rendering is driven by `type`, not
one hardcoded page per question — see frontend QuestionRenderer.
"""
from django.db import models


class QuestionType(models.TextChoices):
    SINGLE_CHOICE = "SINGLE_CHOICE", "Single choice"  # legacy v1
    VISUAL_CHOICE = "VISUAL_CHOICE", "Visual choice (image cards)"
    STORY_CHOICE = "STORY_CHOICE", "Story choice (short text options)"
    SCENARIO_CHOICE = "SCENARIO_CHOICE", "Situational choice (scenario card)"
    VALUE_TRADEOFF = "VALUE_TRADEOFF", "Values trade-off (two options)"
    MULTI_SELECT = "MULTI_SELECT", "Multi-select"
    PATTERN_CHOICE = "PATTERN_CHOICE", "Reasoning puzzle"


MULTI_SELECT_TYPES = {QuestionType.MULTI_SELECT}


class Question(models.Model):
    section = models.ForeignKey(
        "assessments.AssessmentSection", on_delete=models.CASCADE, related_name="questions"
    )
    type = models.CharField(
        max_length=32, choices=QuestionType.choices, default=QuestionType.SINGLE_CHOICE
    )
    prompt = models.CharField(max_length=255)
    helper_text = models.CharField(max_length=255, blank=True)
    # Type-specific presentation data (scenario text, puzzle stimulus, min/max picks).
    content = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "questions_question"
        ordering = ["section__order", "order", "id"]

    def __str__(self) -> str:
        return self.prompt


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    label = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=8, blank=True)  # single emoji glyph
    image = models.CharField(max_length=100, blank=True)  # frontend asset key, e.g. "interest_art_painting_girl_canvas_studio"
    content = models.JSONField(default=dict, blank=True)  # e.g. puzzle glyph spec, {"exclusive": true}
    value = models.SlugField(max_length=50)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "questions_option"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.question_id}:{self.label}"
