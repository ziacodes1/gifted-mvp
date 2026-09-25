import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.ai.models import AIInsight, GenerationType
from apps.ai.services.provider import ProviderError
from apps.ai.tests import FakeProvider
from apps.assessments.models import Assessment
from apps.missions.tests import ANSWERS, SLUG

from .models import LearnerConnectionCode, ParentChild

PARENT_AI = {
    "summary": "The current evidence suggests an early interest in design. This picture is still forming.",
    "what_we_are_seeing": [{"title": "Interest in design", "explanation": "Chosen in most assessment answers."}],
    "what_is_still_unclear": ["There is still limited evidence in helping people."],
    "support_at_home": [
        {"title": "Ask about the experience", "action": "Ask what felt most interesting."},
        {"title": "Try something small", "action": "Offer a short hands-on activity."},
    ],
    "conversation_starter": "What part of the bag challenge did you enjoy?",
    "caution": "Exploration is more useful than an early decision.",
}
REFLECTION = ANSWERS["reflect"]["why"]


class ParentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        call_command("seed_demo_mission", verbosity=0)
        User = get_user_model()
        cls.student = User.objects.create_user("kid@test.dev", "pw12345!", full_name="Ada Lovelace")
        cls.other_kid = User.objects.create_user("kid2@test.dev", "pw12345!")
        cls.parent = User.objects.create_user("mum@test.dev", "pw12345!", role="PARENT")
        cls.stranger = User.objects.create_user("stranger@test.dev", "pw12345!", role="PARENT")
        ParentChild.objects.create(parent=cls.parent, learner=cls.student)

    def _c(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def _overview(self, user=None, learner=None):
        return self._c(user or self.parent).get(f"/api/v1/parent/children/{(learner or self.student).id}/overview/")

    def _insight(self):
        return self._c(self.parent).post(f"/api/v1/parent/children/{self.student.id}/insight/")

    def _assessment(self):
        c = self._c(self.student)
        s = c.post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()
        for q in s["questions"]:
            c.post(
                f"/api/v1/assessment-sessions/{s['id']}/answer/",
                {"question_id": q["id"], "option_id": q["options"][0]["id"]},
                format="json",
            )
        c.post(f"/api/v1/assessment-sessions/{s['id']}/complete/")

    def _mission(self):
        c = self._c(self.student)
        a = c.post(f"/api/v1/missions/{SLUG}/start/").json()
        steps = {s["key"]: s["id"] for s in a["mission"]["steps"]}
        for key, data in ANSWERS.items():
            c.post(f"/api/v1/mission-attempts/{a['id']}/answer/", {"step_id": steps[key], "response": data}, format="json")
        c.post(f"/api/v1/mission-attempts/{a['id']}/complete/")

    def _patch(self, provider):
        return mock.patch("apps.ai.services.parent_insight.get_provider", return_value=provider)

    def test_a_children_list_and_b_empty_state(self):
        kids = self._c(self.parent).get("/api/v1/parent/children/").json()
        self.assertEqual(kids, [{"id": self.student.id, "display_name": "Ada Lovelace"}])
        body = self._overview().json()
        self.assertEqual(body["status"], "EMPTY")
        self.assertFalse(body["has_evidence"])
        self.assertNotIn("current_signals", body)
        self.assertEqual(self._insight().json(), {"parent_insight": None})

    def test_c_emerging_then_d_growing_with_real_data(self):
        self._assessment()
        body = self._overview().json()
        self.assertEqual(body["status"], "EMERGING")
        self.assertEqual(body["evidence"]["assessment"], 10)
        self.assertEqual(body["evidence"]["missions"], 0)
        self.assertEqual(body["parent_insight_state"], "PENDING")

        self._mission()
        body = self._overview().json()
        self.assertEqual(body["status"], "GROWING")
        self.assertEqual(body["learner"]["journey_stage"], "Explore")
        self.assertEqual(body["evidence"]["missions"], 1)
        self.assertEqual(body["recent_activity"][0]["title"], "Design a Better School Bag")
        self.assertEqual(body["next_mission"]["status"], "COMPLETED")

    def test_privacy_boundary(self):
        self._assessment()
        self._mission()
        with self._patch(FakeProvider(result=PARENT_AI)):
            self._insight()
        text = json.dumps(self._overview().json())
        for secret in (REFLECTION, "test_first", "choices", "metadata", "weight", "provider", "fake-1", "input_version", "selected"):
            self.assertNotIn(secret, text)

    def test_e_unrelated_parent_and_f_student_denied(self):
        self._assessment()
        self.assertEqual(self._overview(user=self.stranger).status_code, 404)
        self.assertEqual(self._c(self.stranger).post(f"/api/v1/parent/children/{self.student.id}/insight/").status_code, 404)
        self.assertEqual(self._overview(learner=self.other_kid).status_code, 404)
        self.assertEqual(self._c(self.student).get("/api/v1/parent/children/").status_code, 403)
        self.assertEqual(self._c(self.student).get(f"/api/v1/parent/children/{self.student.id}/overview/").status_code, 403)
        self.assertEqual(APIClient().get("/api/v1/parent/children/").status_code, 401)

    def test_g_provider_failure_falls_back(self):
        self._assessment()
        self._mission()
        with self._patch(FakeProvider(error=ProviderError("connection_error"))):
            r = self._insight()
        self.assertEqual(r.status_code, 200)
        insight = r.json()["parent_insight"]
        self.assertEqual(insight["source"], "FALLBACK")
        self.assertGreaterEqual(len(insight["content"]["support_at_home"]), 2)
        self.assertIn("Design a Better School Bag", insight["content"]["conversation_starter"])
        self.assertNotIn("connection_error", r.content.decode())

    def test_h_no_repeated_llm_calls_per_version_and_new_version_regenerates(self):
        self._assessment()
        fake = FakeProvider(result=PARENT_AI)
        with self._patch(fake):
            first = self._insight().json()["parent_insight"]
            self._insight()
            self._insight()
            for _ in range(3):
                self._overview()  # dashboard loads never call the model
        self.assertEqual(fake.calls, 1)
        self.assertEqual(first["source"], "AI")
        self.assertEqual(self._overview().json()["parent_insight_state"], "READY")

        self._mission()  # new evidence → new Passport version → insight pending again
        self.assertEqual(self._overview().json()["parent_insight_state"], "PENDING")
        with self._patch(fake):
            self._insight()
        self.assertEqual(fake.calls, 2)
        self.assertEqual(AIInsight.objects.filter(generation_type=GenerationType.PARENT_INSIGHT).count(), 2)

    def test_unsafe_ai_output_rejected(self):
        self._assessment()
        bad = {**PARENT_AI, "summary": "Your child should become an architect."}
        with self._patch(FakeProvider(result=bad)):
            self.assertEqual(self._insight().json()["parent_insight"]["source"], "FALLBACK")

    def test_connect_with_code(self):
        LearnerConnectionCode.objects.create(learner=self.other_kid, code="GFT-11111")
        self.assertEqual(self._c(self.stranger).post("/api/v1/parent/children/connect/", {"code": "gft-11111"}).status_code, 200)
        self.assertEqual(self._overview(user=self.stranger, learner=self.other_kid).status_code, 200)
        self.assertEqual(self._c(self.stranger).post("/api/v1/parent/children/connect/", {"code": "GFT-00000"}).status_code, 404)

    def test_sources_explicit_and_mission_misattribution_rejected(self):
        from apps.ai.services.parent_insight import get_saved_parent_insight
        from apps.parents.services import parent_insight_input
        from apps.passports.services import build_passport

        self._assessment()
        self._mission()
        data = parent_insight_input(build_passport(self.student))
        self.assertTrue(all(s["evidence_source"] == "assessment" for s in data["signals"]))
        self.assertTrue(all(d["evidence_source"] == "mission" for d in data["explored_through_missions"]))
        mission_labels = {d["label"] for d in data["explored_through_missions"]}
        assessment_only = next(s["label"] for s in data["signals"] if s["label"] not in mission_labels)
        mission_recorded = next(iter(mission_labels))

        wrong = {**PARENT_AI, "what_we_are_seeing": [
            {"title": f"Interest in {assessment_only}", "explanation": "Shown in the assessment and in the mission."}
        ]}
        with self._patch(FakeProvider(result=wrong)):
            self.assertEqual(self._insight().json()["parent_insight"]["source"], "FALLBACK")

        AIInsight.objects.filter(generation_type=GenerationType.PARENT_INSIGHT).delete()
        right = {**PARENT_AI, "what_we_are_seeing": [
            {"title": f"Interest in {assessment_only}", "explanation": "Current evidence from the assessment suggests an interest."},
            {"title": "Early hands-on exploration", "explanation": f"The mission added evidence about {mission_recorded}."},
        ]}
        with self._patch(FakeProvider(result=right)):
            self.assertEqual(self._insight().json()["parent_insight"]["source"], "AI")
        self.assertIsNotNone(get_saved_parent_insight(self._latest_session(), build_passport(self.student)["version"]))

    def _latest_session(self):
        from apps.assessments.models import AssessmentSession

        return AssessmentSession.objects.filter(learner=self.student, status="COMPLETED").latest("completed_at")

    def test_seed_family_idempotent(self):
        call_command("seed_demo", verbosity=0)
        call_command("seed_demo", verbosity=0)
        User = get_user_model()
        self.assertEqual(
            ParentChild.objects.filter(
                parent=User.objects.get(email="parent@gifted.demo"), learner=User.objects.get(email="student@gifted.demo")
            ).count(),
            1,
        )

