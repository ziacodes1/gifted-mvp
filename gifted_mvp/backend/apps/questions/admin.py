from django.contrib import admin

from apps.signals.models import ResponseSignalMap
from common.admin.locking import LockedContentAdmin, LockedInlineMixin

from .models import Question, QuestionOption


class QuestionOptionInline(LockedInlineMixin, admin.TabularInline):
    model = QuestionOption
    extra = 0
    fields = ("order", "value", "label", "description", "icon", "image", "content", "translations")
    show_change_link = True  # → option page with its signal mappings


@admin.register(Question)
class QuestionAdmin(LockedContentAdmin):
    list_display = ("prompt", "section", "type", "order", "is_active")
    list_filter = ("type", "is_active", "section__assessment")
    search_fields = ("prompt",)
    inlines = [QuestionOptionInline]


class ResponseSignalMapInline(LockedInlineMixin, admin.TabularInline):
    model = ResponseSignalMap
    extra = 0
    autocomplete_fields = ("signal",)


@admin.register(QuestionOption)
class QuestionOptionAdmin(LockedContentAdmin):
    """Where the deterministic scoring rules live: option → signal (+ weight)."""

    list_display = ("label", "question", "value", "order")
    list_filter = ("question__section__assessment", "question__type")
    search_fields = ("label", "value", "question__prompt")
    inlines = [ResponseSignalMapInline]
