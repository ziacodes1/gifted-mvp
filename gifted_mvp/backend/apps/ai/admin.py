from common.admin.locking import ReadOnlyAdmin
from django.contrib import admin

from .models import AIInsight


@admin.register(AIInsight)
class AIInsightAdmin(ReadOnlyAdmin):
    """Traceability view: which provider/model/prompt/schema produced each saved insight, how long
    it took, and why a fallback was used. The result is the AI *interpretation* (no learner text)."""

    list_display = (
        "id", "learner", "generation_type", "language", "source", "provider", "model",
        "prompt_version", "schema_version", "input_version", "latency_ms", "failure_reason", "created_at",
    )
    list_filter = ("generation_type", "source", "language", "provider", "prompt_version")
