"""Today: Spark selection, motivation and in-app nudges — deterministic, no AI call.

Inputs (never private content): assessment status, mission status/date, Passport stage,
streak, and diary *count + dates*. Diary text/mood/tags and Companion messages are never
read here (tested: changing them changes nothing).

Stability: the day's pick is stored in `DailySpark`; refreshing returns the same card. It is
re-picked only when the learner completes what it asked for (e.g. starts the assessment or
writes a diary page), and then the new pick is seeded differently.
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.assessments.models import AssessmentSession, SessionStatus
from apps.diary.models import DiaryEntry
from apps.engagement.models import ActivityEvent, StudentBadge
from apps.engagement.rules import BADGES_BY_KEY, EventType
from apps.engagement.services import local_day, points_summary, record_activity, reward_list, streak_stats
from apps.evidence.models import Evidence, EvidenceSource
from apps.missions.models import AttemptStatus, MissionAttempt
from apps.missions.services import featured_mission

from .catalog import (
    DIARY_MILESTONES,
    DIARY_NUDGE_AFTER_DAYS,
    FACT_COUNT,
    MINI_CHALLENGE_POINTS,
    NUDGE_WINDOW_DAYS,
    RECENT_DAYS,
    SPARKS,
    SparkType,
    spark_for,
)
from .models import DailySpark, NudgeState, SparkStatus

# --- Learner state ---------------------------------------------------------------------


def learner_state(learner, today: date) -> dict:
    session = AssessmentSession.objects.filter(learner=learner).order_by("-started_at").values("status").first()
    completed = AssessmentSession.objects.filter(learner=learner, status=SessionStatus.COMPLETED).exists()
    assessment = "COMPLETED" if completed else (session["status"] if session else "NOT_STARTED")

    mission = featured_mission()
    attempt = MissionAttempt.objects.filter(learner=learner, mission=mission).first() if mission else None
    mission_done_on = local_day(attempt.completed_at) if attempt and attempt.status == AttemptStatus.COMPLETED else None

    # Diary: count and dates only.
    diary_dates = list(DiaryEntry.objects.filter(learner=learner).order_by("created_at").values_list("created_at", flat=True))
    last_diary_day = local_day(diary_dates[-1]) if diary_dates else None

    streak = streak_stats(learner, today)
    return {
        "assessment": assessment,
        "mission": attempt.status if attempt else "NOT_STARTED",
        "mission_slug": mission.slug if mission else None,
        "mission_done_recently": bool(mission_done_on and (today - mission_done_on).days <= RECENT_DAYS),
        "diary_count": len(diary_dates),
        "diary_dates": diary_dates,
        "diary_today": last_diary_day == today,
        "days_since_diary": (today - last_diary_day).days if last_diary_day else None,
        "streak": streak,
    }


# --- Selection ---------------------------------------------------------------------------


def _seed(*parts) -> int:
    return int(hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()[:12], 16)


def candidates(state: dict) -> list[tuple[str, int]]:
    """(spark key, weight). After today's meaningful action only lighter content is offered."""
    reflections = [s.key for s in SPARKS if s.type == SparkType.REFLECTION]
    challenges = [s.key for s in SPARKS if s.type == SparkType.MINI_CHALLENGE]
    if state["streak"]["active_today"]:
        return [(k, 2) for k in reflections] + [("fact", 4), ("cp_plan_week", 1)]

    out: list[tuple[str, int]] = []
    if state["assessment"] == "NOT_STARTED":
        out.append(("ns_start_discovery", 8))
    elif state["assessment"] == "IN_PROGRESS":
        out.append(("ns_continue_assessment", 8))
    else:
        if state["mission"] != AttemptStatus.COMPLETED and state["mission_slug"]:
            out.append(("mn_try_mission", 6))
        out.append(("cp_interests", 2))
    if state["mission_done_recently"]:
        out.append(("ns_passport_updated", 5))
    if state["diary_count"] == 0:
        out.append(("dp_first_page", 3))
    elif state["days_since_diary"] is not None and state["days_since_diary"] >= DIARY_NUDGE_AFTER_DAYS:
        out.append(("dp_come_back", 4))
    near_bonus = 4 <= state["streak"]["current"] <= 6
    out += [(k, 2 if near_bonus else 1) for k in challenges]
    out += [(k, 1) for k in reflections] + [("fact", 2), ("cp_plan_week", 1)]
    return out


