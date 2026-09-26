"""Engagement service layer — one deterministic activity pipeline.

`record_activity` is the only way activity (and therefore points, streaks and badges) is
created. It is idempotent per (learner, event_type, source_key). Other domains call it with
an id-based key and nothing else — the diary passes "entry:<id>", never text, mood, tags or
photos. AI Companion messages never create activity.

Points available = points earned − points spent on redemptions; earned points (and so the
weekly leaderboard) are never reduced.
"""
from __future__ import annotations

import logging
import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Count, Min, Q, Sum
from django.utils import timezone

from common.i18n import current_language, tr

from .models import ActivityEvent, RedemptionStatus, Reward, RewardRedemption, StudentBadge
from .rules import (
    BADGES,
    DIARY_POINTS_PER_DAY,
    LEADERBOARD_SIZE,
    PERCENT_TIERS,
    PERCENTILE_MIN_ACTIVE,
    POINTS,
    STREAK_BONUS_DAYS,
    EventType,
)

logger = logging.getLogger(__name__)


# --- Days -------------------------------------------------------------------------


def local_day(moment: datetime | None = None) -> date:
    moment = moment or timezone.now()
    return timezone.localtime(moment, ZoneInfo(settings.ACTIVITY_TIME_ZONE)).date()


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())  # Monday


# --- Recording -----------------------------------------------------------------------


def _points_for(learner, event_type: str, source_key: str, day: date) -> int:
    base = POINTS[event_type]
    if not base:
        return 0
    events = ActivityEvent.objects.filter(learner=learner, event_type=event_type, points__gt=0)
    if event_type == EventType.ASSESSMENT_COMPLETED:
        # "assessment:<id>:session:<id>" — only the first completion of an assessment earns points.
        prefix = source_key.split(":session:")[0] + ":"
        return 0 if events.filter(source_key__startswith=prefix).exists() else base
    if event_type == EventType.DIARY_ENTRY_CREATED:
        return base if events.filter(occurred_on=day).count() < DIARY_POINTS_PER_DAY else 0
    return base


def _create_event(learner, event_type: str, source_key: str, day: date) -> tuple[ActivityEvent, bool]:
    existing = ActivityEvent.objects.filter(learner=learner, event_type=event_type, source_key=source_key).first()
    if existing:
        return existing, False
    try:
        with transaction.atomic():
            return (
                ActivityEvent.objects.create(
                    learner=learner,
                    event_type=event_type,
                    source_key=source_key,
                    points=_points_for(learner, event_type, source_key, day),
                    occurred_on=day,
                ),
                True,
            )
    except IntegrityError:  # the same action recorded concurrently
        return ActivityEvent.objects.get(learner=learner, event_type=event_type, source_key=source_key), False


def record_activity(learner, event_type: str, source_key: str, at: datetime | None = None) -> tuple[ActivityEvent, bool]:
    """Idempotent. Records one meaningful action, then applies bonuses and badges."""
    if event_type not in POINTS:
        raise ValueError(f"unknown event type {event_type}")
    day = local_day(at)
    event, created = _create_event(learner, event_type, source_key, day)
    if created:
        if event_type == EventType.DIARY_ENTRY_CREATED:
            _create_event(learner, EventType.FIRST_DIARY_ENTRY, "first", day)
        award_streak_bonuses(learner)
        evaluate_badges(learner)
    return event, created


def safe_record(learner, event_type: str, source_key: str, at: datetime | None = None) -> None:
    """For hooks in other domains: engagement must never break the action itself."""
    try:
        record_activity(learner, event_type, source_key, at)
    except Exception:  # noqa: BLE001
        logger.exception("engagement record failed type=%s", event_type)


# --- Streaks -----------------------------------------------------------------------------


def active_days(learner) -> list[date]:
    return sorted(set(ActivityEvent.objects.filter(learner=learner).values_list("occurred_on", flat=True)))


