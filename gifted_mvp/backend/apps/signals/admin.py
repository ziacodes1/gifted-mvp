from django.contrib import admin

from .models import LearnerSignal, ResponseSignalMap, Signal


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "category", "is_active")
    list_filter = ("category",)


admin.site.register(ResponseSignalMap)


@admin.register(LearnerSignal)
class LearnerSignalAdmin(admin.ModelAdmin):
    list_display = ("learner", "signal", "score", "confidence", "evidence_count", "updated_at")
    list_filter = ("signal__category",)
