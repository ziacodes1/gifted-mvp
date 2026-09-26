"""Ecosystem: the organizations around a learner and what they offer.

    Organization ─┬─ Resource ── LearningPath (ordered items)
                  ├─ Opportunity
                  └─ CommunityEvent            CommunityCircle ─ Membership / Post / Report

Catalog rows (organizations, resources, paths, opportunities, circles, events) are content,
managed in Django admin and translated through the `translations` JSON field (see
common.i18n). Learner rows (`LearnerResource`, `LearnerOpportunity`, memberships, posts,
reports) only record *interaction state* — Gifted never claims a learner applied somewhere,
only that they opened the provider's link.

Matching against the Passport is deterministic (services.matching); there is no score and no
AI call. Structure for partner billing/sponsorship is intentionally absent: `Organization`
is the anchor such features would hang off later.
"""
from django.conf import settings
from django.db import models


class OrganizationType(models.TextChoices):
    EDUCATION_CENTER = "EDUCATION_CENTER", "Education center"
    UNIVERSITY = "UNIVERSITY", "University"
    NGO = "NGO", "NGO"
    COMPANY = "COMPANY", "Company"
    COMMUNITY = "COMMUNITY", "Community"
    FOUNDATION = "FOUNDATION", "Foundation"
    GOVERNMENT = "GOVERNMENT", "Government"
    OTHER = "OTHER", "Other"


class Category(models.TextChoices):
    """Shared topic vocabulary for resources, opportunities and circles."""

    STEM = "STEM", "STEM"
    AI_TECH = "AI_TECH", "AI & Technology"
    ARTS = "ARTS", "Arts & Creativity"
    LEADERSHIP = "LEADERSHIP", "Leadership"
    ENTREPRENEURSHIP = "ENTREPRENEURSHIP", "Entrepreneurship"
    SOCIAL_IMPACT = "SOCIAL_IMPACT", "Social Impact"
    ENVIRONMENT = "ENVIRONMENT", "Environment"
    LANGUAGES = "LANGUAGES", "Languages"
    PERSONAL_DEVELOPMENT = "PERSONAL_DEVELOPMENT", "Personal Development"


class Difficulty(models.TextChoices):
    BEGINNER = "BEGINNER", "Beginner"
    INTERMEDIATE = "INTERMEDIATE", "Intermediate"
    ADVANCED = "ADVANCED", "Advanced"


def _list():
    return []


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(TimeStamped):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=80, unique=True)
    organization_type = models.CharField(max_length=20, choices=OrganizationType.choices, default=OrganizationType.OTHER)
    short_description = models.CharField(max_length=300, blank=True)
    logo_key = models.CharField(max_length=60, blank=True, help_text="Frontend image key (optional).")
    website_url = models.URLField(blank=True)
    country = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, blank=True)
    verified = models.BooleanField(default=False, help_text="Identity checked by the Gifted team.")
    # Demo seeds use fictional organizations; the UI labels their content as demo content so
    # nobody mistakes it for a real partnership.
    is_demo = models.BooleanField(default=False, help_text="Fictional organization used for demos.")
    active = models.BooleanField(default=True)
    translations = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ecosystem_organization"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Matchable(models.Model):
    """Deterministic targeting shared by resources and opportunities (see services.matching).

    `target_signals`: interest / work-style / value / aptitude signal keys this item suits.
    `target_exposure`: exposure signal keys it gives first-hand experience of.
    """

    target_signals = models.JSONField(default=_list, blank=True)
    target_exposure = models.JSONField(default=_list, blank=True)
    age_min = models.PositiveSmallIntegerField(null=True, blank=True)
    age_max = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        abstract = True


class ResourceType(models.TextChoices):
    ARTICLE = "ARTICLE", "Article"
    VIDEO = "VIDEO", "Video"
    TOOLKIT = "TOOLKIT", "Toolkit"
    COURSE = "COURSE", "Course"


