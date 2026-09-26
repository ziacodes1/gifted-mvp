"""Admin helpers for versioned assessment content: a version that learners have already taken
is shown read-only (edit a new draft version instead — see apps.assessments.versioning)."""
from django.contrib import admin, messages

from apps.assessments.versioning import assessment_of

LOCKED_HELP = "Locked: learners have taken this assessment version. Use “Create new draft version” on the assessment to change content."


def is_locked(obj) -> bool:
    assessment = assessment_of(obj) if obj is not None else None
    return bool(assessment and assessment.is_locked)


class LockedContentAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if is_locked(obj):
            return [f.name for f in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        return not is_locked(obj) and super().has_delete_permission(request, obj)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, object_id)
        if is_locked(obj):
            messages.info(request, LOCKED_HELP)
        return super().change_view(request, object_id, form_url, extra_context)


class LockedInlineMixin:
    """For inlines: `obj` is the parent object being edited."""

    def has_add_permission(self, request, obj=None):
        return not is_locked(obj) and super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return not is_locked(obj) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return not is_locked(obj) and super().has_delete_permission(request, obj)


class ReadOnlyAdmin(admin.ModelAdmin):
    """Operational/learner records: visible for support, never edited by hand."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
