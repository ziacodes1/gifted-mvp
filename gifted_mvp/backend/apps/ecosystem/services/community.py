"""Community circles: membership, moderated posts, reports, events.

Safety rules (tested):
- only signed-in students take part; no anonymous posting, no DMs, no followers;
- every new post waits for moderation (PENDING) and is visible only to its author until approved;
- any learner can report an approved post; REPORT_REVIEW_THRESHOLD open reports send it back
  to moderation automatically; staff approve/reject/delete in Django admin;
- names are shown as "First L." (or "Gifted learner"), never emails;
- posts are never translated, never sent to an AI provider and never shown to parents.
"""
from __future__ import annotations

from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone

from common.i18n import tr

from apps.engagement.services import safe_display_name

from ..models import (
    CommunityCircle,
    CommunityEvent,
    CommunityMembership,
    CommunityPost,
    CommunityReport,
    ModerationStatus,
    PostType,
    ReportReason,
)
from .catalog import organization_summary
from .matching import CLEAR, EMERGING, Profile, learner_profile

REPORT_REVIEW_THRESHOLD = 3
FEED_SIZE = 30
EVENTS_SIZE = 5
SUGGESTED_SIZE = 3
POST_MIN, POST_MAX = 3, 1000


class CommunityError(Exception):
    def __init__(self, detail: str, status: int = 400):
        super().__init__(detail)
        self.status = status


def _circles():
    return CommunityCircle.objects.filter(active=True).annotate(member_count=Count("memberships"))


def circle_card(c: CommunityCircle, joined: set[int], reason: dict | None = None) -> dict:
    return {
        "slug": c.slug,
        "name": tr(c, "name"),
        "description": tr(c, "description"),
        "category": c.category,
        "cover_key": c.cover_key,
        "icon_key": c.icon_key,
        "member_count": c.member_count,  # real count of memberships
        "joined": c.id in joined,
        "reason": reason,
    }


def suggest_circles(profile: Profile, circles: list[CommunityCircle], joined: set[int]) -> list[tuple]:
    """Deterministic: circles whose target signals the learner shows (clear first, then
    emerging), ordered by the learner's score. Without signals: the admin order."""
    open_circles = [c for c in circles if c.id not in joined]
    if not profile.has_signals:
        return [(c, None) for c in open_circles[:SUGGESTED_SIZE]]
    scored = []
    for c in open_circles:
        hits = [k for k in (c.target_signals or []) if profile.scores.get(k, 0) >= EMERGING]
        if hits:
            best = max(hits, key=lambda k: (profile.scores[k], k))
            code = "interest" if profile.scores[best] >= CLEAR else "emerging"
            scored.append((-profile.scores[best], c.order, c.id, c, {"code": code, "signal": best, "label": profile.labels[best]}))
    scored.sort(key=lambda t: t[:3])
    picks = [(c, reason) for *_, c, reason in scored[:SUGGESTED_SIZE]]
    if len(picks) < SUGGESTED_SIZE:  # top up with circles to try, clearly without a reason
        chosen = {c.id for c, _ in picks}
        picks += [(c, None) for c in open_circles if c.id not in chosen][: SUGGESTED_SIZE - len(picks)]
    return picks


def _post_row(p: CommunityPost, learner) -> dict:
    mine = p.author_id == learner.id
    return {
        "id": p.id,
        "author": "you" if mine else None,
        "author_name": safe_display_name(p.author),  # None → "Gifted learner" in the UI
        "circle": {"slug": p.circle.slug, "name": tr(p.circle, "name")},
        "body": p.body,  # shown as written; never translated
        "post_type": p.post_type,
        "status": p.moderation_status,
        "mine": mine,
        "created_at": p.created_at.isoformat(),
    }


def feed(learner, circle: CommunityCircle | None = None) -> list[dict]:
    reported = CommunityReport.objects.filter(reporter=learner).values_list("post_id", flat=True)
    approved = CommunityPost.objects.filter(moderation_status=ModerationStatus.APPROVED, circle__active=True).exclude(
        id__in=reported
    )
    own = CommunityPost.objects.filter(author=learner, circle__active=True).exclude(
        moderation_status=ModerationStatus.APPROVED
    )
    if circle is not None:
        approved, own = approved.filter(circle=circle), own.filter(circle=circle)
    posts = (approved | own).select_related("author", "circle").order_by("-created_at")[:FEED_SIZE]
    return [_post_row(p, learner) for p in posts]