def pick(learner, day: date, state: dict, exclude: set[str], salt: str = "") -> str:
    pool = [(k, w) for k, w in candidates(state) if k not in exclude] or [("fact", 1)]
    n = _seed(learner.id, day.isoformat(), salt) % sum(w for _, w in pool)
    for key, weight in pool:
        if n < weight:
            break
        n -= weight
    if key == "fact":
        key = f"fact_{_seed('fact', learner.id, day.isoformat(), salt) % FACT_COUNT:02d}"
    return key


def resolved(key: str, state: dict) -> bool:
    """The learner did what this spark asked for → it may be replaced by a lighter one."""
    return {
        "ns_start_discovery": state["assessment"] != "NOT_STARTED",
        "ns_continue_assessment": state["assessment"] == "COMPLETED",
        "mn_try_mission": state["mission"] == AttemptStatus.COMPLETED,
        "dp_first_page": state["diary_today"],
        "dp_come_back": state["diary_today"],
    }.get(key, False)


def todays_spark(learner, state: dict, today: date) -> DailySpark:
    yesterday = DailySpark.objects.filter(learner=learner, day=today - timedelta(days=1)).values_list("spark_key", flat=True).first()
    with transaction.atomic():
        row = DailySpark.objects.select_for_update().filter(learner=learner, day=today).first()
        if row is None:
            try:
                with transaction.atomic():
                    row = DailySpark.objects.create(
                        learner=learner, day=today, spark_key=pick(learner, today, state, {yesterday} if yesterday else set())
                    )
            except IntegrityError:  # concurrent first load
                row = DailySpark.objects.get(learner=learner, day=today)
        elif row.status == SparkStatus.NEW and resolved(row.spark_key, state):
            row.spark_key = pick(learner, today, state, {row.spark_key, yesterday or ""}, salt=row.spark_key)
            row.save(update_fields=["spark_key", "updated_at"])
    return row


def spark_payload(row: DailySpark, state: dict) -> dict:
    spark = spark_for(row.spark_key)
    route = spark.route
    target = state["mission_slug"] if route == "mission" else None
    return {
        "key": row.spark_key,
        "type": spark.type,
        "status": row.status,
        "route": route,
        "target": target,
        "actions": list(spark.actions),
        "fact_index": int(row.spark_key.split("_")[1]) if spark.type == SparkType.FACT else None,
        "points": MINI_CHALLENGE_POINTS if spark.type == SparkType.MINI_CHALLENGE else 0,
    }


# --- Motivation -------------------------------------------------------------------------------


def motivation(learner, state: dict, today: date) -> str:
    """One localized message key picked from what is true for the learner (never guilt)."""
    s = state["streak"]
    options = []
    if s["had_streak_before"]:
        options.append("welcome_back")
    if state["mission_done_recently"]:
        options.append("curiosity_to_evidence")
    if s["current"] >= 2:
        options.append("momentum")
    if 4 <= s["current"] <= 6 and not s["active_today"]:
        options.append("near_bonus")
    if state["diary_count"] >= 3:
        options.append("story_growing")
    if s["active_today"]:
        options.append("done_today")
    if state["assessment"] == "NOT_STARTED":
        options.append("first_step")
    if not options:
        options.append("small_steps")
    if "welcome_back" in options:
        return "welcome_back"  # always greet a returning learner kindly first
    return options[_seed("motivation", learner.id, today.isoformat()) % len(options)]


# --- Nudges ------------------------------------------------------------------------------------


