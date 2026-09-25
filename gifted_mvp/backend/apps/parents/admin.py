from django.contrib import admin

from .models import LearnerConnectionCode, ParentChild


@admin.register(ParentChild)
class ParentChildAdmin(admin.ModelAdmin):
    list_display = ("parent", "learner", "relationship", "connected_at")


@admin.register(LearnerConnectionCode)
class LearnerConnectionCodeAdmin(admin.ModelAdmin):
    list_display = ("learner", "code", "created_at")
