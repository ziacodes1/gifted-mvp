from django.contrib import admin

from common.admin.locking import ReadOnlyAdmin

from .models import Mission, MissionAttempt, MissionSignalMap, MissionStep


class StepInline(admin.StackedInline):
    model = MissionStep
    extra = 0
    fields = ("order", "key", "type", "title", "prompt", "content", "translations")


class MapInline(admin.TabularInline):
    """Deterministic evidence rules (never shown to learners)."""

    model = MissionSignalMap
    extra = 0


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    """Mission content + evidence rules. Evidence is recorded (frozen) when an attempt completes,
    so rule edits only affect future completions."""

    list_display = ("title", "slug", "difficulty", "estimated_minutes", "is_active", "order")
    list_filter = ("is_active", "difficulty")
    search_fields = ("title", "slug")
    inlines = [StepInline, MapInline]


@admin.register(MissionAttempt)
class MissionAttemptAdmin(ReadOnlyAdmin):
    """Status only — step responses and reflection text (MissionResponse) are not in admin."""

    list_display = ("id", "learner", "mission", "status", "started_at", "completed_at")
    list_filter = ("status", "mission")
    fields = ("learner", "mission", "status", "started_at", "completed_at")
