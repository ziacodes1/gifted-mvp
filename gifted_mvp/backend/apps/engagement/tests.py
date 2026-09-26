import json
import shutil
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.assessments.models import Assessment
from apps.companion.tests import RecordingProvider
from apps.missions.tests import ANSWERS, SLUG

from .models import ActivityEvent, Reward, RewardRedemption, StudentBadge
from .rules import EventType
from .services import (
    _create_event,
    award_streak_bonuses,
    badge_list,
    evaluate_badges,
    leaderboard,
    local_day,
    points_summary,
    record_activity,
    standing,
    streak_stats,
    week_start,
)

User = get_user_model()
DIARY_SECRET = "My very private diary sentence about feelings"


class EngagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        call_command("seed_demo_mission", verbosity=0)
        call_command("seed_demo_engagement", verbosity=0)
        cls.student = User.objects.create_user("kid@test.dev", "pw12345!", full_name="Ada Lovelace")
        cls.parent = User.objects.create_user("mum@test.dev", "pw12345!", role="PARENT", full_name="Mum Parent")

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        o = override_settings(PRIVATE_MEDIA_ROOT=Path(self.media))
        o.enable()
        self.addCleanup(o.disable)
        self.today = local_day()

    def _c(self, user=None):
        c = APIClient()
        c.force_authenticate(user or self.student)
        return c

    def _events(self, user=None, **kw):
        return ActivityEvent.objects.filter(learner=user or self.student, **kw)

    def _assessment(self, user=None):
        c = self._c(user)
        s = c.post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()
        for q in s["questions"]:
            c.post(f"/api/v1/assessment-sessions/{s['id']}/answer/", {"question_id": q["id"], "option_id": q["options"][0]["id"]}, format="json")
        return c.post(f"/api/v1/assessment-sessions/{s['id']}/complete/")

    def _mission(self):
        c = self._c()
        a = c.post(f"/api/v1/missions/{SLUG}/start/").json()
        steps = {s["key"]: s["id"] for s in a["mission"]["steps"]}
        for key, data in ANSWERS.items():
            c.post(f"/api/v1/mission-attempts/{a['id']}/answer/", {"step_id": steps[key], "response": data}, format="json")
        c.post(f"/api/v1/mission-attempts/{a['id']}/complete/")
        c.post(f"/api/v1/mission-attempts/{a['id']}/complete/")  # repeated completion

    def _diary(self, n=1):
        for i in range(n):
            self._c().post("/api/v1/diary/entries/", {"title": f"Day {i}", "body": DIARY_SECRET, "mood": "very_low", "tags": ["private-tag"]}, format="json")

    def _days(self, *offsets, user=None):
        """Activity on today - offset days (explicit dates, so streak maths is exact)."""
        for o in offsets:
            _create_event(user or self.student, EventType.ASSESSMENT_PROGRESS, f"test:{o}", self.today - timedelta(days=o))

    # --- activity pipeline -----------------------------------------------------------

    def test_record_activity_is_idempotent(self):
        for _ in range(3):
            record_activity(self.student, EventType.MISSION_COMPLETED, "attempt:99")
        self.assertEqual(self._events(event_type=EventType.MISSION_COMPLETED).count(), 1)
        self.assertEqual(points_summary(self.student)["total_earned"], 60)

    def test_assessment_points_once_and_retake_gives_activity_not_points(self):
        self.assertEqual(self._assessment().status_code, 200)
        done = self._events(event_type=EventType.ASSESSMENT_COMPLETED)
        self.assertEqual([e.points for e in done], [40])
        self.assertEqual(self._events(event_type=EventType.ASSESSMENT_PROGRESS).count(), 1)  # one per session per day, 0 pts
        self._assessment()  # a retake is a new session
        self.assertEqual(sorted(e.points for e in done.all()), [0, 40])
        self.assertEqual(points_summary(self.student)["total_earned"], 40)

    def test_mission_points_once(self):
        self._mission()
        self.assertEqual(list(self._events(event_type=EventType.MISSION_COMPLETED).values_list("points", flat=True)), [60])

    def test_diary_counts_without_content_and_is_capped_per_day(self):
        self._diary(3)
        diary = self._events(event_type=EventType.DIARY_ENTRY_CREATED).order_by("id")
        self.assertEqual([e.points for e in diary], [10, 10, 0])  # 2 paid entries per day
        self.assertEqual(self._events(event_type=EventType.FIRST_DIARY_ENTRY).get().points, 15)
        self.assertTrue(all(e.source_key.startswith("entry:") for e in diary))
        dumped = json.dumps(list(ActivityEvent.objects.values()), default=str)
        for secret in (DIARY_SECRET, "Day 0", "very_low", "private-tag"):
            self.assertNotIn(secret, dumped)
        self.assertEqual(
            {f.name for f in ActivityEvent._meta.get_fields()},
            {"id", "learner", "event_type", "source_key", "points", "occurred_on", "created_at"},
        )

    def test_companion_chat_and_page_views_give_nothing(self):
        conv = self._c().post("/api/v1/companion/conversations/").json()["id"]
        with mock.patch("apps.ai.services.companion.get_provider", return_value=RecordingProvider()):
            for _ in range(5):
                self._c().post(f"/api/v1/companion/conversations/{conv}/messages/", {"content": "hi", "client_id": str(uuid.uuid4())}, format="json")
        for lang in ("en", "uz", "ru"):
            c = self._c()
            c.credentials(HTTP_ACCEPT_LANGUAGE=lang)
            c.get("/api/v1/engagement/overview/")
            c.get("/api/v1/passport/")
        self.assertEqual(self._events().count(), 0)

    # --- streaks ----------------------------------------------------------------------

    def test_streak_current_longest_and_missed_day(self):
        self._days(0, 1, 2)
        s = streak_stats(self.student, self.today)
        self.assertEqual((s["current"], s["longest"], s["active_today"]), (3, 3, True))

        # Yesterday active but not today: the streak is still alive until the day ends.
        s = streak_stats(self.student, self.today + timedelta(days=1))
        self.assertEqual((s["current"], s["active_today"]), (3, False))

        # A missed day resets the current streak but never the longest (or any badge).
        s = streak_stats(self.student, self.today + timedelta(days=2))
        self.assertEqual((s["current"], s["longest"], s["had_streak_before"]), (0, 3, True))

    def test_weekly_consistency(self):
        monday = week_start(self.today)
        offsets = [(self.today - (monday + timedelta(days=i))).days for i in range(self.today.weekday() + 1)]
        self._days(*offsets)
        s = streak_stats(self.student, self.today)
        self.assertEqual(s["active_days_this_week"], self.today.weekday() + 1)
        self.assertEqual([d["future"] for d in s["week"]], [i > self.today.weekday() for i in range(7)])

    def test_seven_day_bonus_once_per_run_and_streak_badges(self):
        self._days(*range(7))
        award_streak_bonuses(self.student)
        award_streak_bonuses(self.student)
        evaluate_badges(self.student)
        bonus = self._events(event_type=EventType.STREAK_7_DAYS)
        self.assertEqual([b.points for b in bonus], [30])
        unlocked = {b["key"] for b in badge_list(self.student) if b["unlocked"]}
        self.assertIn("consistent_explorer", unlocked)
        self.assertNotIn("future_leader", unlocked)

        self._days(*range(7, 30))
        award_streak_bonuses(self.student)
        evaluate_badges(self.student)
        self.assertEqual(self._events(event_type=EventType.STREAK_7_DAYS).count(), 1)  # still one run
        self.assertIn("future_leader", {b["key"] for b in badge_list(self.student) if b["unlocked"]})

    def test_weekly_points_exclude_last_week(self):
        _create_event(self.student, EventType.MISSION_COMPLETED, "old", week_start(self.today) - timedelta(days=1))
        record_activity(self.student, EventType.DIARY_ENTRY_CREATED, "entry:1")
        p = points_summary(self.student)
        self.assertEqual((p["total_earned"], p["this_week"]), (85, 25))

    # --- badges ------------------------------------------------------------------------

    def test_badges_unlock_deterministically_and_future_badges_stay_locked(self):
        badges = {b["key"]: b for b in badge_list(self.student)}
        self.assertEqual(len(badges), 9)
        self.assertFalse(any(b["unlocked"] for b in badges.values()))

        self._assessment()
        self._mission()
        record_activity(self.student, EventType.MISSION_COMPLETED, "attempt:again")
        badges = {b["key"]: b for b in badge_list(self.student)}
        for key in ("curious_learner", "ideas_in_action", "global_thinker"):
            self.assertTrue(badges[key]["unlocked"], key)
            self.assertIsNotNone(badges[key]["unlocked_at"])
        for key in ("opportunity_seeker", "community_contributor", "gifted_explorer"):
            self.assertFalse(badges[key]["unlocked"])
            self.assertFalse(badges[key]["available"])
        self.assertEqual(badges["diary_champion"]["progress"], {"current": 0, "target": 10})
        self.assertEqual(StudentBadge.objects.filter(learner=self.student).count(), 3)

        for i in range(10):
            record_activity(self.student, EventType.DIARY_ENTRY_CREATED, f"entry:{1000 + i}")
        self.assertTrue({b["key"]: b for b in badge_list(self.student)}["diary_champion"]["unlocked"])

    # --- leaderboard -----------------------------------------------------------------------

    def _learner(self, name, points, **extra):
        u = User.objects.create_user(f"{uuid.uuid4().hex[:8]}@test.dev", "pw12345!", full_name=name, **extra)
        _create_event(u, EventType.MISSION_COMPLETED, "x", self.today)
        ActivityEvent.objects.filter(learner=u).update(points=points)
        return u

    def test_leaderboard_ranking_safe_fields_and_own_position(self):
        ActivityEvent.objects.all().delete()  # ignore seeded peers
        for i in range(11):
            self._learner(f"Peer{i} Surname{i}", 500 - i)
        self._learner("Hidden Parent", 9999, role="PARENT")
        self._learner("Gone Student", 9999, is_active=False)
        record_activity(self.student, EventType.DIARY_ENTRY_CREATED, "entry:1")  # 25 this week

        board = self._c().get("/api/v1/engagement/overview/").json()["leaderboard"]
        self.assertEqual(len(board["top"]), 10)
        self.assertEqual(board["top"][0], {"rank": 1, "display_name": "Peer0 S.", "weekly_points": 500, "is_me": False})
        self.assertEqual([r["weekly_points"] for r in board["top"]], sorted((r["weekly_points"] for r in board["top"]), reverse=True))
        self.assertEqual(board["me"], {"rank": 12, "display_name": "Ada L.", "weekly_points": 25, "is_me": True})
        self.assertEqual(board["active_learners"], 12)
        text = json.dumps(board)
        for leak in ("@", "Hidden", "Gone", "Lovelace", "Surname0"):
            self.assertNotIn(leak, text)

    def test_ties_share_a_rank(self):
        ActivityEvent.objects.all().delete()
        self._learner("A One", 100)
        self._learner("B Two", 100)
        self._learner("C Three", 50)
        ranks = [r["rank"] for r in leaderboard(self.student)["top"]]
        self.assertEqual(ranks, [1, 1, 3])

    def test_standing_never_fabricates_a_percentage(self):
        ActivityEvent.objects.all().delete()
        self.assertEqual(standing(leaderboard(self.student))["kind"], "not_yet")
        record_activity(self.student, EventType.MISSION_COMPLETED, "attempt:1")
        self._learner("Other One", 10)
        self.assertEqual(standing(leaderboard(self.student)), {"kind": "most_active", "percent": None})  # 2 learners
        for i in range(10):
            self._learner(f"P{i} Q", 5)
        self.assertEqual(standing(leaderboard(self.student)), {"kind": "top_percent", "percent": 10})  # 1 of 12

    # --- rewards ---------------------------------------------------------------------------------

    def _redeem(self, key):
        return self._c().post(f"/api/v1/engagement/rewards/{key}/redeem/")

    def test_redemption_spends_available_points_only(self):
        self._mission()  # 60
        record_activity(self.student, EventType.DIARY_ENTRY_CREATED, "entry:1")  # 10 + 15
        before_board = leaderboard(self.student)["me"]["weekly_points"]
        r = self._redeem("sticker-pack")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["status"], "RESERVED")
        p = points_summary(self.student)
        self.assertEqual((p["total_earned"], p["available"], p["this_week"]), (85, 35, 85))
        self.assertEqual(leaderboard(self.student)["me"]["weekly_points"], before_board)

        self.assertEqual(self._redeem("sticker-pack").json()["error"]["detail"], "already_redeemed")
        self.assertEqual(self._redeem("notebook").json()["error"]["detail"], "not_enough_points")
        self.assertEqual(self._redeem("no-such-reward").json()["error"]["detail"], "inactive")
        self.assertEqual(RewardRedemption.objects.count(), 1)

        rewards = {r["key"]: r for r in self._c().get("/api/v1/engagement/overview/").json()["rewards"]}
        self.assertTrue(rewards["sticker-pack"]["redeemed"])
        self.assertFalse(rewards["notebook"]["can_redeem"])
        self.assertEqual(rewards["notebook"]["points_missing"], 115)

    def test_stock_is_respected(self):
        Reward.objects.filter(key="sticker-pack").update(stock=1)
        other = self._learner("Rich Kid", 100)
        self.assertEqual(self._c(other).post("/api/v1/engagement/rewards/sticker-pack/redeem/").status_code, 201)
        record_activity(self.student, EventType.MISSION_COMPLETED, "attempt:1")
        self.assertEqual(self._redeem("sticker-pack").json()["error"]["detail"], "out_of_stock")

    def test_rewards_are_localized(self):
        c = self._c()
        c.credentials(HTTP_ACCEPT_LANGUAGE="uz")
        titles = {r["key"]: r["title"] for r in c.get("/api/v1/engagement/overview/").json()["rewards"]}
        self.assertEqual(titles["notebook"], "Gifted daftari")
        self.assertEqual(len(titles), 7)

    # --- access / backfill / seed / reset ------------------------------------------------------------

    def test_roles(self):
        self.assertEqual(self._c(self.parent).get("/api/v1/engagement/overview/").status_code, 403)
        self.assertEqual(self._c(self.parent).post("/api/v1/engagement/rewards/sticker-pack/redeem/").status_code, 403)
        self.assertEqual(APIClient().get("/api/v1/engagement/overview/").status_code, 401)

    def test_backfill_derives_missing_events_once(self):
        self._assessment()
        self._mission()
        self._diary(2)
        earned = points_summary(self.student)["total_earned"]
        self.assertEqual(earned, 40 + 60 + 10 + 10 + 15)
        ActivityEvent.objects.filter(learner=self.student).delete()
        self._c().get("/api/v1/engagement/overview/")
        self._c().get("/api/v1/engagement/overview/")
        self.assertEqual(points_summary(self.student)["total_earned"], earned)
        self.assertEqual(self._events(event_type=EventType.MISSION_COMPLETED).count(), 1)

    def test_seed_is_idempotent_and_reset_clears_demo_engagement(self):
        call_command("seed_demo", verbosity=0)
        counts = (Reward.objects.count(), User.objects.filter(email__endswith="@peers.gifted.demo").count(), ActivityEvent.objects.count())
        call_command("seed_demo", verbosity=0)
        self.assertEqual((Reward.objects.count(), User.objects.filter(email__endswith="@peers.gifted.demo").count(), ActivityEvent.objects.count()), counts)
        self.assertEqual(counts[:2], (7, 6))
        self.assertFalse(User.objects.get(email="peer1@peers.gifted.demo").has_usable_password())

        demo = User.objects.get(email="student@gifted.demo")
        record_activity(demo, EventType.MISSION_COMPLETED, "attempt:1")
        self._c(demo).post("/api/v1/engagement/rewards/sticker-pack/redeem/")
        self.assertTrue(StudentBadge.objects.filter(learner=demo).exists())
        call_command("reset_demo", stdout=open("/dev/null", "w"))
        self.assertFalse(ActivityEvent.objects.filter(learner=demo).exists())
        self.assertFalse(StudentBadge.objects.filter(learner=demo).exists())
        self.assertFalse(RewardRedemption.objects.filter(learner=demo).exists())
        self.assertTrue(ActivityEvent.objects.filter(learner__email__endswith="@peers.gifted.demo").exists())  # peers kept
