from django.contrib import admin, messages
from django.db.models import Count

from common.admin.locking import LockedContentAdmin, LockedInlineMixin, ReadOnlyAdmin

from .models import Assessment, AssessmentSection, AssessmentSession
from .versioning import create_new_version, publish_version


class AssessmentSectionInline(LockedInlineMixin, admin.TabularInline):
    model = AssessmentSection
    extra = 0
    fields = ("order", "slug", "title", "translations")


@admin.register(Assessment)
class AssessmentAdmin(LockedContentAdmin):
    list_display = ("title", "slug", "version", "is_active", "locked", "session_count")
    list_filter = ("is_active",)
    search_fields = ("title", "slug")
    inlines = [AssessmentSectionInline]
    actions = ["new_draft_version", "publish"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_sessions=Count("sessions"))

    @admin.display(boolean=True, description="Locked")
    def locked(self, obj):
        return obj._sessions > 0

    @admin.display(description="Sessions", ordering="_sessions")
    def session_count(self, obj):
        return obj._sessions

    @admin.action(description="Create new draft version (copy content, inactive)")
    def new_draft_version(self, request, queryset):
        for assessment in queryset:
            new = create_new_version(assessment)
            messages.success(request, f"Created draft {new.slug} (v{new.version}). Edit it, then publish.")

    @admin.action(description="Publish selected version (activate it, deactivate other versions)")
    def publish(self, request, queryset):
        if queryset.count() != 1:
            messages.error(request, "Publish exactly one version at a time.")
            return
        publish_version(queryset.get())
        messages.success(request, "Published. New sessions use this version; old sessions keep theirs.")


@admin.register(AssessmentSession)
class AssessmentSessionAdmin(ReadOnlyAdmin):
    """Metadata only — raw answers (AssessmentResponse) are intentionally not in admin."""

    list_display = ("id", "learner", "assessment", "assessment_version", "scoring_version", "status", "progress", "started_at", "completed_at")
    list_filter = ("status", "assessment", "scoring_version")
    fields = ("learner", "assessment", "assessment_version", "scoring_version", "status", "progress", "started_at", "completed_at", "result_snapshot")
