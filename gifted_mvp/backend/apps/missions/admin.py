from django.contrib import admin

from .models import Mission, MissionAttempt, MissionSignalMap, MissionStep


class StepInline(admin.StackedInline):
    model = MissionStep
    extra = 0


class MapInline(admin.TabularInline):
    model = MissionSignalMap
    extra = 0


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "difficulty", "estimated_minutes", "is_active")
    inlines = [StepInline, MapInline]


@admin.register(MissionAttempt)
class MissionAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "learner", "mission", "status", "started_at", "completed_at")
    list_filter = ("status",)
