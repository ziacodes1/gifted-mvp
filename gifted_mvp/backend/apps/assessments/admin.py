from django.contrib import admin

from .models import Assessment, AssessmentResponse, AssessmentSection, AssessmentSession


class AssessmentSectionInline(admin.TabularInline):
    model = AssessmentSection
    extra = 0


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_active")
    inlines = [AssessmentSectionInline]


@admin.register(AssessmentSession)
class AssessmentSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "learner", "assessment", "status", "progress", "started_at")
    list_filter = ("status", "assessment")


admin.site.register(AssessmentResponse)
