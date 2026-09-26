from django.contrib import admin, messages

from common.admin.locking import ReadOnlyAdmin

from .models import ActivityEvent, RedemptionStatus, Reward, RewardRedemption, StudentBadge


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    """Rewards catalog: titles, costs, stock and availability are managed here (the seed only
    provides defaults). `image_key` must match an artwork key shipped with the frontend."""

    list_display = ("title", "key", "reward_type", "points_required", "stock", "active", "order")
    list_filter = ("reward_type", "active")
    list_editable = ("points_required", "stock", "active", "order")
    search_fields = ("title", "key")


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    """Fulfilment queue: the team marks reserved rewards as fulfilled (or cancels them, which
    returns the points to `available`). Nothing else about a redemption is editable."""

    list_display = ("id", "learner", "reward", "points_spent", "status", "created_at")
    list_filter = ("status", "reward")
    readonly_fields = ("learner", "reward", "points_spent", "created_at")
    fields = ("learner", "reward", "points_spent", "status", "created_at")
    actions = ["mark_fulfilled", "mark_cancelled"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Mark as fulfilled")
    def mark_fulfilled(self, request, queryset):
        n = queryset.filter(status=RedemptionStatus.RESERVED).update(status=RedemptionStatus.FULFILLED)
        messages.success(request, f"{n} redemption(s) marked fulfilled.")

    @admin.action(description="Cancel (returns the points)")
    def mark_cancelled(self, request, queryset):
        n = queryset.filter(status=RedemptionStatus.RESERVED).update(status=RedemptionStatus.CANCELLED)
        messages.success(request, f"{n} redemption(s) cancelled.")


@admin.register(ActivityEvent)
class ActivityEventAdmin(ReadOnlyAdmin):
    """Content-free by design: type, id-based key, points, day."""

    list_display = ("learner", "event_type", "points", "occurred_on", "source_key")
    list_filter = ("event_type",)


@admin.register(StudentBadge)
class StudentBadgeAdmin(ReadOnlyAdmin):
    list_display = ("learner", "badge_key", "unlocked_at")
    list_filter = ("badge_key",)
