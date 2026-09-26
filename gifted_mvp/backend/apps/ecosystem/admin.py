"""Ecosystem content management + community moderation.

Learner interaction rows (bookmarks, progress, saved/opened opportunities, memberships) are not
registered: staff see aggregate counts on the catalog pages instead. Posts are registered because
they must be moderated; they are learner-to-learner content by design (never diary/Companion).
"""
from django.contrib import admin, messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import (
    CommunityCircle,
    CommunityEvent,
    CommunityPost,
    CommunityReport,
    LearningPath,
    LearningPathItem,
    ModerationStatus,
    Opportunity,
    Organization,
    Resource,
)

TRANSLATIONS_HELP = 'Uzbek/Russian overrides: {"uz": {"title": "..."}, "ru": {"title": "..."}}'


class ActivateMixin:
    actions = ["activate", "deactivate", "feature", "unfeature"]

    @admin.action(description="Activate")
    def activate(self, request, queryset):
        messages.success(request, f"{queryset.update(active=True)} activated.")

    @admin.action(description="Deactivate (hide from students)")
    def deactivate(self, request, queryset):
        messages.success(request, f"{queryset.update(active=False)} deactivated.")

    @admin.action(description="Feature")
    def feature(self, request, queryset):
        messages.success(request, f"{queryset.update(featured=True)} featured.")

    @admin.action(description="Unfeature")
    def unfeature(self, request, queryset):
        messages.success(request, f"{queryset.update(featured=False)} unfeatured.")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "organization_type", "city", "country", "verified", "is_demo", "active", "n_resources", "n_opportunities")
    list_filter = ("organization_type", "verified", "is_demo", "active", "country")
    list_editable = ("verified", "active")
    search_fields = ("name", "slug", "city", "country")
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _r=Count("resources", distinct=True), _o=Count("opportunities", distinct=True)
        )

    @admin.display(description="Resources", ordering="_r")
    def n_resources(self, obj):
        return obj._r

    @admin.display(description="Opportunities", ordering="_o")
    def n_opportunities(self, obj):
        return obj._o


@admin.register(Resource)
class ResourceAdmin(ActivateMixin, admin.ModelAdmin):
    list_display = ("title", "resource_type", "category", "organization", "duration_minutes", "difficulty", "featured", "active", "order", "completions")
    list_filter = ("resource_type", "category", "difficulty", "featured", "active", "produces_evidence", "organization")
    list_editable = ("featured", "active", "order")
    search_fields = ("title", "slug", "short_description", "organization__name")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("organization", "title", "slug", "short_description", "resource_type", "category", "difficulty", "duration_minutes")}),
        ("Content", {"fields": ("cover_key", "external_url", "content"),
                     "description": 'Leave the URL empty for content shown inside Gifted: {"intro": "...", "points": ["..."], "try_this": "..."}'}),
        ("Matching (deterministic)", {"fields": ("target_signals", "target_exposure", "age_min", "age_max"),
                                      "description": "Signal keys, e.g. [\"investigative\", \"problem_solving\"]; exposure keys, e.g. [\"exp_science\"]."}),
        ("Evidence", {"fields": ("produces_evidence", "evidence_signals"),
                      "description": "Only when checked: completing it records light EXPOSURE evidence for these signal keys."}),
        ("Publishing", {"fields": ("featured", "active", "order", "metadata")}),
        ("Translations", {"fields": ("translations",), "description": TRANSLATIONS_HELP}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _done=Count("learner_states", filter=Q(learner_states__status="COMPLETED"))
        )

    @admin.display(description="Completed by", ordering="_done")
    def completions(self, obj):
        return obj._done


class LearningPathItemInline(admin.TabularInline):
    model = LearningPathItem
    extra = 1
    autocomplete_fields = ("resource",)
    ordering = ("order",)


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "organization", "difficulty", "featured", "active")
    list_filter = ("category", "featured", "active")
    list_editable = ("featured", "active")
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [LearningPathItemInline]