class Resource(TimeStamped, Matchable):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="resources")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    short_description = models.CharField(max_length=400)
    resource_type = models.CharField(max_length=10, choices=ResourceType.choices)
    category = models.CharField(max_length=24, choices=Category.choices)
    cover_key = models.CharField(max_length=60, blank=True, help_text="Frontend cover image key.")
    external_url = models.URLField(blank=True, help_text="Provider page. Empty = content is shown inside Gifted.")
    # In-Gifted content: {"intro": str, "points": [str], "try_this": str}
    content = models.JSONField(default=dict, blank=True)
    duration_minutes = models.PositiveSmallIntegerField(default=10)
    difficulty = models.CharField(max_length=12, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    # Evidence is opt-in per resource: completing it records EXPOSURE evidence for these keys.
    produces_evidence = models.BooleanField(default=False)
    evidence_signals = models.JSONField(default=_list, blank=True)
    featured = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    translations = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ecosystem_resource"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title


class LearningPath(TimeStamped):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="learning_paths")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    category = models.CharField(max_length=24, choices=Category.choices)
    cover_key = models.CharField(max_length=60, blank=True)
    difficulty = models.CharField(max_length=12, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    featured = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    translations = models.JSONField(default=dict, blank=True)
    resources = models.ManyToManyField(Resource, through="LearningPathItem", related_name="paths")

    class Meta:
        db_table = "ecosystem_learning_path"
        ordering = ["-featured", "id"]

    def __str__(self) -> str:
        return self.title


class LearningPathItem(models.Model):
    path = models.ForeignKey(LearningPath, on_delete=models.CASCADE, related_name="items")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="path_items")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "ecosystem_learning_path_item"
        ordering = ["order", "id"]
        constraints = [models.UniqueConstraint(fields=["path", "resource"], name="uniq_path_resource")]


class ProgressStatus(models.TextChoices):
    NOT_STARTED = "NOT_STARTED", "Not started"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    COMPLETED = "COMPLETED", "Completed"


class LearnerResource(models.Model):
    """A learner's bookmark + progress for one resource (no content, no answers)."""

    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ecosystem_resources")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="learner_states")
    saved = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=ProgressStatus.choices, default=ProgressStatus.NOT_STARTED)
    opened_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ecosystem_learner_resource"
        constraints = [models.UniqueConstraint(fields=["learner", "resource"], name="uniq_learner_resource")]


class OpportunityType(models.TextChoices):
    COMPETITION = "COMPETITION", "Competition"
    HACKATHON = "HACKATHON", "Hackathon"
    FELLOWSHIP = "FELLOWSHIP", "Fellowship"
    CAMP = "CAMP", "Camp"
    SCHOLARSHIP = "SCHOLARSHIP", "Scholarship"
    EVENT = "EVENT", "Event"
    INTERNSHIP = "INTERNSHIP", "Internship"
    VOLUNTEERING = "VOLUNTEERING", "Volunteering"
    PROGRAM = "PROGRAM", "Program"
    WORKSHOP = "WORKSHOP", "Workshop"


class Mode(models.TextChoices):
    ONLINE = "ONLINE", "Online"
    IN_PERSON = "IN_PERSON", "In person"
    HYBRID = "HYBRID", "Hybrid"


class Opportunity(TimeStamped, Matchable):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="opportunities")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    short_description = models.CharField(max_length=400)
    description = models.TextField(blank=True)
    opportunity_type = models.CharField(max_length=14, choices=OpportunityType.choices)
    category = models.CharField(max_length=24, choices=Category.choices)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.ONLINE)
    city = models.CharField(max_length=80, blank=True)
    country = models.CharField(max_length=80, blank=True)
    global_available = models.BooleanField(default=False, help_text="Open to learners from any country.")
    application_open_at = models.DateField(null=True, blank=True)
    application_deadline = models.DateField(null=True, blank=True, help_text="Empty = rolling / no deadline.")
    program_start = models.DateField(null=True, blank=True)
    program_end = models.DateField(null=True, blank=True)
    application_url = models.URLField(help_text="The provider's own application page (Gifted never submits applications).")
    cover_key = models.CharField(max_length=60, blank=True)
    skills = models.JSONField(default=_list, blank=True)  # [str]
    eligibility = models.JSONField(default=_list, blank=True)  # [str] requirements as written by the provider
    faqs = models.JSONField(default=_list, blank=True)  # [{"q": str, "a": str}]
    featured = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    translations = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ecosystem_opportunity"
        ordering = ["application_deadline", "id"]
        verbose_name_plural = "opportunities"

    def __str__(self) -> str:
        return self.title


