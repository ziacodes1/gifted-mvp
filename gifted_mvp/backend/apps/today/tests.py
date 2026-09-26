import json
import shutil
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.assessments.models import Assessment
from apps.companion.tests import RecordingProvider
from apps.diary.models import DiaryEntry
from apps.engagement.models import ActivityEvent
from apps.engagement.rules import EventType
from apps.engagement.services import local_day
from apps.missions.tests import ANSWERS, SLUG
from apps.parents.models import ParentChild

from .catalog import FACT_COUNT, SPARKS, SparkType
from .models import DailySpark, SparkStatus
from .services import candidates, learner_state

User = get_user_model()
SECRET = "my secret diary sentence about feeling sad"


class TodayTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        call_command("seed_demo_mission", verbosity=0)
        call_command("seed_demo_engagement", verbosity=0)
        cls.student = User.objects.create_user("kid@test.dev", "pw12345!", full_name="Ada Lovelace")
        cls.parent = User.objects.create_user("mum@test.dev", "pw12345!", role="PARENT")
        ParentChild.objects.create(parent=cls.parent, learner=cls.student)

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        o = override_settings(PRIVATE_MEDIA_ROOT=Path(self.media))
        o.enable()
        self.addCleanup(o.disable)
        self.today = local_day()

    def _c(self, user=None, lang=None):
        c = APIClient()
        c.force_authenticate(user or self.student)
        if lang:
            c.credentials(HTTP_ACCEPT_LANGUAGE=lang)
        return c

    def _today(self, **kw):
        return self._c(**kw).get("/api/v1/today/").json()

    def _force(self, key):
        DailySpark.objects.update_or_create(learner=self.student, day=self.today, defaults={"spark_key": key, "status": SparkStatus.NEW})

    def _action(self, key, action):
        return self._c().post("/api/v1/today/spark/", {"spark_key": key, "action": action}, format="json")

    def _answer_one(self):
        c = self._c()
        s = c.post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()
        q = s["questions"][0]
        c.post(f"/api/v1/assessment-sessions/{s['id']}/answer/", {"question_id": q["id"], "option_id": q["options"][0]["id"]}, format="json")
        return s

    def _assessment(self):
        c = self._c()
        s = c.post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()
        for q in s["questions"]:
            c.post(f"/api/v1/assessment-sessions/{s['id']}/answer/", {"question_id": q["id"], "option_id": q["options"][0]["id"]}, format="json")
        c.post(f"/api/v1/assessment-sessions/{s['id']}/complete/")

    def _mission(self):
        c = self._c()
        a = c.post(f"/api/v1/missions/{SLUG}/start/").json()
        steps = {s["key"]: s["id"] for s in a["mission"]["steps"]}
        for key, data in ANSWERS.items():
            c.post(f"/api/v1/mission-attempts/{a['id']}/answer/", {"step_id": steps[key], "response": data}, format="json")
        c.post(f"/api/v1/mission-attempts/{a['id']}/complete/")

    def _keys(self, today=None):
        return dict(candidates(learner_state(self.student, today or self.today)))

    # --- smart selection -----------------------------------------------------------------

    def test_selection_follows_learner_state(self):
        keys = self._keys()
        self.assertEqual(max(keys, key=keys.get), "ns_start_discovery")
        self.assertIn("dp_first_page", keys)
        self.assertNotIn("mn_try_mission", keys)

        self._assessment()
        # Tomorrow (not active yet): exploration comes first, discovery is gone.
        keys = self._keys(self.today + timedelta(days=1))
        self.assertEqual(max(keys, key=keys.get), "mn_try_mission")
        self.assertNotIn("ns_start_discovery", keys)

        self._mission()
        keys = self._keys(self.today + timedelta(days=1))
        self.assertIn("ns_passport_updated", keys)
        self.assertNotIn("mn_try_mission", keys)

        DiaryEntry.objects.create(learner=self.student, title="t", body="b")
        DiaryEntry.objects.filter(learner=self.student).update(created_at=DiaryEntry.objects.get().created_at - timedelta(days=5))
        keys = self._keys(self.today + timedelta(days=1))
        self.assertIn("dp_come_back", keys)
        self.assertNotIn("dp_first_page", keys)

    def test_after_meaningful_action_today_only_lighter_content(self):
        self._answer_one()  # active today
        types = {("FACT" if k == "fact" else next(s.type for s in SPARKS if s.key == k)) for k in self._keys()}
        self.assertTrue(types <= {SparkType.REFLECTION, SparkType.FACT, SparkType.COMPANION_PROMPT})

    def test_stable_for_the_day_and_varies_across_days(self):
        first = self._today()["spark"]["key"]
        for _ in range(3):
            self.assertEqual(self._today()["spark"]["key"], first)
        self.assertEqual(DailySpark.objects.filter(learner=self.student).count(), 1)

        seen = []
        for i in range(1, 12):
            with mock.patch("apps.today.services.local_day", return_value=self.today + timedelta(days=i)):
                seen.append(self._today()["spark"]["key"])
        self.assertGreater(len(set(seen)), 3)
        self.assertTrue(all(a != b for a, b in zip(seen, seen[1:])))  # never the same card two days running

    def test_changes_when_the_asked_action_is_done(self):
        self._force("ns_start_discovery")
        self.assertEqual(self._today()["spark"]["key"], "ns_start_discovery")
        self._answer_one()
        spark = self._today()["spark"]
        self.assertNotEqual(spark["key"], "ns_start_discovery")
        self.assertIn(spark["type"], (SparkType.REFLECTION, SparkType.FACT, SparkType.COMPANION_PROMPT))

    def test_routes_and_targets(self):
        self._assessment()
        DailySpark.objects.filter(learner=self.student).delete()
        self._force("mn_try_mission")
        spark = self._today()["spark"]
        self.assertEqual((spark["route"], spark["target"], spark["actions"]), ("mission", SLUG, ["go"]))
        self._force("fact_07")
        spark = self._today()["spark"]
        self.assertEqual((spark["type"], spark["fact_index"]), ("FACT", 7))

    # --- privacy ---------------------------------------------------------------------------

    def test_no_diary_text_mood_or_companion_text_is_used(self):
        for _ in range(2):
            self._c().post("/api/v1/diary/entries/", {"title": "Private title", "body": SECRET, "mood": "very_low", "tags": ["secret-tag"]}, format="json")
        conv = self._c().post("/api/v1/companion/conversations/").json()["id"]
        with mock.patch("apps.ai.services.companion.get_provider", return_value=RecordingProvider()):
            self._c().post(f"/api/v1/companion/conversations/{conv}/messages/", {"content": "companion secret text", "client_id": str(uuid.uuid4())}, format="json")
        before = self._today()
        text = json.dumps(before)
        for secret in (SECRET, "Private title", "very_low", "secret-tag", "companion secret text", "mood"):
            self.assertNotIn(secret, text)
        # Changing private content changes nothing.
        DiaryEntry.objects.filter(learner=self.student).update(body="totally different", mood="great", title="x", tags=["y"])
        self.assertEqual(self._today()["spark"], before["spark"])
        self.assertEqual(self._today()["motivation"], before["motivation"])

    def test_parent_sees_none_of_it(self):
        self._assessment()
        self._today()
        parent = self._c(self.parent)
        self.assertEqual(parent.get("/api/v1/today/").status_code, 403)
        self.assertEqual(parent.post("/api/v1/today/spark/", {"spark_key": "x", "action": "dismiss"}, format="json").status_code, 403)
        overview = parent.get(f"/api/v1/parent/children/{self.student.id}/overview/").content.decode()
        for leak in ("spark", "nudge", "motivation", "fact_", "reflect_", "dp_", "cp_"):
            self.assertNotIn(leak, overview)

    # --- mini challenges -------------------------------------------------------------------------

    def test_mini_challenge_completion_is_idempotent_and_capped(self):
        self._force("ch_ask_field")
        self.assertEqual(self._action("ch_ask_field", "complete").status_code, 200)
        r = self._action("ch_ask_field", "complete")
        self.assertEqual(r.json()["spark"]["status"], "DONE")
        events = ActivityEvent.objects.filter(learner=self.student, event_type=EventType.MINI_CHALLENGE)
        self.assertEqual([e.points for e in events], [5])
        self.assertEqual(self._action("ch_ask_field", "dismiss").json()["spark"]["status"], "DONE")  # can't undo done

        # Another challenge key the same day (e.g. via a stale tab) can't pay twice.
        DailySpark.objects.filter(learner=self.student).update(spark_key="ch_three_solutions", status=SparkStatus.NEW)
        self._action("ch_three_solutions", "complete")
        self.assertEqual(events.count(), 1)

    def test_only_todays_challenges_complete_and_dismiss_restore(self):
        self._force("reflect_proud")
        self.assertEqual(self._action("reflect_proud", "complete").json()["error"]["detail"], "not_completable")
        self.assertEqual(self._action("ch_ask_field", "complete").json()["error"]["detail"], "not_today")
        self.assertEqual(self._action("reflect_proud", "dismiss").json()["spark"]["status"], "DISMISSED")
        self.assertEqual(self._action("reflect_proud", "restore").json()["spark"]["status"], "NEW")
        self.assertFalse(ActivityEvent.objects.filter(learner=self.student).exists())

    # --- nudges ------------------------------------------------------------------------------------

    def test_nudges_from_real_state_and_seen(self):
        body = self._today()
        self.assertEqual([n["kind"] for n in body["nudges"]], ["spark"])
        self._assessment()
        self._mission()
        for i in range(5):
            self._c().post("/api/v1/diary/entries/", {"body": f"page {i}"}, format="json")
        kinds = {n["kind"]: n for n in self._today()["nudges"]}
        self.assertIn("badge", kinds)
        self.assertIn("passport", kinds)
        self.assertEqual(kinds["diary_milestone"]["params"], {"count": 5})
        self.assertIn("reward", kinds)  # 100+ points → the sticker pack is affordable
        self.assertGreater(self._today()["unread"], 0)
        self.assertEqual(self._c().post("/api/v1/today/nudges/seen/").status_code, 204)
        self.assertEqual(self._today()["unread"], 0)

    # --- language + copy ------------------------------------------------------------------------------

    def test_payload_is_language_independent_and_every_key_is_translated(self):
        en, uz, ru = (self._today(lang=lang) for lang in ("en", "uz", "ru"))
        self.assertEqual(en["spark"], uz["spark"])
        self.assertEqual(en["spark"], ru["spark"])
        locales = Path(settings.BASE_DIR).parent / "frontend" / "src" / "i18n" / "locales"
        for lang in ("en", "uz", "ru"):
            sparks = json.loads((locales / f"{lang}.json").read_text(encoding="utf-8"))["sparks"]
            for s in SPARKS:
                self.assertIn(s.key, sparks["items"], (lang, s.key))
                self.assertTrue(sparks["items"][s.key]["title"], (lang, s.key))
            self.assertEqual(len(sparks["facts"]), FACT_COUNT, lang)

    def test_reset_demo_clears_today_state(self):
        call_command("seed_demo", verbosity=0)
        demo = User.objects.get(email="student@gifted.demo")
        self._c(demo).get("/api/v1/today/")
        self.assertTrue(DailySpark.objects.filter(learner=demo).exists())
        call_command("reset_demo", stdout=open("/dev/null", "w"))
        self.assertFalse(DailySpark.objects.filter(learner=demo).exists())