@admin.register(Opportunity)
class OpportunityAdmin(ActivateMixin, admin.ModelAdmin):
    list_display = ("title", "opportunity_type", "category", "mode", "organization", "application_deadline", "featured", "active", "saves", "link_opens")
    list_filter = ("opportunity_type", "category", "mode", "global_available", "featured", "active", "country", "organization")
    list_editable = ("application_deadline", "featured", "active")
    search_fields = ("title", "slug", "short_description", "organization__name", "city", "country")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "application_deadline"
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("organization", "title", "slug", "opportunity_type", "category", "short_description", "description")}),
        ("Where & when", {"fields": ("mode", "city", "country", "global_available", "application_open_at", "application_deadline", "program_start", "program_end")}),
        ("Application", {"fields": ("application_url",),
                         "description": "The provider's page. Gifted only records that a learner opened it — never an application."}),
        ("Eligibility & details", {"fields": ("age_min", "age_max", "eligibility", "skills", "faqs"),
                                   "description": 'eligibility/skills: ["..."]; faqs: [{"q": "...", "a": "..."}]'}),
        ("Matching (deterministic)", {"fields": ("target_signals", "target_exposure")}),
        ("Publishing", {"fields": ("cover_key", "featured", "active", "metadata")}),
        ("Translations", {"fields": ("translations",), "description": TRANSLATIONS_HELP}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _saves=Count("learner_states", filter=Q(learner_states__saved=True)),
            _opens=Count("learner_states", filter=Q(learner_states__link_opened_at__isnull=False)),
        )

    @admin.display(description="Saved by", ordering="_saves")
    def saves(self, obj):
        return obj._saves

    @admin.display(description="Opened apply link", ordering="_opens")
    def link_opens(self, obj):
        return obj._opens


@admin.register(CommunityCircle)
class CommunityCircleAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "active", "order", "members", "pending_posts")
    list_filter = ("category", "active")
    list_editable = ("active", "order")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _m=Count("memberships", distinct=True),
            _p=Count("posts", filter=Q(posts__moderation_status=ModerationStatus.PENDING), distinct=True),
        )

    @admin.display(description="Members", ordering="_m")
    def members(self, obj):
        return obj._m

    @admin.display(description="Pending posts", ordering="_p")
    def pending_posts(self, obj):
        return obj._p


@admin.register(CommunityEvent)
class CommunityEventAdmin(admin.ModelAdmin):
    list_display = ("title", "start_at", "mode", "circle", "organization", "active")
    list_filter = ("mode", "active", "circle")
    list_editable = ("active",)
    search_fields = ("title", "location")
    date_hierarchy = "start_at"


class ReportInline(admin.TabularInline):
    model = CommunityReport
    extra = 0
    fields = ("reason", "resolved", "created_at")
    readonly_fields = ("reason", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    """Moderation queue. New posts are PENDING; approve to publish, reject to hide, or delete."""

    list_display = ("id", "circle", "author", "post_type", "short_body", "moderation_status", "open_reports", "created_at")
    list_filter = ("moderation_status", "circle", "post_type")
    search_fields = ("body", "author__email")
    readonly_fields = ("circle", "author", "body", "post_type", "created_at", "moderated_at")
    fields = ("circle", "author", "post_type", "body", "moderation_status", "moderated_at", "created_at")
    inlines = [ReportInline]
    actions = ["approve", "reject"]

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("circle", "author").annotate(
            _reports=Count("reports", filter=Q(reports__resolved=False))
        )

    def save_model(self, request, obj, form, change):
        if "moderation_status" in form.changed_data:
            obj.moderated_at = timezone.now()
            if obj.moderation_status != ModerationStatus.PENDING:
                obj.reports.update(resolved=True)
        super().save_model(request, obj, form, change)

    @admin.display(description="Post")
    def short_body(self, obj):
        return obj.body[:80]

    @admin.display(description="Open reports", ordering="_reports")
    def open_reports(self, obj):
        return obj._reports

    def _moderate(self, request, queryset, status):
        ids = list(queryset.values_list("id", flat=True))
        n = CommunityPost.objects.filter(id__in=ids).update(moderation_status=status, moderated_at=timezone.now())
        CommunityReport.objects.filter(post_id__in=ids).update(resolved=True)
        messages.success(request, f"{n} post(s) set to {status.label.lower()}.")

    @admin.action(description="Approve (publish)")
    def approve(self, request, queryset):
        self._moderate(request, queryset, ModerationStatus.APPROVED)

    @admin.action(description="Reject / hide")
    def reject(self, request, queryset):
        self._moderate(request, queryset, ModerationStatus.REJECTED)


@admin.register(CommunityReport)
class CommunityReportAdmin(admin.ModelAdmin):
    list_display = ("post", "reason", "resolved", "created_at")
    list_filter = ("reason", "resolved")
    readonly_fields = ("post", "reporter", "reason", "created_at")
    list_editable = ("resolved",)

    def has_add_permission(self, request):
        return False
