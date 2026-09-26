"""Every engagement number lives here — points, caps, streak milestones, badges.

Gifted rewards meaningful growth, not grinding: only whitelisted actions create
activity, AI chat never does, and caps stop repeat actions from farming points.
"""
from dataclasses import dataclass


class EventType:
    ASSESSMENT_COMPLETED = "ASSESSMENT_COMPLETED"
    ASSESSMENT_PROGRESS = "ASSESSMENT_PROGRESS"  # answering questions: an active day, no points
    MISSION_COMPLETED = "MISSION_COMPLETED"
    DIARY_ENTRY_CREATED = "DIARY_ENTRY_CREATED"
    FIRST_DIARY_ENTRY = "FIRST_DIARY_ENTRY"  # one-time bonus
    STREAK_7_DAYS = "STREAK_7_DAYS"  # bonus, once per streak run

    CHOICES = [
        (ASSESSMENT_COMPLETED, "Assessment completed"),
        (ASSESSMENT_PROGRESS, "Assessment progress"),
        (MISSION_COMPLETED, "Mission completed"),
        (DIARY_ENTRY_CREATED, "Diary entry created"),
        (FIRST_DIARY_ENTRY, "First diary entry bonus"),
        (STREAK_7_DAYS, "7-day streak bonus"),
    ]


POINTS = {
    EventType.ASSESSMENT_COMPLETED: 40,  # first completion of each assessment only; retakes 0
    EventType.ASSESSMENT_PROGRESS: 0,
    EventType.MISSION_COMPLETED: 60,
    EventType.DIARY_ENTRY_CREATED: 10,  # first DIARY_POINTS_PER_DAY entries per day only
    EventType.FIRST_DIARY_ENTRY: 15,
    EventType.STREAK_7_DAYS: 30,
}
DIARY_POINTS_PER_DAY = 2
STREAK_BONUS_DAYS = 7

LEADERBOARD_SIZE = 10
PERCENTILE_MIN_ACTIVE = 10  # fewer active learners than this → no percentage is shown
PERCENT_TIERS = (10, 25, 50)


@dataclass(frozen=True)
class Badge:
    key: str
    icon: str  # frontend medallion icon
    tone: str  # green | gold | purple | teal
    metric: str | None  # None = a future feature; always locked for now
    target: int = 1


BADGES = [
    Badge("curious_learner", "leaf", "green", "assessments_completed", 1),
    Badge("consistent_explorer", "star", "gold", "longest_streak", 7),
    Badge("diary_champion", "book", "purple", "diary_entries", 10),
    Badge("opportunity_seeker", "compass", "green", None),
    Badge("global_thinker", "globe", "teal", "exploration_kinds", 2),  # an assessment + a mission
    Badge("community_contributor", "people", "green", None),
    Badge("ideas_in_action", "bulb", "gold", "missions_completed", 1),
    Badge("future_leader", "mountain", "purple", "longest_streak", 30),
    Badge("gifted_explorer", "passport", "teal", None),
]
BADGES_BY_KEY = {b.key: b for b in BADGES}


class RewardType:
    PHYSICAL = "PHYSICAL"
    COURSE = "COURSE"
    EVENT = "EVENT"
    COMMUNITY = "COMMUNITY"
    MENTOR = "MENTOR"

    CHOICES = [(PHYSICAL, "Physical"), (COURSE, "Course"), (EVENT, "Event"), (COMMUNITY, "Community"), (MENTOR, "Mentor")]