def _runs(days: list[date]) -> list[tuple[date, date]]:
    """Consecutive-day runs as (start, end)."""
    runs: list[tuple[date, date]] = []
    for d in days:
        if runs and d - runs[-1][1] == timedelta(days=1):
            runs[-1] = (runs[-1][0], d)
        else:
            runs.append((d, d))
    return runs


def streak_stats(learner, today: date | None = None) -> dict:
    """current: consecutive active days ending today — or yesterday, so the streak stays alive
    until the day is over. longest: best run ever (never lost)."""
    today = today or local_day()
    days = active_days(learner)
    runs = _runs(days)
    longest = max(((e - s).days + 1 for s, e in runs), default=0)
    current = 0
    if runs and runs[-1][1] >= today - timedelta(days=1):
        start, end = runs[-1]
        current = (end - start).days + 1
    day_set = set(days)
    monday = week_start(today)
    week = [
        {"date": monday + timedelta(days=i), "active": (monday + timedelta(days=i)) in day_set, "future": monday + timedelta(days=i) > today}
        for i in range(7)
    ]
    return {
        "current": current,
        "longest": longest,
        "active_today": today in day_set,
        "week": week,
        "active_days_this_week": sum(d["active"] for d in week),
        "bonus_days": STREAK_BONUS_DAYS,
        "bonus_points": POINTS[EventType.STREAK_7_DAYS],
        "had_streak_before": longest > 0 and current == 0,
    }


def award_streak_bonuses(learner) -> None:
    """+30 once per run that reaches 7 days, dated on its 7th day. A run already holding a bonus
    never gets another (even if backfilled activity later moves its start earlier)."""
    bonuses = ActivityEvent.objects.filter(learner=learner, event_type=EventType.STREAK_7_DAYS)
    for start, end in _runs(active_days(learner)):
        if (end - start).days + 1 >= STREAK_BONUS_DAYS and not bonuses.filter(occurred_on__range=(start, end)).exists():
            day = start + timedelta(days=STREAK_BONUS_DAYS - 1)
            _create_event(learner, EventType.STREAK_7_DAYS, f"run:{start.isoformat()}", day)


# --- Badges -------------------------------------------------------------------------------


def _metrics(learner) -> dict:
    counts = dict(
        ActivityEvent.objects.filter(learner=learner)
        .values_list("event_type")
        .annotate(n=Count("id"))
        .values_list("event_type", "n")
    )
    assessments = counts.get(EventType.ASSESSMENT_COMPLETED, 0)
    missions = counts.get(EventType.MISSION_COMPLETED, 0)
    return {
        "assessments_completed": assessments,
        "missions_completed": missions,
        "diary_entries": counts.get(EventType.DIARY_ENTRY_CREATED, 0),
        "longest_streak": streak_stats(learner)["longest"],
        "exploration_kinds": int(assessments > 0) + int(missions > 0),
    }


def evaluate_badges(learner) -> None:
    metrics = _metrics(learner)
    have = set(StudentBadge.objects.filter(learner=learner).values_list("badge_key", flat=True))
    for badge in BADGES:
        if badge.metric and badge.key not in have and metrics[badge.metric] >= badge.target:
            StudentBadge.objects.get_or_create(learner=learner, badge_key=badge.key)


def badge_list(learner) -> list[dict]:
    metrics = _metrics(learner)
    unlocked = dict(StudentBadge.objects.filter(learner=learner).values_list("badge_key", "unlocked_at"))
    return [
        {
            "key": b.key,
            "icon": b.icon,
            "tone": b.tone,
            "available": b.metric is not None,
            "unlocked": b.key in unlocked,
            "unlocked_at": unlocked.get(b.key),
            "progress": {"current": min(metrics[b.metric], b.target), "target": b.target} if b.metric else None,
        }
        for b in BADGES
    ]


# --- Points ----------------------------------------------------------------------------------


