from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.ai.models import AIInsight
from apps.ai.tests import VALID_AI, FakeProvider
from apps.assessments.models import Assessment
from apps.signals.models import LearnerSignal

from .models import Passport

URL = "/api/v1/passport/"


class PassportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        User = get_user_model()
        cls.student = User.objects.create_user("s1@test.dev", "pw12345!", full_name="Ada Lovelace")
        cls.other = User.objects.create_user("s2@test.dev", "pw12345!")
        cls.parent = User.objects.create_user("p@test.dev", "pw12345!", role="PARENT")

    def _client(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def _complete(self, user) -> int:
        c = self._client(user)
        s = c.post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()
        for q in s["questions"]:
            c.post(
                f"/api/v1/assessment-sessions/{s['id']}/answer/",
                {"question_id": q["id"], "option_id": q["options"][0]["id"]},
                format="json",
            )
        c.post(f"/api/v1/assessment-sessions/{s['id']}/complete/")
        return s["id"]

    def _no_llm(self):
        """Any provider call from the Passport path is a bug."""
        return mock.patch(
            "apps.ai.services.profile_synthesis.get_provider",
            side_effect=AssertionError("Passport must not call the LLM"),
        )

    def test_empty_state(self):
        with self._no_llm():
            r = self._client(self.student).get(URL)
        body = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(body["status"], "EMPTY")
        self.assertEqual(body["signals"], [])
        self.assertIsNone(body["next_step"])
        self.assertEqual(body["evidence_summary"]["total"], 0)
        self.assertFalse(any(s["done"] for s in body["journey"]))

    def test_emerging_with_persisted_ai_insight(self):
        sid = self._complete(self.student)
        with mock.patch(
            "apps.ai.services.profile_synthesis.get_provider", return_value=FakeProvider(result=VALID_AI)
        ):
            self._client(self.student).post("/api/v1/ai/profile-synthesis/", {"session_id": sid}, format="json")

        with self._no_llm():
            body = self._client(self.student).get(URL).json()

        self.assertEqual(body["status"], "EMERGING")
        self.assertEqual(body["insight_source"], "AI")
        self.assertEqual(body["headline"], VALID_AI["profile"]["headline"])
        self.assertEqual(body["learner"]["display_name"], "Ada Lovelace")
        # Scores are the deterministic LearnerSignal values, untouched by AI.
        db = {
            ls.signal.key: ls.score
            for ls in LearnerSignal.objects.filter(learner=self.student, signal__category="INTEREST", evidence_count__gt=0)
        }
        self.assertEqual({s["key"]: s["score"] for s in body["signals"]}, db)
        self.assertEqual(body["next_step"]["signals_used"], [{"key": "realistic", "label": "Technology & Building"}])
        self.assertEqual(body["evidence_summary"], {"total": 10, "assessment": 10, "missions": 0, "opportunities": 0, "experiences": 0})
        for key in ("provider", "model", "input_version"):
            self.assertNotIn(key, str(body.keys()))

    def test_emerging_without_insight_uses_deterministic_fallback(self):
        self._complete(self.student)
        self.assertEqual(AIInsight.objects.count(), 0)
        with self._no_llm():
            body = self._client(self.student).get(URL).json()
        self.assertEqual(body["status"], "EMERGING")
        self.assertEqual(body["insight_source"], "FALLBACK")
        self.assertTrue(body["headline"])
        self.assertTrue(body["next_step"]["title"])
        self.assertEqual(AIInsight.objects.count(), 0)  # read-only

    def test_passport_created_on_completion_and_versioned(self):
        self._complete(self.student)
        p = Passport.objects.get(learner=self.student)
        self.assertEqual((p.status, p.version), ("EMERGING", 1))
        self._client(self.student).get(URL)
        self._client(self.student).get(URL)
        p.refresh_from_db()
        self.assertEqual(p.version, 1)  # reads don't bump
        self._complete(self.student)  # retake = new evidence
        p.refresh_from_db()
        self.assertEqual(p.version, 2)

    def test_isolation_and_roles(self):
        self._complete(self.student)
        body = self._client(self.other).get(URL).json()
        self.assertEqual(body["status"], "EMPTY")
        self.assertEqual(body["signals"], [])
        self.assertEqual(self._client(self.parent).get(URL).status_code, 403)
        self.assertEqual(APIClient().get(URL).status_code, 401)

    def test_query_count_is_bounded(self):
        self._complete(self.student)
        c = self._client(self.student)
        c.get(URL)
        # Worst case (no saved insight → fallback derived on the fly); constant, no N+1.
        with self.assertNumQueries(16):
            c.get(URL)


class PassportLanguageTests(TestCase):
    """build_passport(learner, lang) must label everything in `lang`, even outside a request."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        call_command("seed_demo_mission", verbosity=0)
        cls.student = get_user_model().objects.create_user("lang@test.dev", "pw12345!")

    def test_explicit_language_reaches_nested_labels(self):
        from apps.missions.tests import ANSWERS, SLUG
        from rest_framework.test import APIClient

        from apps.assessments.models import Assessment
        from apps.passports.services import build_passport

        c = APIClient()
        c.force_authenticate(self.student)
        s = c.post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()
        for q in s["questions"]:
            c.post(f"/api/v1/assessment-sessions/{s['id']}/answer/", {"question_id": q["id"], "option_id": q["options"][0]["id"]}, format="json")
        c.post(f"/api/v1/assessment-sessions/{s['id']}/complete/")
        a = c.post(f"/api/v1/missions/{SLUG}/start/").json()
        steps = {x["key"]: x["id"] for x in a["mission"]["steps"]}
        for key, data in ANSWERS.items():
            c.post(f"/api/v1/mission-attempts/{a['id']}/answer/", {"step_id": steps[key], "response": data}, format="json")
        c.post(f"/api/v1/mission-attempts/{a['id']}/complete/")

        en, ru = build_passport(self.student, "en"), build_passport(self.student, "ru")
        self.assertNotEqual(en["explored_dimensions"][0]["label"], ru["explored_dimensions"][0]["label"])
        self.assertNotEqual(en["recent_evidence"][0]["title"], ru["recent_evidence"][0]["title"])
        self.assertTrue(any("Ѐ" <= ch <= "ӿ" for ch in ru["explored_dimensions"][0]["label"]))