def event_row(e: CommunityEvent) -> dict:
    return {
        "id": e.id,
        "title": tr(e, "title"),
        "description": tr(e, "description"),
        "start_at": e.start_at.isoformat(),
        "end_at": e.end_at.isoformat() if e.end_at else None,
        "mode": e.mode,
        "location": tr(e, "location"),
        "external_url": e.external_url,
        "circle": {"slug": e.circle.slug, "name": tr(e.circle, "name")} if e.circle else None,
        "organization": organization_summary(e.organization) if e.organization else None,
    }


def upcoming_events(now=None) -> list[dict]:
    now = now or timezone.now()
    events = (
        CommunityEvent.objects.filter(active=True, start_at__gte=now)
        .select_related("circle", "organization")
        .order_by("start_at")[:EVENTS_SIZE]
    )
    return [event_row(e) for e in events]


def overview(learner) -> dict:
    profile = learner_profile(learner)
    circles = list(_circles())
    joined = set(CommunityMembership.objects.filter(learner=learner).values_list("circle_id", flat=True))
    return {
        "has_signals": profile.has_signals,
        "suggested": [circle_card(c, joined, reason) for c, reason in suggest_circles(profile, circles, joined)],
        "my_circles": [circle_card(c, joined) for c in circles if c.id in joined],
        "circles": [circle_card(c, joined) for c in circles],
        "feed": feed(learner),
        "events": upcoming_events(),
    }


def get_circle(slug: str) -> CommunityCircle:
    return _circles().get(slug=slug)


def circle_detail(learner, circle: CommunityCircle) -> dict:
    joined = set(CommunityMembership.objects.filter(learner=learner, circle=circle).values_list("circle_id", flat=True))
    events = circle.events.filter(active=True, start_at__gte=timezone.now()).select_related("circle", "organization")
    return {
        **circle_card(circle, joined),
        "feed": feed(learner, circle),
        "events": [event_row(e) for e in events[:EVENTS_SIZE]],
    }


def join(learner, circle: CommunityCircle) -> None:
    CommunityMembership.objects.get_or_create(learner=learner, circle=circle)


def leave(learner, circle: CommunityCircle) -> None:
    CommunityMembership.objects.filter(learner=learner, circle=circle).delete()


def create_post(learner, circle: CommunityCircle, body: str, post_type: str = PostType.SHARE) -> CommunityPost:
    body = (body or "").strip()
    if not CommunityMembership.objects.filter(learner=learner, circle=circle).exists():
        raise CommunityError("Join this circle to post in it.", 403)
    if not POST_MIN <= len(body) <= POST_MAX:
        raise CommunityError(f"Posts are {POST_MIN}–{POST_MAX} characters.")
    if post_type not in PostType.values:
        raise CommunityError("Unknown post type.")
    return CommunityPost.objects.create(circle=circle, author=learner, body=body, post_type=post_type)


@transaction.atomic
def report_post(learner, post_id: int, reason: str = ReportReason.OTHER) -> None:
    post = (
        CommunityPost.objects.select_for_update()
        .filter(id=post_id, moderation_status=ModerationStatus.APPROVED, circle__active=True)
        .first()
    )
    if post is None:
        raise CommunityError("Post not found.", 404)
    if post.author_id == learner.id:
        raise CommunityError("You can't report your own post.")
    if reason not in ReportReason.values:
        reason = ReportReason.OTHER
    try:
        with transaction.atomic():
            CommunityReport.objects.create(post=post, reporter=learner, reason=reason)
    except IntegrityError:
        return  # already reported by this learner: idempotent
    if post.reports.filter(resolved=False).count() >= REPORT_REVIEW_THRESHOLD:
        post.moderation_status = ModerationStatus.PENDING
        post.save(update_fields=["moderation_status", "updated_at"])
