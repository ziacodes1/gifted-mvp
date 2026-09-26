from django.contrib import admin

from common.admin.locking import LockedContentAdmin, ReadOnlyAdmin

from .models import LearnerSignal, ResponseSignalMap, Signal


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("key", "label")


@admin.register(ResponseSignalMap)
class ResponseSignalMapAdmin(LockedContentAdmin):
    """Scoring rules table. Locked for assessment versions that learners have taken."""

    list_display = ("option", "signal", "weight")
    list_filter = ("signal__category", "option__question__section__assessment")
    search_fields = ("option__label", "signal__key")
    autocomplete_fields = ("signal",)


@admin.register(LearnerSignal)
class LearnerSignalAdmin(ReadOnlyAdmin):
    list_display = ("learner", "signal", "score", "confidence", "evidence_count", "opportunity_count", "updated_at")
    list_filter = ("signal__category", "confidence")
