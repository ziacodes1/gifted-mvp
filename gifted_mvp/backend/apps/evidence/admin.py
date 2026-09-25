from django.contrib import admin

from .models import Evidence, SignalEvidence


class SignalEvidenceInline(admin.TabularInline):
    model = SignalEvidence
    extra = 0


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("id", "learner", "source_type", "source_id", "title", "created_at")
    list_filter = ("source_type",)
    inlines = [SignalEvidenceInline]
