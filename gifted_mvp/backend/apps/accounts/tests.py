import io

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.ai.models import AIInsight
from apps.assessments.models import Assessment, AssessmentSession
from apps.evidence.models import Evidence
from apps.missions.models import Mission, MissionAttempt, MissionSignalMap
from apps.missions.tests import ANSWERS, SLUG
from apps.parents.models import ParentChild
from apps.passports.models import Passport
from apps.questions.models import Question
from apps.signals.models import LearnerSignal, Signal


class ResetDemoTests(TestCase):
    def _run_full_demo(self, student):
        c = APIClient()
        c.force_authenticate(student)
        s = c.post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()
        for q in s["questions"]:
            c.post(f"/api/v1/assessment-sessions/{s['id']}/answer/", {"question_id": q["id"], "option_id": q["options"][0]["id"]}, format="json")
        c.post(f"/api/v1/assessment-sessions/{s['id']}/complete/")
        c.post("/api/v1/ai/profile-synthesis/", {}, format="json")
        a = c.post(f"/api/v1/missions/{SLUG}/start/").json()
        steps = {st["key"]: st["id"] for st in a["mission"]["steps"]}
        for key, data in ANSWERS.items():
            c.post(f"/api/v1/mission-attempts/{a['id']}/answer/", {"step_id": steps[key], "response": data}, format="json")
        c.post(f"/api/v1/mission-attempts/{a['id']}/complete/")
        parent = APIClient()
        parent.force_authenticate(User.objects.get(email="parent@gifted.demo"))
        parent.post(f"/api/v1/parent/children/{student.id}/insight/")

    def test_reset_restores_clean_state_and_is_idempotent(self):
        call_command("seed_demo", stdout=io.StringIO())
        student = User.objects.get(email="student@gifted.demo")
        self._run_full_demo(student)
        self.assertEqual(Passport.objects.get(learner=student).status, "GROWING")
        content_before = (Question.objects.count(), Signal.objects.count(), Mission.objects.count(), MissionSignalMap.objects.count())

        for _ in range(2):
            out = io.StringIO()
            call_command("reset_demo", stdout=out)
            self.assertIn("Student state: NOT_STARTED", out.getvalue())
            for model in (AssessmentSession, LearnerSignal, MissionAttempt, Evidence, AIInsight, Passport):
                self.assertFalse(model.objects.filter(learner=student).exists(), model.__name__)

        self.assertEqual(
            (Question.objects.count(), Signal.objects.count(), Mission.objects.count(), MissionSignalMap.objects.count()),
            content_before,
        )
        self.assertTrue(ParentChild.objects.filter(parent__email="parent@gifted.demo", learner=student).exists())
        self.assertEqual(User.objects.get(email="admin@gifted.demo").role, "ADMIN")

        c = APIClient()
        c.force_authenticate(student)
        self.assertIsNone(c.get("/api/v1/assessments/").json()["results"][0]["my_latest_session"])
        self.assertEqual(c.get("/api/v1/passport/").json()["status"], "EMPTY")
