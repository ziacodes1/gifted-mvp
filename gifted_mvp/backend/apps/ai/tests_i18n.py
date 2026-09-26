"""Localization: Accept-Language → localized server content + language-aware AI.

Language must change presentation only — never sessions, responses, scores,
mappings, evidence or Passport state.
"""
import copy
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from apps.assessments.models import Assessment, AssessmentSession
from apps.evidence.models import SignalEvidence
from apps.missions.tests import ANSWERS, SLUG
from apps.parents.models import ParentChild
from apps.parents.tests import PARENT_AI
from apps.signals.models import LearnerSignal
from common.i18n import normalize_language, tr

from .models import AIInsight, GenerationType, InsightSource
from .schemas import PROFILE_SYNTHESIS_JSON_SCHEMA
from .services.provider import LLMProvider, ProviderError
from .tests import VALID_AI

UZ_AI = copy.deepcopy(VALID_AI)
UZ_AI["profile"]["headline"] = "Sizda qurishga qiziqishning dastlabki belgilari ko‘rinmoqda"
UZ_AI["profile"]["summary"] = "Hozirgi ma’lumotlarga ko‘ra, sizni narsalarni yasash qiziqtiradi."

PARENT_UZ = {
    "summary": "Hozirgi ma’lumotlar farzandingizda dizaynga dastlabki qiziqishni ko‘rsatmoqda.",
    "what_we_are_seeing": [{"title": "Dizaynga qiziqish", "explanation": "Testdagi ko‘p javoblarda tanlangan."}],
    "what_is_still_unclear": ["Odamlarga yordam berish bo‘yicha hali ma’lumot kam."],
    "support_at_home": [
        {"title": "Tajriba haqida so‘rang", "action": "Nima eng qiziq bo‘lganini so‘rang."},
        {"title": "Kichik narsadan boshlang", "action": "Qisqa amaliy mashg‘ulot taklif qiling."},
    ],
    "conversation_starter": "Senga nima ko‘proq yoqdi?",
    "caution": "Hozircha izlanish erta qaror qabul qilishdan foydaliroq.",
}


class RecordingProvider(LLMProvider):
    """Returns a result per requested language and records every call."""

    name, model = "fake", "fake-1"

    def __init__(self, by_language=None, error=None):
        self.by_language, self.error, self.calls = by_language or {}, error, []

    def generate_structured(self, *, system, prompt, schema, max_tokens=2000):
        lang = "uz" if "Uzbek" in system else "ru" if "Russian" in system else "en"
        self.calls.append({"system": system, "prompt": prompt, "schema": schema, "lang": lang})
        if self.error:
            raise self.error
        return copy.deepcopy(self.by_language[lang])


class NormalizeLanguageTests(SimpleTestCase):
    def test_supported_unsupported_and_regional(self):
        self.assertEqual(normalize_language("uz"), "uz")
        self.assertEqual(normalize_language("ru-RU,ru;q=0.9,en;q=0.8"), "ru")
        self.assertEqual(normalize_language("fr-FR, de;q=0.5"), "en")
        self.assertEqual(normalize_language("fr, uz;q=0.4"), "uz")
        self.assertEqual(normalize_language(None), "en")
        self.assertEqual(normalize_language(""), "en")


