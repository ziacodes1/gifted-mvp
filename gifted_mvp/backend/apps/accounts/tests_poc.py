"""POC-hardening tests: production config, throttling, auth/token lifecycle, account deletion,
parent connection codes, assessment versioning, admin privacy, health, API docs, tracing."""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from apps.ai.models import AIInsight
from apps.ai.services.provider import ProviderError
from apps.ai.tests import VALID_AI, FakeProvider
from apps.assessments.models import Assessment, AssessmentSession
from apps.assessments.versioning import create_new_version, publish_version
from apps.diary.models import DiaryAttachment, DiaryEntry
from apps.parents.models import LearnerConnectionCode, ParentChild
from apps.questions.models import Question, QuestionOption
from apps.signals.models import ResponseSignalMap
from config.security import production_problems

User = get_user_model()
BACKEND = Path(settings.BASE_DIR)
STRONG_PW = "correct-horse-battery-7"
LOCMEM = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "poc-tests"}}


def run_settings(env: dict) -> subprocess.CompletedProcess:
    """Import settings in a fresh interpreter (settings fail at import time by design)."""
    code = (
        "import django, os; os.environ['DJANGO_SETTINGS_MODULE']='config.settings'; django.setup();"
        "from django.conf import settings as s;"
        "print(s.DEBUG, s.SESSION_COOKIE_SECURE, s.SECURE_HSTS_SECONDS, s.SECURE_SSL_REDIRECT, s.X_FRAME_OPTIONS)"
    )
    clean = {k: v for k, v in os.environ.items() if not k.startswith(("DJANGO_", "SECURE_"))}
    return subprocess.run([sys.executable, "-c", code], cwd=BACKEND, env={**clean, **env}, capture_output=True, text=True, timeout=60)


