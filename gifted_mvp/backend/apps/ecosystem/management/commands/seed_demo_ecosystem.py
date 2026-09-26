"""Seed the demo ecosystem catalog + demo community activity (idempotent).

Organizations are fictional (`is_demo=True`); see `_ecosystem_data.py`. Re-running updates the
catalog in place (by slug) and moves dates relative to today, so deadlines and upcoming events
stay meaningful. Learner interaction rows of real learners are never touched.
"""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.ecosystem.models import (
    CommunityCircle,
    CommunityEvent,
    CommunityMembership,
    CommunityPost,
    LearningPath,
    LearningPathItem,
    ModerationStatus,
    Opportunity,
    Organization,
    Resource,
)
from apps.engagement.services import local_day

from ._ecosystem_data import CIRCLES, EVENTS, LEARNING_PATH, MEMBERS, OPPORTUNITIES, ORGANIZATIONS, POSTS, RESOURCES


def _peer(i: int) -> User | None:
    return User.objects.filter(email=f"peer{i}@peers.gifted.demo").first()


class Command(BaseCommand):
    help = "Seed demo organizations, resources, learning path, opportunities and community (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        today = local_day()
        orgs = {}
        for spec in ORGANIZATIONS:
            spec = dict(spec)
            loc = spec.pop("loc")
            translations = {
                lang: {"short_description": spec.pop(lang)["short_description"], **loc[lang]} for lang in ("uz", "ru")
            }
            slug = spec.pop("slug")
            orgs[slug], _ = Organization.objects.update_or_create(
                slug=slug, defaults={**spec, "is_demo": True, "active": True, "translations": translations}
            )

        resources = {}
        for spec in RESOURCES:
            spec = dict(spec)
            spec["organization"] = orgs[spec["organization"]]
            slug = spec.pop("slug")
            resources[slug], _ = Resource.objects.update_or_create(
                slug=slug, defaults={**spec, "active": True}
            )

        spec = dict(LEARNING_PATH)
        items = spec.pop("items")
        spec["organization"] = orgs[spec["organization"]]
        path, _ = LearningPath.objects.update_or_create(slug=spec.pop("slug"), defaults={**spec, "active": True})
        LearningPathItem.objects.filter(path=path).exclude(resource__slug__in=items).delete()
        for order, slug in enumerate(items, start=1):
            LearningPathItem.objects.update_or_create(path=path, resource=resources[slug], defaults={"order": order})

        for spec in OPPORTUNITIES:
            spec = dict(spec)
            spec["organization"] = orgs[spec["organization"]]
            deadline, (start, end), opens = spec.pop("deadline_days"), spec.pop("program_days"), spec.pop("open_days")
            day = lambda n: today + timedelta(days=n) if n is not None else None  # noqa: E731
            spec.update(
                application_deadline=day(deadline), program_start=day(start), program_end=day(end),
                application_open_at=day(opens),
            )
            Opportunity.objects.update_or_create(slug=spec.pop("slug"), defaults={**spec, "active": True})

        circles = {}
        for order, (slug, name, category, cover, icon, targets, desc, uz, ru) in enumerate(CIRCLES, start=1):
            circles[slug], _ = CommunityCircle.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name, "category": category, "cover_key": cover, "icon_key": icon, "target_signals": targets,
                    "description": desc, "order": order, "active": True,
                    "translations": {"uz": {"name": uz[0], "description": uz[1]}, "ru": {"name": ru[0], "description": ru[1]}},
                },
            )

        tz = ZoneInfo(settings.ACTIVITY_TIME_ZONE)
        for circle, org, days, hour, hours, mode, en, uz, ru in EVENTS:
            start = datetime.combine(today + timedelta(days=days), time(hour), tzinfo=tz)
            CommunityEvent.objects.update_or_create(
                title=en[0],
                defaults={
                    "circle": circles[circle], "organization": orgs.get(org), "description": en[1], "location": en[2],
                    "start_at": start, "end_at": start + timedelta(hours=hours), "mode": mode, "active": True,
                    "translations": {
                        "uz": {"title": uz[0], "description": uz[1], "location": uz[2]},
                        "ru": {"title": ru[0], "description": ru[1], "location": ru[2]},
                    },
                },
            )

        peers = 0
        for slug, members in MEMBERS.items():
            for i in members:
                if (user := _peer(i)) is not None:
                    CommunityMembership.objects.get_or_create(learner=user, circle=circles[slug])
                    peers += 1
        now = timezone.now()
        posts = 0
        for i, circle, post_type, hours_ago, body in POSTS:
            if (user := _peer(i)) is None:
                continue
            CommunityMembership.objects.get_or_create(learner=user, circle=circles[circle])
            post, _ = CommunityPost.objects.update_or_create(
                author=user, circle=circles[circle], body=body,
                defaults={"post_type": post_type, "moderation_status": ModerationStatus.APPROVED},
            )
            # Keep demo posts recent relative to the seed run.
            CommunityPost.objects.filter(pk=post.pk).update(
                created_at=now - timedelta(hours=hours_ago), moderated_at=now - timedelta(hours=hours_ago)
            )
            posts += 1

        self.stdout.write(
            f"Seeded ecosystem: {len(orgs)} demo organizations, {len(resources)} resources, 1 learning path, "
            f"{len(OPPORTUNITIES)} opportunities, {len(circles)} circles, {len(EVENTS)} events, {posts} demo posts."
        )