def points_summary(learner, today: date | None = None) -> dict:
    today = today or local_day()
    agg = ActivityEvent.objects.filter(learner=learner).aggregate(
        earned=Sum("points"), week=Sum("points", filter=Q(occurred_on__gte=week_start(today), occurred_on__lte=today))
    )
    spent = (
        RewardRedemption.objects.filter(learner=learner)
        .exclude(status=RedemptionStatus.CANCELLED)
        .aggregate(s=Sum("points_spent"))["s"]
        or 0
    )
    earned = agg["earned"] or 0
    return {"total_earned": earned, "available": earned - spent, "spent": spent, "this_week": agg["week"] or 0}


# --- Leaderboard ------------------------------------------------------------------------------


def safe_display_name(user) -> str | None:
    """First name + last initial ("Aziza Y."). Never the email. None → the UI shows "Gifted learner"."""
    parts = (user.full_name or "").split()
    if not parts:
        return None
    return f"{parts[0]} {parts[-1][0]}." if len(parts) > 1 else parts[0]


def leaderboard(learner, today: date | None = None) -> dict:
    """This week's (Mon–Sun, learner-local) earned points among active student accounts."""
    today = today or local_day()
    monday = week_start(today)
    rows = list(
        ActivityEvent.objects.filter(
            occurred_on__gte=monday,
            occurred_on__lte=today,
            learner__role="STUDENT",
            learner__is_active=True,
        )
        .values("learner_id")
        .annotate(points=Sum("points"), first=Min("created_at"))
        .filter(points__gt=0)
        .order_by("-points", "first", "learner_id")
    )
    ranked, rank, prev = [], 0, None
    for i, row in enumerate(rows, start=1):
        if row["points"] != prev:
            rank, prev = i, row["points"]
        ranked.append({**row, "rank": rank})

    users = {u.id: u for u in get_user_model().objects.filter(id__in=[r["learner_id"] for r in ranked[:LEADERBOARD_SIZE]] + [learner.id])}

    def public(row):
        return {
            "rank": row["rank"],
            "display_name": safe_display_name(users[row["learner_id"]]),
            "weekly_points": row["points"],
            "is_me": row["learner_id"] == learner.id,
        }

    mine = next((r for r in ranked if r["learner_id"] == learner.id), None)
    return {
        "week_start": monday,
        "top": [public(r) for r in ranked[:LEADERBOARD_SIZE]],
        "me": public(mine) if mine else {"rank": None, "display_name": safe_display_name(learner), "weekly_points": 0, "is_me": True},
        "active_learners": len(ranked),
    }


def standing(board: dict) -> dict:
    """Top-percent card. A percentage only with enough active learners — never fabricated."""
    me, total = board["me"], board["active_learners"]
    if not me["rank"]:
        return {"kind": "not_yet", "percent": None}
    if total >= PERCENTILE_MIN_ACTIVE:
        pct = math.ceil(me["rank"] / total * 100)
        tier = next((t for t in PERCENT_TIERS if pct <= t), None)
        return {"kind": "top_percent", "percent": tier} if tier else {"kind": "keep_going", "percent": None}
    return {"kind": "most_active" if me["rank"] <= 3 else "keep_going", "percent": None}


# --- Rewards ------------------------------------------------------------------------------------


class RedemptionError(Exception):
    """code: inactive | already_redeemed | out_of_stock | not_enough_points"""


def _stock_left(reward: Reward) -> int | None:
    if reward.stock is None:
        return None
    used = reward.redemptions.exclude(status=RedemptionStatus.CANCELLED).count()
    return max(reward.stock - used, 0)


def reward_list(learner, available: int, language: str | None = None) -> list[dict]:
    language = language or current_language()
    mine = set(
        RewardRedemption.objects.filter(learner=learner).exclude(status=RedemptionStatus.CANCELLED).values_list("reward_id", flat=True)
    )
    out = []
    for r in Reward.objects.filter(active=True):
        stock_left = _stock_left(r)
        redeemed = r.id in mine
        out.append(
            {
                "key": r.key,
                "title": tr(r, "title", language),
                "description": tr(r, "description", language),
                "points_required": r.points_required,
                "reward_type": r.reward_type,
                "image_key": r.image_key,
                "stock_left": stock_left,
                "redeemed": redeemed,
                "points_missing": max(r.points_required - available, 0),
                "can_redeem": not (redeemed and r.one_per_learner) and stock_left != 0 and available >= r.points_required,
            }
        )
    return out