class Fixture:
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        call_command("seed_demo_mission", verbosity=0)
        User = get_user_model()
        cls.student = User.objects.create_user("lang@test.dev", "pw12345!")
        cls.twin = User.objects.create_user("twin@test.dev", "pw12345!")
        cls.parent = User.objects.create_user("lang-parent@test.dev", "pw12345!", role="PARENT")
        ParentChild.objects.create(parent=cls.parent, learner=cls.student)

    def _c(self, user, lang=None):
        c = APIClient(**({"HTTP_ACCEPT_LANGUAGE": lang} if lang else {}))
        c.force_authenticate(user)
        return c

    def _start(self, user, lang=None):
        return self._c(user, lang).post(f"/api/v1/assessments/{Assessment.objects.get().id}/start/").json()

    def _answer_all(self, user, langs=("en",)):
        """Answer every question with its first option, cycling request languages."""
        s = self._start(user, langs[0])
        for i, q in enumerate(s["questions"]):
            r = self._c(user, langs[i % len(langs)]).post(
                f"/api/v1/assessment-sessions/{s['id']}/answer/",
                {"question_id": q["id"], "option_id": q["options"][0]["id"]},
                format="json",
            )
            self.assertEqual(r.status_code, 200)
        return s["id"]

    def _complete(self, user, lang="en", langs=("en",)):
        sid = self._answer_all(user, langs)
        r = self._c(user, lang).post(f"/api/v1/assessment-sessions/{sid}/complete/")
        self.assertEqual(r.status_code, 200)
        return sid, r.json()

    def _do_mission(self, user, langs=("en",)):
        a = self._c(user, langs[0]).post(f"/api/v1/missions/{SLUG}/start/").json()
        steps = {s["key"]: s["id"] for s in a["mission"]["steps"]}
        for i, (key, data) in enumerate(ANSWERS.items()):
            r = self._c(user, langs[i % len(langs)]).post(
                f"/api/v1/mission-attempts/{a['id']}/answer/", {"step_id": steps[key], "response": data}, format="json"
            )
            self.assertEqual(r.status_code, 200)
        return self._c(user, langs[-1]).post(f"/api/v1/mission-attempts/{a['id']}/complete/").json()


class LocalizedContentTests(Fixture, TestCase):
    def test_assessment_payload_is_localized_with_stable_ids_and_order(self):
        en = self._start(self.student, "en")
        uz = self._c(self.student, "uz").get(f"/api/v1/assessment-sessions/{en['id']}/").json()
        ru = self._c(self.student, "ru").get(f"/api/v1/assessment-sessions/{en['id']}/").json()
        self.assertEqual(en["questions"][0]["prompt"][:10], "Your schoo")
        self.assertIn("Maktab", uz["questions"][0]["prompt"])
        self.assertIn("Школа", ru["questions"][0]["prompt"])
        self.assertEqual(uz["assessment"]["title"], "Kashfiyot testi")
        # scenario inside content JSON is localized too
        scenario = next(q for q in ru["questions"] if q["type"] == "SCENARIO_CHOICE")
        self.assertIn("проекта", scenario["content"]["scenario"])
        for other in (uz, ru):
            self.assertEqual([q["id"] for q in other["questions"]], [q["id"] for q in en["questions"]])
            self.assertEqual(
                [[o["id"] for o in q["options"]] for q in other["questions"]],
                [[o["id"] for o in q["options"]] for q in en["questions"]],
            )
            # puzzle glyph data / images are untouched
            self.assertEqual([q["content"].get("stimulus") for q in other["questions"]], [q["content"].get("stimulus") for q in en["questions"]])
            self.assertEqual([[o["image"] for o in q["options"]] for q in other["questions"]], [[o["image"] for o in q["options"]] for q in en["questions"]])

    def test_unsupported_language_falls_back_to_english(self):
        s = self._start(self.student, "fr-FR,de;q=0.8")
        self.assertTrue(s["questions"][0]["prompt"].startswith("Your school"))
        r = self._c(self.student, "fr").get("/api/v1/missions/")
        self.assertEqual(r.json()[0]["title"], "Design a Better School Bag")
        self.assertEqual(r["Content-Language"], "en")

    def test_mission_payload_is_localized_but_keys_are_not(self):
        en = self._c(self.student, "en").get(f"/api/v1/missions/{SLUG}/").json()
        uz = self._c(self.student, "uz").get(f"/api/v1/missions/{SLUG}/").json()
        ru = self._c(self.student, "ru").get(f"/api/v1/missions/{SLUG}/").json()
        self.assertEqual(uz["title"], "Yaxshiroq maktab sumkasini loyihalang")
        self.assertEqual(ru["time_label"], "5–8 мин")
        self.assertEqual(ru["intro_steps"][0]["title"], "Познакомься с пользователями")
        for other in (uz, ru):
            for a, b in zip(en["steps"], other["steps"]):
                self.assertEqual((a["id"], a["key"], a["type"]), (b["id"], b["key"], b["type"]))
                self.assertNotEqual(a["title"], b["title"])
                for oa, ob in zip(a["content"].get("options", []), b["content"].get("options", [])):
                    self.assertEqual({k: oa[k] for k in ("key", "icon") if k in oa}, {k: ob[k] for k in ("key", "icon") if k in ob})
                    self.assertEqual(oa.get("cost"), ob.get("cost"))
                    self.assertNotEqual(oa["label"], ob["label"])
        budget = next(s for s in ru["steps"] if s["key"] == "prioritize")["content"]
        self.assertEqual(budget["budget"], 10)
        self.assertEqual(budget["options"][0]["label"], "Более прочный и лёгкий материал")

    def test_every_seeded_signal_has_uz_and_ru_labels(self):
        from apps.signals.models import Signal

        for s in Signal.objects.filter(is_active=True):
            self.assertNotEqual(tr(s, "label", "uz"), s.label, s.key)
            self.assertNotEqual(tr(s, "label", "ru"), s.label, s.key)
            self.assertEqual(tr(s, "label", "en"), s.label)


