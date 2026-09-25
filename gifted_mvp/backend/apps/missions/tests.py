from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.assessments.models import Assessment
from apps.evidence.models import Evidence, EvidenceSource
from apps.passports.models import Passport
from apps.signals.models import LearnerSignal

from .models import Mission, MissionSignalMap
from .services import match_mission

SLUG = "design-a-better-school-bag"

ANSWERS = {
    "brief": {"acknowledged": True},
    "understand": {"selected": ["uncomfortable_straps", "hard_to_organize"]},
    "prioritize": {"selected": ["ergonomic_straps", "modular_compartments", "waterproof_layer"]},
    "direction": {"selected": "comfort_fit"},
    "reflect": {"why": "Comfort affects everyone every single day.", "test_first": "Strap padding with a heavy load."},
}


class MissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        call_command("seed_demo_mission", verbosity=0)
        User = get_user_model()
        cls.student = User.objects.create_user("s1@test.dev", "pw12345!")
        cls.other = User.objects.create_user("s2@test.dev", "pw12345!")
        cls.parent = User.objects.create_user("p@test.dev", "pw12345!", role="PARENT")

    def setUp(self):
        # Any provider call anywhere in these flows is a bug.
        patcher = mock.patch(
            "apps.ai.services.profile_synthesis.get_provider",
            side_effect=AssertionError("no LLM calls in mission/passport flows"),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _c(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def _complete_assessment(self, user):
        c = self._c(user)
        s = c.post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()
        for q in s["questions"]:
            c.post(
                f"/api/v1/assessment-sessions/{s['id']}/answer/",
                {"question_id": q["id"], "option_id": q["options"][0]["id"]},
                format="json",
            )
        c.post(f"/api/v1/assessment-sessions/{s['id']}/complete/")

    def _start(self, user):
        return self._c(user).post(f"/api/v1/missions/{SLUG}/start/").json()

    def _answer_all(self, user, attempt):
        steps = {s["key"]: s["id"] for s in attempt["mission"]["steps"]}
        for key, data in ANSWERS.items():
            r = self._c(user).post(
                f"/api/v1/mission-attempts/{attempt['id']}/answer/",
                {"step_id": steps[key], "response": data},
                format="json",
            )
            self.assertEqual(r.status_code, 200, r.content)
        return r.json()

    def test_detail_hides_evidence_rules(self):
        body = self._c(self.student).get(f"/api/v1/missions/{SLUG}/").json()
        self.assertEqual(len(body["steps"]), 5)
        text = str(body)
        for secret in ("signal_maps", "'weight':", "user_thinking", "observation"):
            self.assertNotIn(secret, text)

    def test_start_resumes_and_progress_restores(self):
        a1 = self._start(self.student)
        steps = {s["key"]: s["id"] for s in a1["mission"]["steps"]}
        c = self._c(self.student)
        c.post(f"/api/v1/mission-attempts/{a1['id']}/answer/", {"step_id": steps["brief"], "response": {}}, format="json")
        c.post(
            f"/api/v1/mission-attempts/{a1['id']}/answer/",
            {"step_id": steps["understand"], "response": ANSWERS["understand"]},
            format="json",
        )
        a2 = self._start(self.student)
        self.assertEqual(a2["id"], a1["id"])
        self.assertEqual(a2["next_step_index"], 2)
        self.assertEqual(a2["responses"][str(steps["understand"])], ANSWERS["understand"])

    def test_validation(self):
        a = self._start(self.student)
        steps = {s["key"]: s["id"] for s in a["mission"]["steps"]}
        post = lambda key, data: self._c(self.student).post(  # noqa: E731
            f"/api/v1/mission-attempts/{a['id']}/answer/", {"step_id": steps[key], "response": data}, format="json"
        )
        self.assertEqual(post("understand", {"selected": ["too_heavy", "hard_to_organize", "books_damaged"]}).status_code, 400)
        over = {"selected": ["lightweight_material", "ergonomic_straps", "modular_compartments"]}  # 10 ok
        self.assertEqual(post("prioritize", over).status_code, 200)
        over["selected"].append("waterproof_layer")  # 12 > 10
        self.assertEqual(post("prioritize", over).status_code, 400)
        self.assertEqual(post("direction", {"selected": "nope"}).status_code, 400)
        self.assertEqual(post("reflect", {"why": "short"}).status_code, 400)
        self.assertEqual(self._c(self.student).post(f"/api/v1/mission-attempts/{a['id']}/complete/").status_code, 400)

    def test_complete_creates_evidence_once_and_grows_passport(self):
        self._complete_assessment(self.student)
        scores_before = dict(LearnerSignal.objects.filter(learner=self.student).values_list("signal__key", "score"))
        p = Passport.objects.get(learner=self.student)
        self.assertEqual((p.status, p.version), ("EMERGING", 1))

        a = self._start(self.student)
        self._answer_all(self.student, a)
        r1 = self._c(self.student).post(f"/api/v1/mission-attempts/{a['id']}/complete/").json()
        r2 = self._c(self.student).post(f"/api/v1/mission-attempts/{a['id']}/complete/").json()

        self.assertTrue(r1["evidence_created"])
        self.assertFalse(r2["evidence_created"])
        self.assertEqual(r1["result"]["id"], r2["result"]["id"])
        self.assertEqual(Evidence.objects.filter(source_type=EvidenceSource.MISSION).count(), 1)
        self.assertEqual(r1["passport"], {"status": "GROWING", "version": 2, "missions": 1})
        labels = {d["label"] for d in r1["result"]["dimensions"]}
        self.assertTrue({"Design & making exposure", "Prioritization & trade-offs", "User thinking & empathy"} <= labels)

        # Contributions are bounded per activity.
        ev = Evidence.objects.get(source_type=EvidenceSource.MISSION)
        self.assertTrue(all(0 < c.weight <= 1 for c in ev.contributions.all()))
        # Assessment scores are untouched by mission evidence.
        self.assertEqual(
            dict(LearnerSignal.objects.filter(learner=self.student).values_list("signal__key", "score")), scores_before
        )
        # Answers are locked after completion.
        step_id = a["mission"]["steps"][1]["id"]
        r = self._c(self.student).post(
            f"/api/v1/mission-attempts/{a['id']}/answer/", {"step_id": step_id, "response": ANSWERS["understand"]}, format="json"
        )
        self.assertEqual(r.status_code, 400)

        passport = self._c(self.student).get("/api/v1/passport/").json()
        self.assertEqual(passport["status"], "GROWING")
        self.assertEqual(passport["evidence_summary"]["missions"], 1)
        self.assertEqual(passport["evidence_summary"]["assessment"], 10)
        self.assertEqual(passport["evidence_sources"], {"assessments": 1, "missions": 1})
        self.assertEqual([s["done"] for s in passport["journey"]], [True, True, False, False, False])
        self.assertEqual(passport["recent_evidence"][0]["title"], "Design a Better School Bag")
        self.assertFalse(passport["insight_covers_new_evidence"])
        self.assertEqual(passport["recommended_mission"]["my_attempt"]["status"], "COMPLETED")
        self.assertEqual(passport["version"], 2)  # reads don't bump

    def test_mission_without_assessment_keeps_passport_empty(self):
        a = self._start(self.student)
        self._answer_all(self.student, a)
        self._c(self.student).post(f"/api/v1/mission-attempts/{a['id']}/complete/")
        self.assertEqual(self._c(self.student).get("/api/v1/passport/").json()["status"], "EMPTY")

    def test_isolation_and_roles(self):
        a = self._start(self.student)
        other = self._c(self.other)
        self.assertEqual(other.get(f"/api/v1/mission-attempts/{a['id']}/").status_code, 404)
        self.assertEqual(other.post(f"/api/v1/mission-attempts/{a['id']}/complete/").status_code, 404)
        self.assertEqual(
            other.post(f"/api/v1/mission-attempts/{a['id']}/answer/", {"step_id": 1, "response": {}}, format="json").status_code,
            404,
        )
        self.assertEqual(self._c(self.parent).get("/api/v1/missions/").status_code, 403)
        self.assertEqual(APIClient().get("/api/v1/missions/").status_code, 401)

    def test_match_is_honest(self):
        m = Mission.objects.get(slug=SLUG)
        self.assertEqual(match_mission({"title": "Try a 30-minute bridge design challenge", "signals_used": []}, m), "RECOMMENDED")
        self.assertEqual(match_mission({"title": "x", "signals_used": ["realistic"]}, m), "RECOMMENDED")
        self.assertEqual(match_mission({"title": "Run a mini home experiment", "signals_used": ["investigative"]}, m), "SUGGESTED")
        self.assertEqual(match_mission(None, m), "SUGGESTED")

    def test_seed_is_idempotent(self):
        call_command("seed_demo_mission", verbosity=0)
        self.assertEqual(Mission.objects.count(), 1)
        self.assertEqual(MissionSignalMap.objects.count(), 21)