class LearnerOpportunity(models.Model):
    """Privacy-safe interaction state. `link_opened_at` means the learner opened the
    provider's application page — never that they applied."""

    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ecosystem_opportunities")
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="learner_states")
    saved = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)
    link_opened_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ecosystem_learner_opportunity"
        constraints = [models.UniqueConstraint(fields=["learner", "opportunity"], name="uniq_learner_opportunity")]

    @property
    def state(self) -> str:
        if self.link_opened_at:
            return "APPLICATION_LINK_OPENED"
        if self.saved:
            return "SAVED"
        return "VIEWED" if self.viewed_at else "NONE"


# --- Community ------------------------------------------------------------------------------


class CommunityCircle(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=60, unique=True)
    description = models.CharField(max_length=300)
    category = models.CharField(max_length=24, choices=Category.choices)
    cover_key = models.CharField(max_length=60, blank=True)
    icon_key = models.CharField(max_length=40, blank=True)
    target_signals = models.JSONField(default=_list, blank=True)  # used for suggestions only
    active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)
    translations = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ecosystem_community_circle"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.name


class CommunityMembership(models.Model):
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="circle_memberships")
    circle = models.ForeignKey(CommunityCircle, on_delete=models.CASCADE, related_name="memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ecosystem_community_membership"
        constraints = [models.UniqueConstraint(fields=["learner", "circle"], name="uniq_circle_membership")]


class PostType(models.TextChoices):
    SHARE = "SHARE", "Share"
    QUESTION = "QUESTION", "Question"
    IDEA = "IDEA", "Idea"
    ACHIEVEMENT = "ACHIEVEMENT", "Achievement"


class ModerationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected / hidden"


class CommunityPost(models.Model):
    """Learner-written, shown to other learners only after moderation. Never translated,
    never sent to an AI provider, never shown to parents."""

    circle = models.ForeignKey(CommunityCircle, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="community_posts")
    body = models.TextField(max_length=1000)
    post_type = models.CharField(max_length=12, choices=PostType.choices, default=PostType.SHARE)
    moderation_status = models.CharField(
        max_length=10, choices=ModerationStatus.choices, default=ModerationStatus.PENDING, db_index=True
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ecosystem_community_post"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"#{self.pk} in {self.circle_id} ({self.moderation_status})"


class ReportReason(models.TextChoices):
    UNKIND = "UNKIND", "Unkind or bullying"
    UNSAFE = "UNSAFE", "Unsafe or personal information"
    SPAM = "SPAM", "Spam or advertising"
    OTHER = "OTHER", "Something else"


class CommunityReport(models.Model):
    post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="community_reports")
    reason = models.CharField(max_length=10, choices=ReportReason.choices, default=ReportReason.OTHER)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ecosystem_community_report"
        constraints = [models.UniqueConstraint(fields=["post", "reporter"], name="uniq_post_report")]


class CommunityEvent(TimeStamped):
    circle = models.ForeignKey(CommunityCircle, on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=400, blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.ONLINE)
    location = models.CharField(max_length=120, blank=True)
    external_url = models.URLField(blank=True)
    active = models.BooleanField(default=True)
    translations = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ecosystem_community_event"
        ordering = ["start_at"]

    def __str__(self) -> str:
        return self.title