def redeem(learner, reward_key: str) -> RewardRedemption:
    """Checks active / one-time / stock / available points under row locks, then reserves."""
    User = get_user_model()
    with transaction.atomic():
        User.objects.select_for_update().only("id").get(pk=learner.pk)  # one redemption at a time per learner
        reward = Reward.objects.select_for_update().filter(key=reward_key).first()
        if reward is None or not reward.active:
            raise RedemptionError("inactive")
        if reward.one_per_learner and RewardRedemption.objects.filter(learner=learner, reward=reward).exclude(
            status=RedemptionStatus.CANCELLED
        ).exists():
            raise RedemptionError("already_redeemed")
        if _stock_left(reward) == 0:
            raise RedemptionError("out_of_stock")
        if points_summary(learner)["available"] < reward.points_required:
            raise RedemptionError("not_enough_points")
        return RewardRedemption.objects.create(learner=learner, reward=reward, points_spent=reward.points_required)


# --- Backfill -------------------------------------------------------------------------------------


def backfill_learner(learner) -> int:
    """Derive missing events for actions completed before engagement existed (or missed by a
    hook). Idempotent: keys match the live hooks, so nothing is ever awarded twice. Reads ids
    and timestamps only — never diary or chat content."""
    from apps.assessments.models import AssessmentResponse, AssessmentSession, SessionStatus
    from apps.diary.models import DiaryEntry
    from apps.missions.models import AttemptStatus, MissionAttempt

    items: list[tuple[datetime, str, str]] = []
    for sid, aid, done in AssessmentSession.objects.filter(learner=learner, status=SessionStatus.COMPLETED).values_list(
        "id", "assessment_id", "completed_at"
    ):
        items.append((done, EventType.ASSESSMENT_COMPLETED, f"assessment:{aid}:session:{sid}"))
    for sid, created in AssessmentResponse.objects.filter(session__learner=learner).values_list("session_id", "created_at"):
        items.append((created, EventType.ASSESSMENT_PROGRESS, f"session:{sid}:day:{local_day(created).isoformat()}"))
    for aid, done in MissionAttempt.objects.filter(learner=learner, status=AttemptStatus.COMPLETED).values_list("id", "completed_at"):
        items.append((done, EventType.MISSION_COMPLETED, f"attempt:{aid}"))
    for eid, created in DiaryEntry.objects.filter(learner=learner).values_list("id", "created_at"):
        items.append((created, EventType.DIARY_ENTRY_CREATED, f"entry:{eid}"))

    created_count = 0
    for at, event_type, key in sorted((i for i in items if i[0]), key=lambda i: i[0]):
        _, created = _create_event(learner, event_type, key, local_day(at))
        created_count += created
        if created and event_type == EventType.DIARY_ENTRY_CREATED:
            _create_event(learner, EventType.FIRST_DIARY_ENTRY, "first", local_day(at))
    award_streak_bonuses(learner)
    evaluate_badges(learner)
    return created_count


# --- Read model ------------------------------------------------------------------------------------


def overview(learner, language: str | None = None) -> dict:
    today = local_day()
    points = points_summary(learner, today)
    board = leaderboard(learner, today)
    recent = list(ActivityEvent.objects.filter(learner=learner).exclude(event_type=EventType.ASSESSMENT_PROGRESS)[:6])
    return {
        "today": today,
        "points": points,
        "streak": streak_stats(learner, today),
        "badges": badge_list(learner),
        "leaderboard": board,
        "standing": standing(board),
        "rewards": reward_list(learner, points["available"], language),
        "redemptions": [
            {"reward_key": r.reward.key, "status": r.status, "points_spent": r.points_spent, "created_at": r.created_at}
            for r in RewardRedemption.objects.filter(learner=learner).select_related("reward")[:10]
        ],
        "recent_activity": [{"type": e.event_type, "points": e.points, "date": e.occurred_on} for e in recent],
    }