def _tz():
    return ZoneInfo(settings.ACTIVITY_TIME_ZONE)


def nudges(learner, state: dict, today: date, spark: DailySpark) -> list[dict]:
    """In-app only, from real state. Newest first."""
    now = timezone.now()
    window = now - timedelta(days=NUDGE_WINDOW_DAYS)
    items: list[dict] = []
    if spark.status == SparkStatus.NEW:
        items.append({"kind": "spark", "params": {}, "to": "/app", "at": datetime.combine(today, time.min, tzinfo=_tz())})
    for key, at in StudentBadge.objects.filter(learner=learner, unlocked_at__gte=window).values_list("badge_key", "unlocked_at"):
        if key in BADGES_BY_KEY:
            items.append({"kind": "badge", "params": {"badge": key}, "to": "/app/rewards", "at": at})
    evidence_at = (
        Evidence.objects.filter(learner=learner, created_at__gte=window)
        .exclude(source_type=EvidenceSource.ASSESSMENT)
        .order_by("-created_at")
        .values_list("created_at", flat=True)
        .first()
    )
    if evidence_at:
        items.append({"kind": "passport", "params": {}, "to": "/app/passport", "at": evidence_at})
    count = state["diary_count"]
    reached = [m for m in DIARY_MILESTONES if m <= count]
    if reached and state["diary_dates"][reached[-1] - 1] >= window:
        items.append({"kind": "diary_milestone", "params": {"count": reached[-1]}, "to": "/app/diary", "at": state["diary_dates"][reached[-1] - 1]})
    points = points_summary(learner, today)
    affordable = [r for r in reward_list(learner, points["available"]) if r["can_redeem"]]
    if affordable:
        last_points_at = ActivityEvent.objects.filter(learner=learner, points__gt=0).order_by("-created_at").values_list("created_at", flat=True).first()
        items.append({"kind": "reward", "params": {"count": len(affordable)}, "to": "/app/rewards", "at": last_points_at or now})
    items.sort(key=lambda i: i["at"], reverse=True)
    return items


# --- Read model / actions -------------------------------------------------------------------------


def today_overview(learner) -> dict:
    today = local_day()
    state = learner_state(learner, today)
    row = todays_spark(learner, state, today)
    items = nudges(learner, state, today, row)
    seen = NudgeState.objects.filter(learner=learner).values_list("seen_at", flat=True).first()
    return {
        "day": today,
        "spark": spark_payload(row, state),
        "motivation": motivation(learner, state, today),
        "nudges": [{**i, "unread": seen is None or i["at"] > seen} for i in items],
        "unread": sum(1 for i in items if seen is None or i["at"] > seen),
    }


class SparkActionError(Exception):
    """code: not_today | not_completable"""


def set_spark_status(learner, spark_key: str, status: str) -> DailySpark:
    """DONE (mini challenges only; idempotent, +5 once a day) · DISMISSED · NEW (undo dismiss)."""
    today = local_day()
    with transaction.atomic():
        row = DailySpark.objects.select_for_update().filter(learner=learner, day=today, spark_key=spark_key).first()
        if row is None:
            raise SparkActionError("not_today")
        if status == SparkStatus.DONE:
            if spark_for(spark_key).type != SparkType.MINI_CHALLENGE:
                raise SparkActionError("not_completable")
            if row.status != SparkStatus.DONE:
                row.status = SparkStatus.DONE
                row.save(update_fields=["status", "updated_at"])
        elif row.status != SparkStatus.DONE:  # a completed challenge can't be un-done
            row.status = status
            row.save(update_fields=["status", "updated_at"])
    if row.status == SparkStatus.DONE:
        record_activity(learner, EventType.MINI_CHALLENGE, f"challenge:{today.isoformat()}")
    return row


def mark_nudges_seen(learner) -> None:
    NudgeState.objects.update_or_create(learner=learner, defaults={"seen_at": timezone.now()})