class ProductionConfigTests(TestCase):
    def test_production_fails_closed_without_safe_settings(self):
        r = run_settings({"DJANGO_ENV": "production", "DJANGO_DEBUG": "False", "DJANGO_ALLOWED_HOSTS": "pilot.example.org"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY", r.stderr)

        r = run_settings({"DJANGO_ENV": "production", "DJANGO_SECRET_KEY": "x" * 64, "DJANGO_DEBUG": "True", "DJANGO_ALLOWED_HOSTS": "pilot.example.org"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("DJANGO_DEBUG must be false", r.stderr)

        r = run_settings({"DJANGO_ENV": "production", "DJANGO_SECRET_KEY": "x" * 64, "DJANGO_DEBUG": "False", "DJANGO_ALLOWED_HOSTS": ""})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS", r.stderr)

    def test_production_starts_with_secure_defaults(self):
        r = run_settings({"DJANGO_ENV": "production", "DJANGO_SECRET_KEY": "k" * 64, "DJANGO_DEBUG": "False", "DJANGO_ALLOWED_HOSTS": "pilot.example.org"})
        self.assertEqual(r.returncode, 0, r.stderr)
        debug, cookie_secure, hsts, redirect, frame = r.stdout.split()
        self.assertEqual((debug, cookie_secure, redirect, frame), ("False", "True", "True", "DENY"))
        self.assertGreater(int(hsts), 0)

    def test_development_stays_convenient(self):
        r = run_settings({"DJANGO_ENV": "development"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.split()[0], "True")

    def test_problem_list(self):
        self.assertEqual(
            production_problems({"SECRET_KEY": "s" * 64, "DEBUG": False, "ALLOWED_HOSTS": ["a.org"], "AI_PROVIDER": "groq"}), []
        )
        self.assertEqual(len(production_problems({"SECRET_KEY": "short", "DEBUG": True, "ALLOWED_HOSTS": ["*"], "AI_PROVIDER": "x"})), 4)


class AuthAndThrottleTests(TestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        o = override_settings(PRIVATE_MEDIA_ROOT=Path(self.media))
        o.enable()
        self.addCleanup(o.disable)

    def _login(self, email, pw):
        return APIClient().post("/api/v1/auth/login/", {"email": email, "password": pw}, format="json")

    def test_registration_rules(self):
        c = APIClient()
        self.assertEqual(c.post("/api/v1/auth/register/", {"email": "a@t.dev", "password": "short1"}, format="json").status_code, 400)
        self.assertEqual(c.post("/api/v1/auth/register/", {"email": "b@t.dev", "password": "1234567890123"}, format="json").status_code, 400)
        r = c.post("/api/v1/auth/register/", {"email": "c@t.dev", "password": STRONG_PW, "role": "ADMIN"}, format="json")
        self.assertEqual(r.status_code, 400)  # ADMIN can never be self-assigned
        r = c.post("/api/v1/auth/register/", {"email": "d@t.dev", "password": STRONG_PW, "role": "PARENT"}, format="json")
        self.assertEqual((r.status_code, r.json()["role"]), (201, "PARENT"))
        self.assertFalse(User.objects.get(email="d@t.dev").is_staff)

    def test_refresh_rotates_and_logout_revokes(self):
        User.objects.create_user("u@t.dev", STRONG_PW)
        tokens = self._login("u@t.dev", STRONG_PW).json()
        r = APIClient().post("/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(r.status_code, 200)
        rotated = r.json()["refresh"]
        self.assertNotEqual(rotated, tokens["refresh"])
        # The old refresh token is blacklisted after rotation.
        self.assertEqual(APIClient().post("/api/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json").status_code, 401)

        # The SPA discards its access token before calling logout: the refresh token alone suffices.
        self.assertEqual(APIClient().post("/api/v1/auth/logout/", {"refresh": rotated}, format="json").status_code, 204)
        self.assertEqual(APIClient().post("/api/v1/auth/refresh/", {"refresh": rotated}, format="json").status_code, 401)
        self.assertEqual(APIClient().post("/api/v1/auth/logout/", {"refresh": "garbage"}, format="json").status_code, 204)

    def test_password_change_revokes_tokens(self):
        u = User.objects.create_user("p@t.dev", STRONG_PW)
        access = self._login("p@t.dev", STRONG_PW).json()["access"]
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION="Bearer " + access)
        self.assertEqual(c.get("/api/v1/auth/me/").status_code, 200)
        u.set_password("another-strong-pass-9")
        u.save()
        self.assertEqual(c.get("/api/v1/auth/me/").status_code, 401)

    def test_account_deletion_removes_learner_data_and_files(self):
        u = User.objects.create_user("del@t.dev", STRONG_PW)
        keep = User.objects.create_user("keep@t.dev", STRONG_PW)
        c = APIClient()
        c.force_authenticate(u)
        entry = c.post("/api/v1/diary/entries/", {"title": "private", "body": "words"}, format="json").json()
        buf = io.BytesIO()
        Image.new("RGB", (20, 20)).save(buf, "PNG")
        from django.core.files.uploadedfile import SimpleUploadedFile

        c.post(f"/api/v1/diary/entries/{entry['id']}/attachments/", {"file": SimpleUploadedFile("a.png", buf.getvalue(), "image/png")}, format="multipart")
        path = Path(DiaryAttachment.objects.get().image.path)
        self.assertTrue(path.exists())
        other = APIClient()
        other.force_authenticate(keep)
        other.post("/api/v1/diary/entries/", {"body": "not deleted"}, format="json")

        self.assertEqual(c.delete("/api/v1/auth/me/", {"password": "wrong-password-1"}, format="json").status_code, 400)
        self.assertEqual(c.delete("/api/v1/auth/me/", {"password": STRONG_PW}, format="json").status_code, 204)
        self.assertFalse(User.objects.filter(email="del@t.dev").exists())
        self.assertFalse(path.exists())
        self.assertEqual(DiaryEntry.objects.count(), 1)  # the other learner's entry stays

    @override_settings(CACHES=LOCMEM)
    def test_login_and_parent_connect_are_throttled(self):
        from django.core.cache import cache

        cache.clear()
        User.objects.create_user("t@t.dev", STRONG_PW)
        with mock.patch.object(ScopedRateThrottle, "THROTTLE_RATES", {**ScopedRateThrottle.THROTTLE_RATES, "auth": "3/min", "parent_connect": "2/hour"}):
            codes = [self._login("t@t.dev", "wrong-password-x").status_code for _ in range(4)]
            self.assertEqual(codes, [401, 401, 401, 429])
            parent = User.objects.create_user("par@t.dev", STRONG_PW, role="PARENT")
            c = APIClient()
            c.force_authenticate(parent)
            codes = [c.post("/api/v1/parent/children/connect/", {"code": "GFT-AAAA-AAAA"}, format="json").status_code for _ in range(3)]
            self.assertEqual(codes, [404, 404, 429])
        cache.clear()


class ParentCodeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.kid = User.objects.create_user("kid@t.dev", STRONG_PW, full_name="Kid One")
        cls.mum = User.objects.create_user("mum@t.dev", STRONG_PW, role="PARENT", full_name="Mum")
        cls.stranger = User.objects.create_user("str@t.dev", STRONG_PW, role="PARENT")

    def _c(self, u):
        c = APIClient()
        c.force_authenticate(u)
        return c

    def _connect(self, parent, code):
        return self._c(parent).post("/api/v1/parent/children/connect/", {"code": code}, format="json")

    def test_student_generates_single_use_expiring_code(self):
        r = self._c(self.kid).post("/api/v1/parent-access/code/")
        self.assertEqual(r.status_code, 201)
        code = r.json()["code"]
        self.assertRegex(code, r"^GFT-[A-Z2-9]{4}-[A-Z2-9]{4}$")
        self.assertEqual(self._connect(self.mum, code).status_code, 200)
        self.assertEqual(self._connect(self.stranger, code).status_code, 404)  # single use
        access = self._c(self.kid).get("/api/v1/parent-access/").json()
        self.assertIsNone(access["code"])
        self.assertEqual([p["display_name"] for p in access["parents"]], ["Mum"])

    def test_expired_revoked_and_regenerated_codes(self):
        code = self._c(self.kid).post("/api/v1/parent-access/code/").json()["code"]
        LearnerConnectionCode.objects.filter(code=code).update(expires_at=timezone.now() - timedelta(minutes=1))
        self.assertEqual(self._connect(self.mum, code).status_code, 404)

        code = self._c(self.kid).post("/api/v1/parent-access/code/").json()["code"]
        self.assertEqual(self._c(self.kid).delete("/api/v1/parent-access/code/").status_code, 204)
        self.assertEqual(self._connect(self.mum, code).status_code, 404)

        old = self._c(self.kid).post("/api/v1/parent-access/code/").json()["code"]
        new = self._c(self.kid).post("/api/v1/parent-access/code/").json()["code"]
        self.assertEqual(self._connect(self.mum, old).status_code, 404)  # regenerating replaces it
        self.assertEqual(self._connect(self.mum, new).status_code, 200)

    def test_student_can_remove_a_parent_and_roles_are_enforced(self):
        ParentChild.objects.create(parent=self.mum, learner=self.kid)
        self.assertEqual(self._c(self.mum).get(f"/api/v1/parent/children/{self.kid.id}/overview/").status_code, 200)
        self.assertEqual(self._c(self.kid).delete(f"/api/v1/parent-access/parents/{self.mum.id}/").status_code, 204)
        self.assertEqual(self._c(self.mum).get(f"/api/v1/parent/children/{self.kid.id}/overview/").status_code, 404)
        self.assertEqual(self._c(self.mum).post("/api/v1/parent-access/code/").status_code, 403)  # parents can't mint codes
        self.assertEqual(self._c(self.kid).post("/api/v1/parent/children/connect/", {"code": "GFT-AAAA-AAAA"}, format="json").status_code, 403)


class AssessmentVersioningTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        cls.student = User.objects.create_user("v@t.dev", STRONG_PW)
        cls.admin = User.objects.create_superuser("root@t.dev", STRONG_PW)

    def _complete(self, assessment):
        c = APIClient()
        c.force_authenticate(self.student)
        s = c.post(f"/api/v1/assessments/{assessment.id}/start/").json()
        for q in s["questions"]:
            c.post(f"/api/v1/assessment-sessions/{s['id']}/answer/", {"question_id": q["id"], "option_id": q["options"][0]["id"]}, format="json")
        c.post(f"/api/v1/assessment-sessions/{s['id']}/complete/")
        return AssessmentSession.objects.get(pk=s["id"])

    def test_session_records_versions_and_frozen_snapshot(self):
        from apps.ai.services.profile_synthesis import build_signal_input

        a = Assessment.objects.get()
        session = self._complete(a)
        self.assertEqual((session.assessment_version, session.scoring_version), (1, "s2"))
        self.assertEqual(session.result_snapshot["scoring_version"], "s2")
        before = build_signal_input(session)

        # Someone edits the scoring rules of the used version afterwards (e.g. via a shell):
        ResponseSignalMap.objects.filter(option__question__section__assessment=a).update(weight=0)
        self.assertEqual(build_signal_input(session)["signals"], before["signals"])  # never re-interpreted

    def test_new_version_is_a_full_copy_and_publish_switches(self):
        a = Assessment.objects.get()
        self._complete(a)
        self.assertTrue(a.is_locked)
        v2 = create_new_version(a)
        self.assertEqual((v2.version, v2.is_active, v2.previous_version_id), (2, False, a.id))
        count = lambda x: (Question.objects.filter(section__assessment=x).count(), QuestionOption.objects.filter(question__section__assessment=x).count(), ResponseSignalMap.objects.filter(option__question__section__assessment=x).count())  # noqa: E731
        self.assertEqual(count(v2), count(a))
        self.assertFalse(v2.is_locked)
        publish_version(v2)
        a.refresh_from_db()
        self.assertEqual((a.is_active, Assessment.objects.get(pk=v2.pk).is_active), (False, True))
        s2 = self._complete(Assessment.objects.get(pk=v2.pk))
        self.assertEqual(s2.assessment_version, 2)

    def test_admin_locks_used_content(self):
        a = Assessment.objects.get()
        q = Question.objects.filter(section__assessment=a).first()
        request = RequestFactory().get("/")
        request.user = self.admin
        qa = admin.site._registry[Question]
        self.assertNotIn("prompt", qa.get_readonly_fields(request, q))
        self._complete(a)
        self.assertIn("prompt", qa.get_readonly_fields(request, q))
        self.assertFalse(qa.has_delete_permission(request, q))
        ma = admin.site._registry[ResponseSignalMap]
        m = ResponseSignalMap.objects.filter(option__question__section__assessment=a).first()
        self.assertIn("weight", ma.get_readonly_fields(request, m))


class AdminPrivacyTests(TestCase):
    def test_private_learner_content_is_not_in_admin(self):
        from apps.assessments.models import AssessmentResponse
        from apps.companion.models import CompanionConversation, CompanionMessage
        from apps.missions.models import MissionResponse
        from apps.today.models import DailySpark, NudgeState

        registered = set(admin.site._registry)
        for model in (DiaryEntry, DiaryAttachment, CompanionConversation, CompanionMessage, AssessmentResponse, MissionResponse, DailySpark, NudgeState):
            self.assertNotIn(model, registered, model.__name__)

    def test_learner_records_are_read_only(self):
        from apps.engagement.models import ActivityEvent
        from apps.evidence.models import Evidence
        from apps.missions.models import MissionAttempt
        from apps.signals.models import LearnerSignal

        request = RequestFactory().get("/")
        request.user = User.objects.create_superuser("ro@t.dev", STRONG_PW)
        for model in (AssessmentSession, LearnerSignal, Evidence, MissionAttempt, ActivityEvent, AIInsight):
            ma = admin.site._registry[model]
            self.assertFalse(ma.has_change_permission(request), model.__name__)
            self.assertFalse(ma.has_delete_permission(request), model.__name__)

    def test_admin_changelists_render(self):
        call_command("seed_demo", verbosity=0, stdout=io.StringIO())
        c = self.client
        c.force_login(User.objects.get(email="admin@gifted.demo"))
        for url in ("assessments/assessment", "questions/question", "questions/questionoption", "signals/responsesignalmap",
                    "missions/mission", "engagement/reward", "engagement/rewardredemption", "ai/aiinsight", "accounts/user"):
            self.assertEqual(c.get(f"/admin/{url}/").status_code, 200, url)


class ObservabilityTests(TestCase):
    def test_health_live_ready_and_request_id(self):
        self.assertEqual(self.client.get("/api/v1/health/live/").status_code, 200)
        r = self.client.get("/api/v1/health/ready/", HTTP_X_REQUEST_ID="abc12345-demo")
        self.assertEqual((r.status_code, r.json()["checks"]["database"]), (200, "ok"))
        self.assertEqual(r["X-Request-ID"], "abc12345-demo")
        self.assertRegex(self.client.get("/api/v1/health/", HTTP_X_REQUEST_ID="bad id!").get("X-Request-ID"), r"^[0-9a-f]{32}$")

    def test_ready_fails_when_database_is_down_but_not_for_ai(self):
        with mock.patch("common.observability.connection.cursor", side_effect=Exception("db down")):
            r = self.client.get("/api/v1/health/ready/")
        self.assertEqual((r.status_code, r.json()["checks"]["database"]), (503, "error"))
        with override_settings(AI_PROVIDER="groq", GROQ_API_KEY=""):
            self.assertEqual(self.client.get("/api/v1/health/ready/").status_code, 200)

    def test_openapi_schema(self):
        r = self.client.get("/api/v1/schema/")
        self.assertEqual(r.status_code, 200)
        text = r.content.decode()
        for path in ("/api/v1/auth/login/", "/api/v1/passport/", "/api/v1/diary/entries/", "/api/v1/parent-access/code/"):
            self.assertIn(path, text)
        self.assertEqual(self.client.get("/api/v1/docs/").status_code, 200)


class AITraceabilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        cls.student = User.objects.create_user("ai@t.dev", STRONG_PW)

    def test_insight_records_versions_latency_and_failure_category(self):
        c = APIClient()
        c.force_authenticate(self.student)
        s = c.post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()
        for q in s["questions"]:
            c.post(f"/api/v1/assessment-sessions/{s['id']}/answer/", {"question_id": q["id"], "option_id": q["options"][0]["id"]}, format="json")
        c.post(f"/api/v1/assessment-sessions/{s['id']}/complete/")

        with mock.patch("apps.ai.services.profile_synthesis.get_provider", return_value=FakeProvider(error=ProviderError("rate_limited"))):
            c.post("/api/v1/ai/profile-synthesis/", {}, format="json")
        row = AIInsight.objects.get()
        self.assertEqual((row.source, row.failure_reason, row.prompt_version, row.schema_version), ("FALLBACK", "rate_limited", "p2", "ps1"))

        AIInsight.objects.all().delete()
        with mock.patch("apps.ai.services.profile_synthesis.get_provider", return_value=FakeProvider(result=VALID_AI)):
            c.post("/api/v1/ai/profile-synthesis/", {}, format="json")
        row = AIInsight.objects.get()
        self.assertEqual((row.source, row.provider, row.model, row.failure_reason), ("AI", "fake", "fake-1", ""))
        self.assertTrue(re.fullmatch(r"s2-p2", row.input_version))
