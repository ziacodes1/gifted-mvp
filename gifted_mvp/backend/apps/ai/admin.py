from django.contrib import admin

from .models import AIInsight


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ("id", "learner", "session", "generation_type", "source", "model", "created_at")
    list_filter = ("generation_type", "source")
    readonly_fields = ("created_at", "updated_at")