class LanguageSwitchKeepsStateTests(Fixture, TestCase):
    def test_switching_mid_assessment_keeps_session_answers_order_and_scores(self):
        s = self._start(self.student, "en")
        qs = s["questions"]
        for q in qs[:4]:
            self._c(self.student, "en").post(
                f"/api/v1/assessment-sessions/{s['id']}/answer/",
                {"question_id": q["id"], "option_id": q["options"][0]["id"]},
                format="json",
            )
        again = self._start(self.student, "uz")  # revisit in Uzbek: resumes, no new session
        self.assertEqual(again["id"], s["id"])
        self.assertEqual(AssessmentSession.objects.filter(learner=self.student).count(), 1)
        self.assertEqual(len(again["responses"]), 4)
        self.assertEqual([q["id"] for q in again["questions"]], [q["id"] for q in qs])
        self.assertIn("Kashf", again["assessment"]["title"])
        for q in qs[4:]:
            self._c(self.student, "uz").post(
                f"/api/v1/assessment-sessions/{s['id']}/answer/",
                {"question_id": q["id"], "option_id": q["options"][0]["id"]},
                format="json",
            )
        done = self._c(self.student, "uz").post(f"/api/v1/assessment-sessions/{s['id']}/complete/").json()

        # Same answers, English only → identical scores.
        _, twin = self._complete(self.twin, "en")
        strip = lambda rows: sorted((r["key"], r["score"], r["confidence"]) for r in rows)  # noqa: E731
        self.assertEqual(strip(done["signals"]), strip(twin["signals"]))
        mine = {(ls.signal.key, ls.score, ls.evidence_count, ls.opportunity_count) for ls in LearnerSignal.objects.filter(learner=self.student)}
        theirs = {(ls.signal.key, ls.score, ls.evidence_count, ls.opportunity_count) for ls in LearnerSignal.objects.filter(learner=self.twin)}
        self.assertEqual(mine, theirs)
        # labels follow the language of the request, keys don't
        self.assertIn("Texnologiya va qurish", {r["label"] for r in done["signals"]})

    def test_switching_mid_mission_keeps_attempt_and_evidence_mapping(self):
        with mock.patch("apps.ai.services.profile_synthesis.get_provider", return_value=RecordingProvider(error=ProviderError("x"))):
            self._complete(self.student)
            self._complete(self.twin)
        mixed = self._do_mission(self.student, langs=("en", "uz", "ru"))
        plain = self._do_mission(self.twin, langs=("en",))
        self.assertTrue(mixed["evidence_created"])
        rows = lambda user: sorted(  # noqa: E731
            (e.signal.key, e.kind, str(e.weight)) for e in SignalEvidence.objects.filter(evidence__learner=user)
        )
        self.assertEqual(rows(self.student), rows(self.twin))
        self.assertEqual(mixed["passport"], plain["passport"])
        # Completed mission shows its localized title in the Passport
        p = self._c(self.student, "ru").get("/api/v1/passport/").json()
        self.assertEqual(p["recent_evidence"][0]["title"], "Придумай школьный рюкзак получше")
        self.assertEqual(p["recent_evidence"][0]["source_label"], "Миссия")
        self.assertEqual(p["journey"][0]["label"], "Открытие")


