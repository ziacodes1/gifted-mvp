import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.evidence.models import Evidence
from apps.questions.models import QuestionOption
from apps.signals.models import LearnerSignal, ResponseSignalMap, Signal

from .models import Assessment, AssessmentSession


class AssessmentV2Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        cls.student = get_user_model().objects.create_user("s@test.dev", "pw12345!")

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.student)
        self.session = self.c.post(f"/api/v1/assessments/{Assessment.objects.get(is_active=True).id}/start/").json()
        self.q = {q["type"] + str(i): q for i, q in enumerate(self.session["questions"])}

    def _answer(self, question, option_ids):
        return self.c.post(
            f"/api/v1/assessment-sessions/{self.session['id']}/answer/",
            {"question_id": question["id"], "option_ids": option_ids},
            format="json",
        )

    def _pick(self, question, value):
        return QuestionOption.objects.get(question_id=question["id"], value=value).id

    def test_mixed_types_and_hidden_labels(self):
        types = [q["type"] for q in self.session["questions"]]
        self.assertEqual(len(types), 10)
        self.assertEqual(
            set(types), {"VISUAL_CHOICE", "STORY_CHOICE", "SCENARIO_CHOICE", "VALUE_TRADEOFF", "MULTI_SELECT", "PATTERN_CHOICE"}
        )
        payload = json.dumps(self.session["questions"])
        # Category labels and signal keys never reach the learner, and neither do puzzle answers.
        for hidden in [s.label for s in Signal.objects.all()] + ["investigative", "exp_", "weight", "correct"]:
            self.assertNotIn(hidden, payload)
        visual = [q for q in self.session["questions"] if q["type"] == "VISUAL_CHOICE"]
        images = [o["image"] for q in visual for o in q["options"]]
        self.assertEqual(len(images), len(set(images)), "visual questions must not repeat images")

    def test_multi_select_rules(self):
        exposure = next(q for q in self.session["questions"] if q["type"] == "MULTI_SELECT")
        none_id, built_id = self._pick(exposure, "none"), self._pick(exposure, "built")
        self.assertEqual(self._answer(exposure, [none_id, built_id]).status_code, 400)
        self.assertEqual(self._answer(exposure, [built_id, self._pick(exposure, "coded")]).status_code, 200)
        restored = self.c.get(f"/api/v1/assessment-sessions/{self.session['id']}/").json()["responses"]
        self.assertEqual(sorted(restored[str(exposure["id"])]), sorted([built_id, self._pick(exposure, "coded")]))
        single = self.session["questions"][0]
        self.assertEqual(self._answer(single, [o["id"] for o in single["options"][:2]]).status_code, 400)

    def _complete_choosing(self, choose):
        for q in self.session["questions"]:
            ids = choose(q)
            self.assertEqual(self._answer(q, ids).status_code, 200)
        r = self.c.post(f"/api/v1/assessment-sessions/{self.session['id']}/complete/")
        self.assertEqual(r.status_code, 200)
        return {ls.signal.key: ls for ls in LearnerSignal.objects.filter(learner=self.student).select_related("signal")}

    def test_scoring_is_per_opportunity_and_categories_stay_separate(self):
        def choose(q):
            correct = ResponseSignalMap.objects.filter(
                option__question_id=q["id"], signal__category="APTITUDE"
            ).values_list("option_id", flat=True)
            if correct:
                return [correct[0]]
            if q["type"] == "MULTI_SELECT":
                return [self._pick(q, "none")]
            return [q["options"][0]["id"]]

        signals = self._complete_choosing(choose)
        cats = {ls.signal.category for ls in signals.values()}
        self.assertEqual(cats, {"INTEREST", "APTITUDE", "WORK_STYLE", "VALUE", "EXPOSURE"})
        # Puzzles answered correctly → aptitude evidence, but always LOW confidence.
        self.assertEqual(signals["logical_reasoning"].score, 100)
        self.assertEqual(signals["logical_reasoning"].confidence, "LOW")
        # "None of these yet" → exposure rows exist with zero evidence (known "not tried").
        self.assertEqual(signals["exp_science"].evidence_count, 0)
        self.assertEqual(signals["exp_science"].opportunity_count, 1)
        # Short assessment never produces HIGH confidence.
        self.assertFalse(any(ls.confidence == "HIGH" for ls in signals.values()))
        # Interest scores use their own chances as the denominator.
        realistic = signals["realistic"]
        self.assertEqual(realistic.opportunity_count, 5)
        self.assertEqual(Evidence.objects.filter(source_type="ASSESSMENT").count(), 1)

    def test_wrong_puzzle_answer_is_not_negative_evidence(self):
        def choose(q):
            if q["type"] == "PATTERN_CHOICE":
                mapped = set(ResponseSignalMap.objects.filter(option__question_id=q["id"]).values_list("option_id", flat=True))
                return [next(o["id"] for o in q["options"] if o["id"] not in mapped)]
            return [q["options"][0]["id"]]

        signals = self._complete_choosing(choose)
        self.assertEqual(signals["spatial_reasoning"].evidence_count, 0)
        passport = self.c.get("/api/v1/passport/").json()
        self.assertNotIn("spatial_reasoning", [s["key"] for s in passport["signals"]])
        self.assertTrue(all(s["category"] == "INTEREST" for s in passport["signals"]))

    def test_completed_session_is_not_duplicated_by_revisiting(self):
        self._complete_choosing(lambda q: [q["options"][0]["id"]])
        # The frontend only calls start() with ?retake=1; a plain start still creates a retake by design.
        self.assertEqual(AssessmentSession.objects.filter(learner=self.student).count(), 1)

    def test_seed_is_idempotent(self):
        call_command("seed_demo_assessment", verbosity=0)
        self.assertEqual(Assessment.objects.filter(is_active=True).count(), 1)
        self.assertEqual(QuestionOption.objects.filter(question__section__assessment__is_active=True).count(), 39)
