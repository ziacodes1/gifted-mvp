from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.assessments.models import Assessment

from .models import AIInsight, InsightSource
from .services.provider import AnthropicProvider, LLMProvider, ProviderError

URL = "/api/v1/ai/profile-synthesis/"

VALID_AI = {
    "profile": {
        "headline": "Curiosity and building stand out so far",
        "summary": "Your current evidence suggests a strong pull toward building things. "
        "This profile will evolve as more evidence is collected.",
        "emerging_strengths": [{"title": "Technology & Building", "reason": "Chosen often."}],
        "exposure_gaps": ["There is not enough evidence yet about Helping People."],
        "uncertainty_notes": ["One assessment only."],
        "suggested_explorations": ["Build a paper bridge"],
    },
    "next_step": {
        "title": "Try a 30-minute bridge design challenge",
        "activity_type": "challenge",
        "reason": "Your realistic signal is currently strongest.",
        "signals_used": ["realistic", "made_up_key"],
        "intended_validation": "Whether the interest holds in practice.",
        "confidence_note": "A tentative suggestion.",
    },
}


class FakeProvider(LLMProvider):
    name, model = "fake", "fake-1"

    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result, error, 0

    def generate_structured(self, **kwargs):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class SessionFixtureMixin:
    """Student/parent fixtures + a helper that completes the seeded assessment."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        User = get_user_model()
        cls.student = User.objects.create_user("s1@test.dev", "pw12345!")
        cls.other = User.objects.create_user("s2@test.dev", "pw12345!")
        cls.parent = User.objects.create_user("p@test.dev", "pw12345!", role="PARENT")

    def _client(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def _complete_session(self, user) -> int:
        c = self._client(user)
        assessment = Assessment.objects.get()
        s = c.post(f"/api/v1/assessments/{assessment.id}/start/").json()
        for q in s["questions"]:
            c.post(
                f"/api/v1/assessment-sessions/{s['id']}/answer/",
                {"question_id": q["id"], "option_id": q["options"][0]["id"]},
                format="json",
            )
        r = c.post(f"/api/v1/assessment-sessions/{s['id']}/complete/")
        self.assertEqual(r.status_code, 200)
        return s["id"]


class ProfileSynthesisTests(SessionFixtureMixin, TestCase):
    def _patch(self, provider):
        return mock.patch("apps.ai.services.profile_synthesis.get_provider", return_value=provider)

    def test_ai_success_is_persisted_and_reused(self):
        sid = self._complete_session(self.student)
        fake = FakeProvider(result=VALID_AI)
        with self._patch(fake):
            r1 = self._client(self.student).post(URL, {"session_id": sid}, format="json")
            r2 = self._client(self.student).post(URL, {"session_id": sid}, format="json")
            r3 = self._client(self.student).post(URL, {}, format="json")  # latest completed
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["source"], "AI")
        self.assertEqual(r1.json()["next_step"]["signals_used"], ["realistic"])
        self.assertEqual(r2.json(), r1.json())
        self.assertEqual(r3.json()["session_id"], sid)
        self.assertEqual(fake.calls, 1)
        self.assertEqual(AIInsight.objects.count(), 1)
        insight = AIInsight.objects.get()
        self.assertEqual((insight.provider, insight.model), ("fake", "fake-1"))

    def test_provider_error_falls_back(self):
        sid = self._complete_session(self.student)
        with self._patch(FakeProvider(error=ProviderError("connection_error"))):
            r = self._client(self.student).post(URL, {"session_id": sid}, format="json")
        body = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(body["source"], "FALLBACK")
        self.assertTrue(body["profile"]["headline"])
        self.assertTrue(body["profile"]["emerging_strengths"])
        self.assertTrue(body["next_step"]["signals_used"])
        self.assertNotIn("connection_error", r.content.decode())

    def test_stub_provider_falls_back(self):
        sid = self._complete_session(self.student)
        with override_settings(AI_PROVIDER="stub"):
            r = self._client(self.student).post(URL, {"session_id": sid}, format="json")
        self.assertEqual(r.json()["source"], "FALLBACK")

    def test_invalid_or_unsafe_output_falls_back(self):
        sid = self._complete_session(self.student)
        bad_schema = {"profile": {"headline": "x"}}
        unsafe = {**VALID_AI, "profile": {**VALID_AI["profile"], "summary": "You should become an engineer."}}
        for bad in (bad_schema, unsafe):
            AIInsight.objects.all().delete()
            with self._patch(FakeProvider(result=bad)):
                r = self._client(self.student).post(URL, {"session_id": sid}, format="json")
            self.assertEqual(r.json()["source"], "FALLBACK")

    def test_fallback_upgrades_to_ai_after_cooldown(self):
        sid = self._complete_session(self.student)
        with self._patch(FakeProvider(error=ProviderError("x"))):
            self._client(self.student).post(URL, {"session_id": sid}, format="json")
        fake = FakeProvider(result=VALID_AI)
        with self._patch(fake):  # within cooldown: no retry
            r = self._client(self.student).post(URL, {"session_id": sid}, format="json")
        self.assertEqual((r.json()["source"], fake.calls), ("FALLBACK", 0))
        with self._patch(fake), mock.patch(
            "apps.ai.services.profile_synthesis.FALLBACK_RETRY_AFTER", new=__import__("datetime").timedelta(0)
        ):
            r = self._client(self.student).post(URL, {"session_id": sid}, format="json")
        self.assertEqual(r.json()["source"], "AI")
        self.assertEqual(AIInsight.objects.count(), 1)

    def test_other_student_cannot_access(self):
        sid = self._complete_session(self.student)
        with self._patch(FakeProvider(result=VALID_AI)):
            r = self._client(self.other).post(URL, {"session_id": sid}, format="json")
            r_latest = self._client(self.other).post(URL, {}, format="json")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r_latest.status_code, 404)
        self.assertEqual(self._client(self.parent).post(URL, {}, format="json").status_code, 403)
        self.assertEqual(APIClient().post(URL, {}, format="json").status_code, 401)

    def test_incomplete_session_rejected_and_client_scores_ignored(self):
        c = self._client(self.student)
        s = c.post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()
        r = c.post(URL, {"session_id": s["id"], "signals": [{"key": "x", "score": 100}]}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_anthropic_provider_maps_sdk_errors(self):
        import anthropic

        p = AnthropicProvider(api_key="sk-test", model="", timeout=1, effort="low")
        self.assertEqual(p.model, "claude-opus-5")
        req = mock.Mock()
        with mock.patch.object(
            p._client.beta.messages, "create", side_effect=anthropic.APIConnectionError(request=req)
        ):
            with self.assertRaises(ProviderError):
                p.generate_structured(system="s", prompt="p", schema={})


# --- Gemini provider (network fully mocked) ------------------------------------------

import json as _json  # noqa: E402
from types import SimpleNamespace  # noqa: E402

from google.genai import errors as genai_errors  # noqa: E402

from .services.provider import GeminiProvider, StubProvider, get_provider  # noqa: E402


def _gemini_response(payload, finish="STOP"):
    text = payload if isinstance(payload, str) else _json.dumps(payload)
    return SimpleNamespace(text=text, candidates=[SimpleNamespace(finish_reason=finish)])


class GeminiProviderTests(SessionFixtureMixin, TestCase):

    def _gemini(self, response=None, error=None, models=("models/gemini-3-flash", "models/gemini-3-flash-lite")):
        client = mock.MagicMock()
        client.models.list.return_value = [SimpleNamespace(name=n, supported_actions=["generateContent"]) for n in models]
        if error:
            client.models.generate_content.side_effect = error
        else:
            client.models.generate_content.return_value = response
        GeminiProvider._resolved.clear()
        with mock.patch("google.genai.Client", return_value=client):
            provider = GeminiProvider(api_key="test-key", model="", timeout=5)
        return provider, client

    def _post(self, provider, sid):
        with mock.patch("apps.ai.services.profile_synthesis.get_provider", return_value=provider):
            return self._client(self.student).post(URL, {"session_id": sid}, format="json")

    def test_selection_by_environment(self):
        with override_settings(AI_PROVIDER="stub"):
            self.assertIsInstance(get_provider(), StubProvider)
        with override_settings(AI_PROVIDER="gemini", GEMINI_API_KEY=""):
            self.assertIsInstance(get_provider(), StubProvider)  # missing key → graceful stub
        with override_settings(AI_PROVIDER="gemini", GEMINI_API_KEY="k", AI_MODEL="claude-opus-5"), mock.patch("google.genai.Client"):
            p = get_provider()
            self.assertIsInstance(p, GeminiProvider)
            self.assertEqual(p.model, "")  # a Claude model name is ignored → auto-select
        with override_settings(AI_PROVIDER="gemini", GEMINI_API_KEY="k", AI_MODEL="gemini-3-flash-lite"), mock.patch("google.genai.Client"):
            self.assertEqual(get_provider().model, "gemini-3-flash-lite")
        with override_settings(AI_PROVIDER="anthropic", AI_API_KEY="k"):
            self.assertIsInstance(get_provider(), AnthropicProvider)

    def test_success_structured_request_and_persistence(self):
        sid = self._complete_session(self.student)
        provider, client = self._gemini(_gemini_response(VALID_AI))
        r1 = self._post(provider, sid)
        r2 = self._post(provider, sid)
        self.assertEqual(r1.json()["source"], "AI")
        self.assertEqual(r2.json(), r1.json())
        self.assertEqual(client.models.generate_content.call_count, 1)  # reused on refresh
        kwargs = client.models.generate_content.call_args.kwargs
        self.assertEqual(kwargs["model"], "gemini-3-flash")  # auto-selected stable Flash
        config = kwargs["config"]
        self.assertEqual(config.response_mime_type, "application/json")
        self.assertIn("profile", config.response_json_schema["properties"])
        self.assertNotIn("additionalProperties", _json.dumps(config.response_json_schema))
        insight = AIInsight.objects.get()
        self.assertEqual((insight.provider, insight.model), ("gemini", "gemini-3-flash"))
        # Trusted compact input only: no question bank, no raw answers.
        self.assertNotIn("helper_text", kwargs["contents"])
        self.assertIn('"signals"', kwargs["contents"])

    def test_malformed_json_falls_back(self):
        sid = self._complete_session(self.student)
        provider, _ = self._gemini(_gemini_response("{not json"))
        self.assertEqual(self._post(provider, sid).json()["source"], "FALLBACK")

    def test_truncated_or_blocked_output_falls_back(self):
        sid = self._complete_session(self.student)
        provider, _ = self._gemini(_gemini_response(VALID_AI, finish="MAX_TOKENS"))
        self.assertEqual(self._post(provider, sid).json()["source"], "FALLBACK")

    def test_banned_phrase_falls_back(self):
        sid = self._complete_session(self.student)
        unsafe = {**VALID_AI, "profile": {**VALID_AI["profile"], "summary": "You should become a designer."}}
        provider, _ = self._gemini(_gemini_response(unsafe))
        self.assertEqual(self._post(provider, sid).json()["source"], "FALLBACK")

    def test_provider_errors_fall_back_without_leaking(self):
        sid = self._complete_session(self.student)
        quota = genai_errors.ClientError(429, {"error": {"code": 429, "message": "Quota exceeded for key test-key", "status": "RESOURCE_EXHAUSTED"}})
        provider, _ = self._gemini(error=quota)
        with self.assertLogs("apps.ai", level="WARNING") as logs:
            r = self._post(provider, sid)
        self.assertEqual((r.status_code, r.json()["source"]), (200, "FALLBACK"))
        self.assertIn("provider=gemini", logs.output[0])
        self.assertIn("reason=quota_exceeded", logs.output[0])
        self.assertNotIn("test-key", " ".join(logs.output) + r.content.decode())

    def test_error_categories(self):
        cases = [
            (genai_errors.ClientError(400, {"error": {"code": 400, "message": "API key not valid", "status": "INVALID_ARGUMENT"}}), "auth_failed"),
            (genai_errors.ClientError(404, {"error": {"code": 404, "message": "not found", "status": "NOT_FOUND"}}), "model_not_found"),
            (genai_errors.ServerError(503, {"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}}), "server_error_503"),
        ]
        for exc, reason in cases:
            provider, _ = self._gemini(error=exc)
            with self.assertRaises(ProviderError) as ctx:
                provider.generate_structured(system="s", prompt="p", schema={})
            self.assertEqual(str(ctx.exception), reason)

    def test_parent_insight_uses_same_provider_contract(self):
        from apps.parents.models import ParentChild
        from apps.parents.tests import PARENT_AI

        self._complete_session(self.student)
        ParentChild.objects.create(parent=self.parent, learner=self.student)
        provider, client = self._gemini(_gemini_response(PARENT_AI))
        with mock.patch("apps.ai.services.parent_insight.get_provider", return_value=provider):
            r = self._client(self.parent).post(f"/api/v1/parent/children/{self.student.id}/insight/")
            self._client(self.parent).post(f"/api/v1/parent/children/{self.student.id}/insight/")
        self.assertEqual(r.json()["parent_insight"]["source"], "AI")
        self.assertEqual(client.models.generate_content.call_count, 1)
        self.assertIn("support_at_home", client.models.generate_content.call_args.kwargs["config"].response_json_schema["properties"])


# --- Groq provider (network fully mocked) -----------------------------------------------

import httpx  # noqa: E402
import groq as groq_sdk  # noqa: E402

from .services.provider import FailoverProvider, GroqProvider  # noqa: E402


def _groq_response(payload, finish="stop"):
    text = payload if isinstance(payload, str) else _json.dumps(payload)
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason=finish, message=SimpleNamespace(content=text))])


def _groq_status(cls, status, code="x"):
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(status, request=req)
    return cls(f"status {status}", response=resp, body={"error": {"code": code, "message": "sensitive detail"}})


class GroqProviderTests(SessionFixtureMixin, TestCase):
    def _groq(self, response=None, error=None, model="openai/gpt-oss-20b"):
        client = mock.MagicMock()
        if error:
            client.chat.completions.create.side_effect = error
        else:
            client.chat.completions.create.return_value = response
        with mock.patch("groq.Groq", return_value=client):
            provider = GroqProvider(api_key="test-key", model=model, timeout=10, effort="medium")
        return provider, client

    def _post(self, provider, sid):
        with mock.patch("apps.ai.services.profile_synthesis.get_provider", return_value=provider):
            return self._client(self.student).post(URL, {"session_id": sid}, format="json")

    def test_selection_and_failover_wiring(self):
        with override_settings(AI_PROVIDER="groq", GROQ_API_KEY=""):
            self.assertIsInstance(get_provider(), StubProvider)
        with override_settings(AI_PROVIDER="groq", GROQ_API_KEY="k", AI_MODEL="", AI_SECONDARY_PROVIDER=""), mock.patch("groq.Groq"):
            p = get_provider()
            self.assertIsInstance(p, GroqProvider)
            self.assertEqual(p.model, "openai/gpt-oss-20b")
        with override_settings(AI_PROVIDER="groq", GROQ_API_KEY="k", AI_MODEL="gemini-3-flash"), mock.patch("groq.Groq"):
            self.assertEqual(get_provider().model, "openai/gpt-oss-20b")  # other provider's model ignored
        with override_settings(AI_PROVIDER="groq", GROQ_API_KEY="k", AI_SECONDARY_PROVIDER="gemini", GEMINI_API_KEY="g"), \
                mock.patch("groq.Groq"), mock.patch("google.genai.Client"):
            self.assertIsInstance(get_provider(), FailoverProvider)
        with override_settings(AI_PROVIDER="groq", GROQ_API_KEY="k", AI_SECONDARY_PROVIDER="gemini", GEMINI_API_KEY=""), mock.patch("groq.Groq"):
            self.assertIsInstance(get_provider(), GroqProvider)  # secondary without key → no failover

    def test_success_strict_structured_output_and_persistence(self):
        sid = self._complete_session(self.student)
        provider, client = self._groq(_groq_response(VALID_AI))
        r1, r2 = self._post(provider, sid), self._post(provider, sid)
        self.assertEqual(r1.json()["source"], "AI")
        self.assertEqual(r2.json(), r1.json())
        self.assertEqual(client.chat.completions.create.call_count, 1)  # persisted insight reused
        kwargs = client.chat.completions.create.call_args.kwargs
        rf = kwargs["response_format"]
        self.assertEqual((rf["type"], rf["json_schema"]["strict"]), ("json_schema", True))
        self.assertIn("profile", rf["json_schema"]["schema"]["properties"])
        self.assertEqual((kwargs["reasoning_effort"], kwargs["include_reasoning"]), ("medium", False))
        self.assertNotIn("helper_text", kwargs["messages"][1]["content"])
        insight = AIInsight.objects.get()
        self.assertEqual((insight.provider, insight.model), ("groq", "openai/gpt-oss-20b"))

    def test_failures_fall_back_with_safe_reasons(self):
        sid = self._complete_session(self.student)
        req = httpx.Request("POST", "https://api.groq.com")
        cases = [
            (_groq_status(groq_sdk.AuthenticationError, 401), "auth_failed"),
            (_groq_status(groq_sdk.RateLimitError, 429), "rate_limited"),
            (groq_sdk.APITimeoutError(request=req), "timeout"),
            (_groq_status(groq_sdk.InternalServerError, 503), "server_error"),
            (_groq_status(groq_sdk.BadRequestError, 400, "json_validate_failed"), "invalid_output"),  # after 1 retry
        ]
        for error, reason in cases:
            AIInsight.objects.all().delete()
            provider, _ = self._groq(error=error)
            with self.assertLogs("apps.ai", level="INFO") as logs:
                r = self._post(provider, sid)
            self.assertEqual((r.status_code, r.json()["source"]), (200, "FALLBACK"), reason)
            self.assertIn(f"provider=groq model=openai/gpt-oss-20b outcome=fallback", logs.output[-1])
            self.assertIn(f"reason={reason}", logs.output[-1])
            self.assertNotIn("sensitive detail", " ".join(logs.output) + r.content.decode())
            self.assertNotIn("test-key", " ".join(logs.output) + r.content.decode())

    def test_malformed_truncated_and_banned_outputs_fall_back(self):
        sid = self._complete_session(self.student)
        unsafe = {**VALID_AI, "profile": {**VALID_AI["profile"], "summary": "You should become an engineer."}}
        for response in (_groq_response("{oops"), _groq_response(VALID_AI, finish="length"), _groq_response(unsafe)):
            AIInsight.objects.all().delete()
            provider, _ = self._groq(response)
            self.assertEqual(self._post(provider, sid).json()["source"], "FALLBACK")

    def test_one_retry_on_malformed_output_only(self):
        sid = self._complete_session(self.student)
        provider, client = self._groq()
        client.chat.completions.create.side_effect = [_groq_response("{broken"), _groq_response(VALID_AI)]
        self.assertEqual(self._post(provider, sid).json()["source"], "AI")
        self.assertEqual(client.chat.completions.create.call_count, 2)
        AIInsight.objects.all().delete()
        provider, client = self._groq(error=_groq_status(groq_sdk.RateLimitError, 429))
        self.assertEqual(self._post(provider, sid).json()["source"], "FALLBACK")
        self.assertEqual(client.chat.completions.create.call_count, 1)  # no retry on rate limits

    def test_failover_only_on_transient_errors(self):
        primary, _ = self._groq(error=_groq_status(groq_sdk.RateLimitError, 429))
        secondary = FakeProvider(result={"ok": True})
        fo = FailoverProvider(primary, secondary)
        self.assertEqual(fo.generate_structured(system="s", prompt="p", schema={}), {"ok": True})
        self.assertEqual((fo.name, fo.model), ("fake", "fake-1"))  # logs/persistence show who answered
        primary, _ = self._groq(error=_groq_status(groq_sdk.AuthenticationError, 401))
        secondary = FakeProvider(result={"ok": True})
        with self.assertRaises(ProviderError):
            FailoverProvider(primary, secondary).generate_structured(system="s", prompt="p", schema={})
        self.assertEqual(secondary.calls, 0)  # bad key is not transient → deterministic fallback
