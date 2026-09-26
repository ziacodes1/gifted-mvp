from django.contrib import admin

from common.admin.locking import ReadOnlyAdmin

from .models import Evidence, SignalEvidence


class SignalEvidenceInline(admin.TabularInline):
    model = SignalEvidence
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Evidence)
class EvidenceAdmin(ReadOnlyAdmin):
    list_display = ("id", "learner", "source_type", "source_id", "title", "created_at")
    list_filter = ("source_type",)
    fields = ("learner", "source_type", "source_id", "title", "description", "created_at")
    inlines = [SignalEvidenceInline]
