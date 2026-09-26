import io
import json
import shutil
import tempfile
import uuid
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from apps.ai.tests import FakeProvider
from apps.companion.models import CompanionMessage
from apps.companion.tests import RecordingProvider
from apps.evidence.models import Evidence
from apps.missions.tests import ANSWERS, SLUG
from apps.parents.models import ParentChild
from apps.parents.tests import PARENT_AI
from apps.signals.models import LearnerSignal

from .models import DiaryAttachment, DiaryEntry

SECRET_TITLE = "Secret diary title xyz"
SECRET_BODY = "Nobody else should ever read this private diary sentence."
SECRET_TAG = "secret-tag-qqq"
NO_MODEL = FakeProvider(error=AssertionError("the diary must never call a model"))


def png_bytes(size=(64, 48), color=(20, 120, 80), fmt="PNG", exif=None) -> bytes:
    buf = io.BytesIO()
    kwargs = {"exif": exif} if exif is not None else {}
    Image.new("RGB", size, color).save(buf, fmt, **kwargs)
    return buf.getvalue()


class DiaryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        call_command("seed_demo_mission", verbosity=0)
        User = get_user_model()
        cls.student = User.objects.create_user("kid@test.dev", "pw12345!", full_name="Ada Lovelace")
        cls.other = User.objects.create_user("kid2@test.dev", "pw12345!")
        cls.parent = User.objects.create_user("mum@test.dev", "pw12345!", role="PARENT")
        ParentChild.objects.create(parent=cls.parent, learner=cls.student)

    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media, ignore_errors=True)
        override = override_settings(PRIVATE_MEDIA_ROOT=Path(self.media))
        override.enable()
        self.addCleanup(override.disable)
        # Any model call from diary endpoints is a bug.
        for target in ("apps.ai.services.profile_synthesis.get_provider", "apps.ai.services.companion.get_provider"):
            patcher = mock.patch(target, return_value=NO_MODEL)
            patcher.start()
            self.addCleanup(patcher.stop)

    def _c(self, user=None, lang=None):
        c = APIClient()
        c.force_authenticate(user or self.student)
        if lang:
            c.credentials(HTTP_ACCEPT_LANGUAGE=lang)
        return c

    def _create(self, user=None, **data):
        payload = {"title": SECRET_TITLE, "body": SECRET_BODY, "mood": "very_low", "tags": [SECRET_TAG]} | data
        return self._c(user).post("/api/v1/diary/entries/", payload, format="json")

    def _photo(self, entry_id, content=None, name="photo.png", user=None):
        upload = SimpleUploadedFile(name, content if content is not None else png_bytes(), content_type="image/png")
        return self._c(user).post(f"/api/v1/diary/entries/{entry_id}/attachments/", {"file": upload}, format="multipart")

    # --- CRUD ---------------------------------------------------------------------

    def test_manual_crud_without_ai(self):
        r = self._create(stickers=[{"id": "leaf", "slot": 0}, {"id": "bomb", "slot": 1}, {"id": "star", "slot": 0}],
                         tags=["#School", "school", " friends  "])
        self.assertEqual(r.status_code, 201)
        entry = r.json()
        self.assertEqual(entry["source"], "MANUAL")
        self.assertEqual(entry["tags"], ["School", "friends"])  # cleaned + de-duplicated
        self.assertEqual(entry["stickers"], [{"id": "leaf", "slot": 0}])  # unknown/duplicate slots dropped

        eid = entry["id"]
        self.assertEqual(self._c().get(f"/api/v1/diary/entries/{eid}/").json()["body"], SECRET_BODY)
        r = self._c().patch(f"/api/v1/diary/entries/{eid}/", {"body": "Edited words", "mood": ""}, format="json")
        self.assertEqual((r.json()["body"], r.json()["mood"], r.json()["title"]), ("Edited words", None, SECRET_TITLE))
        self.assertEqual(self._c().get("/api/v1/diary/entries/").json()["count"], 1)
        self.assertEqual(self._c().delete(f"/api/v1/diary/entries/{eid}/").status_code, 204)
        self.assertEqual(DiaryEntry.objects.count(), 0)

    def test_validation(self):
        self.assertEqual(self._create(title="", body="   ").status_code, 400)
        self.assertEqual(self._create(mood="devastated").status_code, 400)
        self.assertEqual(self._create(body="x" * 10_001).status_code, 400)

    def test_other_student_404_parent_403_anonymous_401(self):
        eid = self._create().json()["id"]
        pid = self._photo(eid).json()["id"]
        other = self._c(self.other)
        for url in (f"/api/v1/diary/entries/{eid}/", f"/api/v1/diary/attachments/{pid}/"):
            self.assertEqual(other.get(url).status_code, 404)
            self.assertEqual(other.delete(url).status_code, 404)
        self.assertEqual(other.patch(f"/api/v1/diary/entries/{eid}/", {"body": "hack"}, format="json").status_code, 404)
        self.assertEqual(self._photo(eid, user=self.other).status_code, 404)
        self.assertEqual(other.get("/api/v1/diary/entries/").json()["count"], 0)
        self.assertEqual(other.get("/api/v1/diary/overview/").json()["pages_filled"], 0)

        parent = self._c(self.parent)
        for url in ("/api/v1/diary/entries/", f"/api/v1/diary/entries/{eid}/", f"/api/v1/diary/attachments/{pid}/", "/api/v1/diary/overview/"):
            self.assertEqual(parent.get(url).status_code, 403)
            self.assertEqual(APIClient().get(url).status_code, 401)
        self.assertEqual(DiaryEntry.objects.get().body, SECRET_BODY)

    # --- photos -------------------------------------------------------------------

    def test_photo_upload_is_reencoded_private_and_owned(self):
        eid = self._create().json()["id"]
        exif = Image.Exif()
        exif[0x010F] = "SpyCam"  # camera make; metadata must not survive
        r = self._photo(eid, png_bytes(size=(3000, 1500), fmt="JPEG", exif=exif), name="IMG_1.jpg")
        self.assertEqual(r.status_code, 201)
        self.assertEqual((r.json()["width"], r.json()["height"]), (1600, 800))

        stored = DiaryAttachment.objects.get()
        path = Path(stored.image.path)
        self.assertTrue(str(path).startswith(self.media))  # private root, not the public MEDIA_ROOT
        self.assertEqual(path.suffix, ".webp")
        with Image.open(path) as saved:
            self.assertEqual(saved.format, "WEBP")
            self.assertNotIn(0x010F, saved.getexif())

        got = self._c().get(f"/api/v1/diary/attachments/{stored.id}/")
        self.assertEqual((got.status_code, got["Content-Type"]), (200, "image/webp"))
        self.assertIn("private", got["Cache-Control"])
        self.assertEqual(self._c().get(f"/api/v1/diary/entries/{eid}/").json()["photos"][0]["id"], stored.id)

        self.assertEqual(self._c().delete(f"/api/v1/diary/entries/{eid}/").status_code, 204)
        self.assertFalse(path.exists())  # the file goes with the entry

    def test_invalid_uploads_rejected(self):
        eid = self._create().json()["id"]
        cases = {
            "not_an_image": (b"#!/bin/sh\nrm -rf /\n", "run.jpg"),
            "unsupported_type": (png_bytes(fmt="GIF"), "a.gif"),
        }
        for code, (content, name) in cases.items():
            r = self._photo(eid, content, name)
            self.assertEqual(r.status_code, 400, code)
            self.assertIn(code, json.dumps(r.json()))
        with mock.patch("apps.diary.services.MAX_PHOTO_BYTES", 100):
            self.assertIn("too_large", json.dumps(self._photo(eid).json()))
        for _ in range(4):
            self.assertEqual(self._photo(eid).status_code, 201)
        self.assertIn("too_many", json.dumps(self._photo(eid).json()))
        self.assertEqual(DiaryAttachment.objects.count(), 4)

    # --- overview -------------------------------------------------------------------

    def test_overview_counts_real_entries(self):
        empty = self._c().get("/api/v1/diary/overview/").json()
        self.assertEqual((empty["pages_filled"], empty["page_target"], empty["recent_entries"]), (0, 100, []))
        for i in range(3):
            self._create(title=f"Day {i}", mood="good" if i else "")
        body = self._c().get("/api/v1/diary/overview/").json()
        self.assertEqual(body["pages_filled"], 3)
        self.assertEqual(len(body["book_pages"]), 3)
        self.assertEqual(len(body["mood_week"]), 7)
        self.assertIn("good", [d["mood"] for d in body["mood_week"]])

    # --- Companion → Diary -------------------------------------------------------------

    def _chat(self, text, suggest=True):
        conv = self._c().post("/api/v1/companion/conversations/").json()["id"]
        fake = RecordingProvider(result={"reply": "That sounds like a proud moment.", "suggest_diary": suggest})
        with mock.patch("apps.ai.services.companion.get_provider", return_value=fake):
            r = self._c().post(
                f"/api/v1/companion/conversations/{conv}/messages/",
                {"content": text, "client_id": str(uuid.uuid4())},
                format="json",
            )
        return conv, r.json()

    def test_companion_offer_needs_explicit_action_and_never_duplicates(self):
        text = "Today I finally presented in class. I was nervous, but I felt proud afterwards!"
        conv, turn = self._chat(text)
        offer = turn["assistant_message"]["diary"]
        self.assertEqual(offer["offer"], "OFFERED")
        self.assertEqual(DiaryEntry.objects.count(), 0)  # offering saves nothing

        pending = self._c().get("/api/v1/diary/overview/").json()["pending_moment"]
        self.assertEqual(pending["student_message_id"], offer["student_message_id"])
        draft = self._c().post("/api/v1/diary/companion-draft/", {"message_id": offer["student_message_id"]}, format="json").json()
        self.assertEqual(draft["draft"]["body"], text)  # the student's own words only
        self.assertEqual(draft["draft"]["title"], "Today I finally presented in class")
        self.assertNotIn("proud moment", json.dumps(draft))  # no Companion text copied in
        self.assertEqual(DiaryEntry.objects.count(), 0)  # a draft is not persisted

        save = {**draft["draft"], "mood": "great"}
        first = self._c().post("/api/v1/diary/entries/", save, format="json")
        again = self._c().post("/api/v1/diary/entries/", save, format="json")
        self.assertEqual((first.status_code, again.status_code), (201, 200))
        self.assertEqual(first.json()["id"], again.json()["id"])
        self.assertEqual(first.json()["source"], "COMPANION")
        self.assertEqual(DiaryEntry.objects.count(), 1)

        self.assertIsNone(self._c().get("/api/v1/diary/overview/").json()["pending_moment"])  # saved → gone
        redraft = self._c().post("/api/v1/diary/companion-draft/", {"message_id": offer["student_message_id"]}, format="json").json()
        self.assertEqual(redraft["existing_entry_id"], first.json()["id"])
        messages = self._c().get(f"/api/v1/companion/conversations/{conv}/").json()["messages"]
        self.assertEqual(messages[1]["diary"]["entry_id"], first.json()["id"])
        moments = self._c().get("/api/v1/diary/entries/?source=COMPANION").json()
        self.assertEqual(moments["count"], 1)

    def test_draft_only_from_own_student_message(self):
        _, turn = self._chat("I planted a tree with my grandad today and loved it.")
        assistant_id = turn["assistant_message"]["id"]
        student_id = turn["user_message"]["id"]
        self.assertEqual(self._c().post("/api/v1/diary/companion-draft/", {"message_id": assistant_id}, format="json").status_code, 404)
        self.assertEqual(self._c(self.other).post("/api/v1/diary/companion-draft/", {"message_id": student_id}, format="json").status_code, 404)
        r = self._c(self.other).post("/api/v1/diary/entries/", {"body": "x", "companion_message_id": student_id}, format="json")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self._c(self.parent).post("/api/v1/diary/companion-draft/", {"message_id": student_id}, format="json").status_code, 403)

    def test_keep_only_in_chat_and_no_offer_for_questions_or_risk(self):
        conv, turn = self._chat("I scored my first goal today and my team cheered.")
        aid = turn["assistant_message"]["id"]
        self.assertEqual(self._c(self.other).post(f"/api/v1/companion/messages/{aid}/dismiss-diary-offer/").status_code, 404)
        self.assertEqual(self._c().post(f"/api/v1/companion/messages/{aid}/dismiss-diary-offer/").status_code, 204)
        self.assertEqual(CompanionMessage.objects.get(pk=aid).diary_offer, "DISMISSED")
        self.assertIsNone(self._c().get("/api/v1/diary/overview/").json()["pending_moment"])

        _, q = self._chat("What is a fraction?", suggest=False)
        self.assertEqual(q["assistant_message"]["diary"]["offer"], "NONE")
        _, risk = self._chat("I want to disappear, nobody would notice.", suggest=True)
        self.assertEqual(risk["assistant_message"]["diary"]["offer"], "NONE")
        self.assertEqual(DiaryEntry.objects.count(), 0)

    # --- privacy + no evidence ---------------------------------------------------------

    def _progress(self):
        c = self._c()
        from apps.assessments.models import Assessment

        s = c.post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()
        for q in s["questions"]:
            c.post(f"/api/v1/assessment-sessions/{s['id']}/answer/", {"question_id": q["id"], "option_id": q["options"][0]["id"]}, format="json")
        c.post(f"/api/v1/assessment-sessions/{s['id']}/complete/")
        a = c.post(f"/api/v1/missions/{SLUG}/start/").json()
        steps = {st["key"]: st["id"] for st in a["mission"]["steps"]}
        for key, data in ANSWERS.items():
            c.post(f"/api/v1/mission-attempts/{a['id']}/answer/", {"step_id": steps[key], "response": data}, format="json")
        c.post(f"/api/v1/mission-attempts/{a['id']}/complete/")

    def test_diary_never_reaches_parents_ai_passport_or_evidence(self):
        self._progress()
        signals_before = list(LearnerSignal.objects.filter(learner=self.student).values_list("signal__key", "score"))
        evidence_before = Evidence.objects.filter(learner=self.student).count()
        passport_before = self._c().get("/api/v1/passport/").json()["version"]

        eid = self._create(stickers=[{"id": "heart", "slot": 2}]).json()["id"]
        self._photo(eid)
        self._chat("I felt really proud of my drawing today.")  # companion AI context check below

        self.assertEqual(Evidence.objects.filter(learner=self.student).count(), evidence_before)
        self.assertEqual(list(LearnerSignal.objects.filter(learner=self.student).values_list("signal__key", "score")), signals_before)
        passport = self._c().get("/api/v1/passport/")
        self.assertEqual(passport.json()["version"], passport_before)

        parent_ai = RecordingProvider(result=PARENT_AI)
        with mock.patch("apps.ai.services.parent_insight.get_provider", return_value=parent_ai):
            insight = self._c(self.parent).post(f"/api/v1/parent/children/{self.student.id}/insight/")
        overview = self._c(self.parent).get(f"/api/v1/parent/children/{self.student.id}/overview/")
        children = self._c(self.parent).get("/api/v1/parent/children/")
        for r in (insight, overview, children, passport):
            self.assertEqual(r.status_code, 200)
            text = r.content.decode()
            for secret in (SECRET_TITLE, SECRET_BODY, SECRET_TAG, "very_low", "diary", "heart"):
                self.assertNotIn(secret, text)
        self.assertEqual(len(parent_ai.calls), 1)
        prompt = parent_ai.calls[0]["raw"]
        for secret in (SECRET_TITLE, SECRET_BODY, SECRET_TAG, "very_low", "mood"):
            self.assertNotIn(secret, prompt)

    def test_companion_context_contains_no_diary(self):
        self._create()
        conv = self._c().post("/api/v1/companion/conversations/").json()["id"]
        fake = RecordingProvider(result={"reply": "Hi!", "suggest_diary": False})
        with mock.patch("apps.ai.services.companion.get_provider", return_value=fake):
            self._c().post(f"/api/v1/companion/conversations/{conv}/messages/", {"content": "hi", "client_id": str(uuid.uuid4())}, format="json")
        for secret in (SECRET_TITLE, SECRET_BODY, SECRET_TAG, "very_low"):
            self.assertNotIn(secret, fake.calls[0]["raw"])

    def test_user_content_is_never_translated(self):
        uz = "Bugun men do‘stlarim bilan tog‘ga chiqdim."
        eid = self._create(title="Tog‘da", body=uz).json()["id"]
        for lang in ("en", "ru", "uz"):
            body = self._c(lang=lang).get(f"/api/v1/diary/entries/{eid}/").json()
            self.assertEqual((body["title"], body["body"]), ("Tog‘da", uz))