class ProfileInsightLanguageTests(Fixture, TestCase):
    URL = "/api/v1/ai/profile-synthesis/"

    def _patch(self, provider):
        return mock.patch("apps.ai.services.profile_synthesis.get_provider", return_value=provider)

    def test_language_reaches_prompt_and_insights_are_cached_per_language(self):
        sid, _ = self._complete(self.student)
        fake = RecordingProvider({"en": VALID_AI, "uz": UZ_AI, "ru": VALID_AI})
        with self._patch(fake):
            en = self._c(self.student, "en").post(self.URL, {}, format="json").json()
            uz = self._c(self.student, "uz").post(self.URL, {}, format="json").json()
            uz_again = self._c(self.student, "uz").post(self.URL, {}, format="json").json()
            en_again = self._c(self.student, "en").post(self.URL, {}, format="json").json()

        self.assertEqual([c["lang"] for c in fake.calls], ["en", "uz"])  # EN not reused for UZ; both reused later
        self.assertNotIn("Output language", fake.calls[0]["system"])  # English prompt unchanged
        self.assertIn("Uzbek", fake.calls[1]["system"])
        self.assertIn("JSON keys stay exactly as specified in English", fake.calls[1]["system"])
        self.assertIs(fake.calls[1]["schema"], PROFILE_SYNTHESIS_JSON_SCHEMA)
        self.assertIn("Texnologiya va qurish", fake.calls[1]["prompt"])  # localized labels in input
        self.assertIn('"realistic"', fake.calls[1]["prompt"])  # keys unchanged

        self.assertEqual(en["language"], "en")
        self.assertEqual(uz["language"], "uz")
        self.assertEqual(uz["profile"]["headline"], UZ_AI["profile"]["headline"])
        self.assertEqual(set(uz["profile"]), set(en["profile"]))
        self.assertEqual(set(uz["next_step"]), set(en["next_step"]))
        self.assertEqual(uz_again["generated_at"], uz["generated_at"])
        self.assertEqual(en_again["profile"], en["profile"])
        self.assertEqual(
            AIInsight.objects.filter(session_id=sid, generation_type=GenerationType.PROFILE_SYNTHESIS).count(), 2
        )

    def test_fallback_is_localized(self):
        self._complete(self.student)
        with self._patch(RecordingProvider(error=ProviderError("rate_limited"))):
            uz = self._c(self.student, "uz").post(self.URL, {}, format="json").json()
            ru = self._c(self.student, "ru").post(self.URL, {}, format="json").json()
            en = self._c(self.student, "en").post(self.URL, {}, format="json").json()
        self.assertEqual({uz["source"], ru["source"], en["source"]}, {InsightSource.FALLBACK})
        self.assertIn("belgi", uz["profile"]["headline"])
        self.assertIn("сигнал", ru["profile"]["headline"])
        self.assertIn("signal", en["profile"]["headline"])
        self.assertIn("Bu belgilar", " ".join(uz["profile"]["uncertainty_notes"]))
        self.assertEqual(uz["next_step"]["signals_used"], en["next_step"]["signals_used"])
        self.assertEqual(uz["next_step"]["activity_type"], en["next_step"]["activity_type"])

    def test_banned_phrases_rejected_in_uzbek_and_russian(self):
        self._complete(self.student)
        bad_uz, bad_ru = copy.deepcopy(UZ_AI), copy.deepcopy(VALID_AI)
        bad_uz["profile"]["summary"] = "Siz albatta muhandis bo‘lasiz."
        bad_ru["profile"]["summary"] = "Тебе следует стать инженером."
        with self._patch(RecordingProvider({"uz": bad_uz, "ru": bad_ru})):
            uz = self._c(self.student, "uz").post(self.URL, {}, format="json").json()
            ru = self._c(self.student, "ru").post(self.URL, {}, format="json").json()
        self.assertEqual((uz["source"], ru["source"]), (InsightSource.FALLBACK, InsightSource.FALLBACK))

    def test_passport_reads_only_the_same_language_insight(self):
        self._complete(self.student)
        with self._patch(RecordingProvider({"en": VALID_AI})):
            self._c(self.student, "en").post(self.URL, {}, format="json")
        with mock.patch("apps.ai.services.profile_synthesis.get_provider", side_effect=AssertionError("no LLM")):
            en = self._c(self.student, "en").get("/api/v1/passport/").json()
            uz = self._c(self.student, "uz").get("/api/v1/passport/").json()
        self.assertEqual(en["headline"], VALID_AI["profile"]["headline"])
        self.assertEqual(en["insight_source"], "AI")
        self.assertEqual(uz["insight_source"], "FALLBACK")  # never the English AI text
        self.assertIn("belgi", uz["headline"])
        self.assertEqual([s["score"] for s in en["signals"]], [s["score"] for s in uz["signals"]])
        self.assertEqual(en["version"], uz["version"])
        self.assertEqual(uz["signals"][0]["key"], en["signals"][0]["key"])


