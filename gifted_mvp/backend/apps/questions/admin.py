from django.contrib import admin

from .models import Question, QuestionOption


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("prompt", "section", "type", "order", "is_active")
    list_filter = ("type", "is_active", "section__assessment")
    inlines = [QuestionOptionInline]
