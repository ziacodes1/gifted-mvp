import json
import uuid
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.ai.services.provider import LLMProvider, ProviderError, StubProvider
from apps.ai.tests import FakeProvider
from apps.assessments.models import Assessment
from apps.missions.tests import ANSWERS, SLUG
from apps.parents.models import ParentChild
from apps.parents.tests import PARENT_AI

from .models import CompanionConversation, CompanionMessage

SECRET = "I feel nervous about my exams and I cried last night"
REPLY = "That sounds like a lot to carry. One small idea: pick one topic and do 20 focused minutes today."


class RecordingProvider(LLMProvider):
    """Records every call (system + parsed payload) so tests can inspect what the model saw."""

    name, model = "fake", "fake-1"

    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result or {"reply": REPLY}, error, []

    def generate_structured(self, *, system, prompt, schema, max_tokens=2000):
        self.calls.append({"system": system, "payload": json.loads(prompt), "raw": prompt})
        if self.error:
            raise self.error
        return self.result


class CompanionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        call_command("seed_demo_mission", verbosity=0)
        User = get_user_model()
        cls.student = User.objects.create_user("kid@test.dev", "pw12345!", full_name="Ada Lovelace")
        cls.other = User.objects.create_user("kid2@test.dev", "pw12345!", full_name="Other Kid")
        cls.parent = User.objects.create_user("mum@test.dev", "pw12345!", role="PARENT")
        ParentChild.objects.create(parent=cls.parent, learner=cls.student)

    def _c(self, user, lang=None):
        c = APIClient()
        c.force_authenticate(user)
        if lang:
            c.credentials(HTTP_ACCEPT_LANGUAGE=lang)
        return c

    def _patch(self, provider):
        return mock.patch("apps.ai.services.companion.get_provider", return_value=provider)

    def _new_chat(self, user=None, lang=None) -> int:
        return self._c(user or self.student, lang).post("/api/v1/companion/conversations/").json()["id"]

    def _send(self, conv_id, content="Hi!", user=None, client_id=None, lang=None):
        return self._c(user or self.student, lang).post(
            f"/api/v1/companion/conversations/{conv_id}/messages/",
            {"content": content, "client_id": str(client_id or uuid.uuid4())},
            format="json",
        )

    def _assessment(self, user=None):
        c = self._c(user or self.student)
        s = c.post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()
        for q in s["questions"]:
            c.post(
                f"/api/v1/assessment-sessions/{s['id']}/answer/",
                {"question_id": q["id"], "option_id": q["options"][0]["id"]},
                format="json",
            )
        c.post(f"/api/v1/assessment-sessions/{s['id']}/complete/")

    def _mission(self, user=None):
        c = self._c(user or self.student)
        a = c.post(f"/api/v1/missions/{SLUG}/start/").json()
        steps = {s["key"]: s["id"] for s in a["mission"]["steps"]}
        for key, data in ANSWERS.items():
            c.post(f"/api/v1/mission-attempts/{a['id']}/answer/", {"step_id": steps[key], "response": data}, format="json")
        c.post(f"/api/v1/mission-attempts/{a['id']}/complete/")

    # --- conversations ------------------------------------------------------------

    def test_student_creates_own_conversation_and_empty_chat_is_reused(self):
        r = self._c(self.student).post("/api/v1/companion/conversations/")
        self.assertEqual(r.status_code, 201)
        again = self._c(self.student).post("/api/v1/companion/conversations/")
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json()["id"], r.json()["id"])
        self.assertEqual(CompanionConversation.objects.get().learner, self.student)

    def test_message_gets_reply_and_conversation_persists(self):
        conv = self._new_chat()
        fake = RecordingProvider()
        with self._patch(fake):
            r = self._send(conv, "Help me understand what my current interests mean")
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body["user_message"]["role"], "USER")
        self.assertEqual(body["assistant_message"]["content"], REPLY)
        self.assertEqual(body["conversation"]["title"], "Help me understand what my current interests mean")

        detail = self._c(self.student).get(f"/api/v1/companion/conversations/{conv}/").json()
        self.assertEqual([m["role"] for m in detail["messages"]], ["USER", "ASSISTANT"])
        listed = self._c(self.student).get("/api/v1/companion/conversations/").json()
        self.assertEqual([c["id"] for c in listed], [conv])

        # A second turn sends the earlier turns as history; a new chat then starts clean.
        with self._patch(fake):
            self._send(conv, "And what next?")
        history = fake.calls[1]["payload"]["conversation"]
        self.assertEqual([h["from"] for h in history], ["student", "companion"])
        new = self._new_chat()
        self.assertNotEqual(new, conv)
        self.assertEqual(self._c(self.student).get(f"/api/v1/companion/conversations/{new}/").json()["messages"], [])

    def test_retry_with_same_client_id_returns_stored_turn(self):
        conv = self._new_chat()
        cid = uuid.uuid4()
        fake = RecordingProvider()
        with self._patch(fake):
            first = self._send(conv, "Hi", client_id=cid)
            second = self._send(conv, "Hi", client_id=cid)
        self.assertEqual((first.status_code, second.status_code), (201, 200))
        self.assertEqual(first.json()["assistant_message"]["id"], second.json()["assistant_message"]["id"])
        self.assertEqual(len(fake.calls), 1)
        self.assertEqual(CompanionMessage.objects.count(), 2)

    def test_other_student_parent_and_anonymous_are_denied(self):
        conv = self._new_chat()
        with self._patch(RecordingProvider()):
            self._send(conv, SECRET)
        other = self._c(self.other)
        self.assertEqual(other.get(f"/api/v1/companion/conversations/{conv}/").status_code, 404)
        with self._patch(RecordingProvider()):
            self.assertEqual(self._send(conv, "hi", user=self.other).status_code, 404)
        self.assertEqual(other.get("/api/v1/companion/conversations/").json(), [])

        parent = self._c(self.parent)
        for url in ("/api/v1/companion/conversations/", f"/api/v1/companion/conversations/{conv}/", "/api/v1/companion/overview/"):
            self.assertEqual(parent.get(url).status_code, 403)
            self.assertEqual(APIClient().get(url).status_code, 401)
        self.assertEqual(CompanionMessage.objects.count(), 2)

    def test_input_validation(self):
        conv = self._new_chat()
        with self._patch(RecordingProvider()):
            self.assertEqual(self._send(conv, "   ").status_code, 400)
            self.assertEqual(self._send(conv, "x" * 2001).status_code, 400)
            r = self._c(self.student).post(
                f"/api/v1/companion/conversations/{conv}/messages/", {"content": "hi"}, format="json"
            )
            self.assertEqual(r.status_code, 400)  # client_id required

    # --- context --------------------------------------------------------------------

    def test_context_uses_the_right_learner_and_keeps_sources_separate(self):
        self._assessment()
        self._mission()
        fake = RecordingProvider()
        with self._patch(fake):
            self._send(self._new_chat())
            self._send(self._new_chat(self.other), user=self.other)
        mine, theirs = fake.calls[0]["payload"]["learner_context"], fake.calls[1]["payload"]["learner_context"]

        self.assertEqual(mine["journey"]["passport_status"], "GROWING")
        self.assertEqual(mine["assessment"]["source"], "assessment")
        self.assertTrue(mine["assessment"]["interests"])
        self.assertEqual(mine["missions"]["source"], "mission")
        self.assertEqual(mine["missions"]["completed"], ["Design a Better School Bag"])
        self.assertEqual(mine["interpretation"]["written_from"], "assessment only")

        self.assertEqual(theirs["journey"]["passport_status"], "EMPTY")
        self.assertNotIn("assessment", theirs)
        self.assertNotIn("missions", theirs)

        sent = fake.calls[0]["raw"]
        for private in ("Ada", "Lovelace", "kid@test.dev", ANSWERS["reflect"]["why"], "weight", "test_first", '"score"'):
            self.assertNotIn(private, sent)

    def test_language_reaches_the_model(self):
        self._assessment()
        fake = RecordingProvider(result={"reply": "Salom! Keling, birga o‘ylab ko‘ramiz."})
        with self._patch(fake):
            r = self._send(self._new_chat(lang="uz"), "Salom", lang="uz")
        self.assertEqual(r.status_code, 201)
        call = fake.calls[0]
        self.assertIn("write the reply in Uzbek", call["system"])
        self.assertIn("Kashf qilish", call["payload"]["learner_context"]["journey"]["stages_reached"])
        self.assertEqual(CompanionMessage.objects.filter(role="ASSISTANT").get().language, "uz")

        with self._patch(fake):
            self._send(self._new_chat(lang="ru"), "Привет", lang="ru")
        self.assertIn("write the reply in Russian", fake.calls[1]["system"])
        self.assertIn("Открытие", fake.calls[1]["payload"]["learner_context"]["journey"]["stages_reached"])

    # --- failure & safety -----------------------------------------------------------

    def test_provider_failure_is_safe_and_stores_nothing(self):
        conv = self._new_chat()
        cid = uuid.uuid4()
        for error in (ProviderError("rate_limited"), ProviderError("api_status_400:secret_detail")):
            with self._patch(RecordingProvider(error=error)):
                r = self._send(conv, SECRET, client_id=cid)
            self.assertEqual(r.status_code, 503)
            self.assertEqual(r.json()["error"]["detail"], "companion_unavailable")
            self.assertNotIn("rate_limited", r.content.decode())
            self.assertNotIn("secret_detail", r.content.decode())
        self.assertEqual(CompanionMessage.objects.count(), 0)

        # Unconfigured provider (stub) → same calm state, never a canned "AI" answer.
        with self._patch(StubProvider()):
            self.assertEqual(self._send(conv, "hello").status_code, 503)

        with self._patch(RecordingProvider()):  # the same send succeeds once the provider is back
            self.assertEqual(self._send(conv, SECRET, client_id=cid).status_code, 201)
        self.assertEqual(CompanionMessage.objects.count(), 2)

    def test_unsafe_or_malformed_replies_are_rejected(self):
        conv = self._new_chat()
        for bad in ({"reply": "You should become a product designer."}, {"reply": "Тебе нужно стать врачом."}, {"text": "hi"}, {"reply": ""}):
            with self._patch(RecordingProvider(result=bad)):
                self.assertEqual(self._send(conv, "What should I be?").status_code, 503)
        self.assertEqual(CompanionMessage.objects.count(), 0)

    # --- prompts / overview -----------------------------------------------------------

    def test_overview_is_state_aware_and_never_calls_a_model(self):
        with self._patch(FakeProvider(error=AssertionError("no model call expected"))):
            empty = self._c(self.student).get("/api/v1/companion/overview/").json()
            self.assertEqual(empty["suggested_prompts"][0]["key"], "getting_started")
            self.assertEqual(empty["about"]["passport_status"], "EMPTY")

            self._assessment()
            emerging = self._c(self.student).get("/api/v1/companion/overview/").json()
            keys = [p["key"] for p in emerging["suggested_prompts"]]
            self.assertEqual(keys[0], "interest_meaning")
            self.assertTrue(emerging["suggested_prompts"][0]["params"]["interest"])
            self.assertNotIn("reflect_mission", keys)

            self._mission()
            growing = self._c(self.student, "ru").get("/api/v1/companion/overview/").json()
            first = growing["suggested_prompts"][0]
            self.assertEqual(first["key"], "reflect_mission")
            self.assertEqual(growing["about"]["missions_completed"], 1)
            self.assertEqual(growing["about"]["journey_stage"], "Исследование")
            self.assertLessEqual(len(growing["suggested_prompts"]), 4)

    # --- privacy boundary --------------------------------------------------------------

    def test_parent_endpoints_leak_no_companion_content(self):
        self._assessment()
        self._mission()
        with self._patch(RecordingProvider(result={"reply": "Private companion reply text"})):
            self._send(self._new_chat(), SECRET)

        parent_ai = RecordingProvider(result=PARENT_AI)
        with mock.patch("apps.ai.services.parent_insight.get_provider", return_value=parent_ai):
            insight = self._c(self.parent).post(f"/api/v1/parent/children/{self.student.id}/insight/")
        overview = self._c(self.parent).get(f"/api/v1/parent/children/{self.student.id}/overview/")
        children = self._c(self.parent).get("/api/v1/parent/children/")

        for r in (insight, overview, children):
            self.assertEqual(r.status_code, 200)
            text = r.content.decode()
            for secret in (SECRET, "Private companion reply text", "companion"):
                self.assertNotIn(secret, text)
        # …and nothing from the chat reaches the parent insight model either.
        self.assertEqual(len(parent_ai.calls), 1)
        self.assertNotIn(SECRET, json.dumps(parent_ai.calls[0]))

    def test_risk_message_always_points_to_a_trusted_adult(self):
        conv = self._new_chat()
        with self._patch(RecordingProvider(result={"reply": "That sounds really hard. Try a short walk."})):
            r = self._send(conv, "Sometimes I just want to disappear")
        self.assertIn("trusted adult", r.json()["assistant_message"]["content"])
        with self._patch(RecordingProvider(result={"reply": "Мне жаль, что тебе так тяжело."})):
            r = self._send(self._new_chat(lang="ru"), "Я не хочу жить", lang="ru")
        self.assertIn("взрослым, которому доверяешь", r.json()["assistant_message"]["content"])
        # Ordinary stress gets no crisis line; a reply that already points to an adult isn't doubled.
        with self._patch(RecordingProvider()):
            r = self._send(self._new_chat(), "I'm stressed about exams")
        self.assertEqual(r.json()["assistant_message"]["content"], REPLY)

    def test_payload_is_real_utf8_and_message_comes_first(self):
        fake = RecordingProvider(result={"reply": "Дробь — это часть целого."})
        with self._patch(fake):
            self._send(self._new_chat(lang="ru"), "Объясни дроби", lang="ru")
        self.assertIn("Объясни дроби", fake.calls[0]["raw"])  # not \u-escaped
        self.assertEqual(list(fake.calls[0]["payload"])[0], "student_message")