class ParentInsightLanguageTests(Fixture, TestCase):
    def _url(self):
        return f"/api/v1/parent/children/{self.student.id}/insight/"

    def _patch(self, provider):
        return mock.patch("apps.ai.services.parent_insight.get_provider", return_value=provider)

    def test_parent_insight_is_language_aware_and_cached_per_language(self):
        with mock.patch("apps.ai.services.profile_synthesis.get_provider", return_value=RecordingProvider(error=ProviderError("x"))):
            self._complete(self.student)
        fake = RecordingProvider({"en": PARENT_AI, "uz": PARENT_UZ})
        with self._patch(fake):
            en = self._c(self.parent, "en").post(self._url()).json()["parent_insight"]
            uz = self._c(self.parent, "uz").post(self._url()).json()["parent_insight"]
            self._c(self.parent, "uz").post(self._url())
            self._c(self.parent, "en").post(self._url())
        self.assertEqual([c["lang"] for c in fake.calls], ["en", "uz"])
        self.assertEqual(uz["content"]["summary"], PARENT_UZ["summary"])
        self.assertEqual(set(uz["content"]), set(en["content"]))
        self.assertIn("Texnologiya va qurish", fake.calls[1]["prompt"])  # localized labels in input
        self.assertIn("Technology & Building", fake.calls[0]["prompt"])
        overview = self._c(self.parent, "uz").get(f"/api/v1/parent/children/{self.student.id}/overview/").json()
        self.assertEqual(overview["parent_insight_state"], "READY")
        self.assertEqual(overview["parent_insight"]["content"]["summary"], PARENT_UZ["summary"])
        self.assertIn("ota-onalarga", overview["privacy_note"])
        ru = self._c(self.parent, "ru").get(f"/api/v1/parent/children/{self.student.id}/overview/").json()
        self.assertEqual(ru["parent_insight_state"], "PENDING")  # RU not generated yet, EN/UZ not reused

    def test_parent_fallback_is_localized(self):
        with mock.patch("apps.ai.services.profile_synthesis.get_provider", return_value=RecordingProvider(error=ProviderError("x"))):
            self._complete(self.student)
            self._do_mission(self.student)
        with self._patch(RecordingProvider(error=ProviderError("timeout"))):
            ru = self._c(self.parent, "ru").post(self._url()).json()["parent_insight"]
            uz = self._c(self.parent, "uz").post(self._url()).json()["parent_insight"]
        self.assertEqual((ru["source"], uz["source"]), ("FALLBACK", "FALLBACK"))
        self.assertIn("Текущие данные", ru["content"]["summary"])
        self.assertIn("Придумай школьный рюкзак получше", ru["content"]["conversation_starter"])
        self.assertIn("Hozirgi ma’lumotlar", uz["content"]["summary"])
        self.assertEqual(len(ru["content"]["support_at_home"]), 3)
