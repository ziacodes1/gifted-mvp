import io
import json
from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.engagement.services import local_day
from apps.evidence.models import Evidence, EvidenceSource
from apps.parents.models import ParentChild
from apps.signals.models import LearnerSignal, Signal

from .models import (
    CommunityCircle,
    CommunityMembership,
    CommunityPost,
    CommunityReport,
    LearnerOpportunity,
    LearnerResource,
    LearningPath,
    ModerationStatus,
    Opportunity,
    ProgressStatus,
    Resource,
)
from .services import for_you
from .services.matching import learner_profile, match_item, match_opportunity

User = get_user_model()
POST_TEXT = "My unique community post about bean roots"


def give_signals(learner, **scores):
    for key, score in scores.items():
        LearnerSignal.objects.update_or_create(
            learner=learner, signal=Signal.objects.get(key=key), defaults={"score": score}
        )


class EcosystemBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_assessment", verbosity=0)
        call_command("seed_demo_engagement", verbosity=0, stdout=io.StringIO())
        call_command("seed_demo_ecosystem", verbosity=0, stdout=io.StringIO())
        cls.student = User.objects.create_user("kid@test.dev", "pw12345!", full_name="Ada Lovelace")
        cls.other = User.objects.create_user("friend@test.dev", "pw12345!", full_name="Grace Hopper")
        cls.parent = User.objects.create_user("mum@test.dev", "pw12345!", role="PARENT")
        ParentChild.objects.create(parent=cls.parent, learner=cls.student)

    def _c(self, user=None, lang=None):
        c = APIClient()
        c.force_authenticate(user or self.student)
        if lang:
            c.credentials(HTTP_ACCEPT_LANGUAGE=lang)
        return c


class MatchingTests(EcosystemBase):
    def test_no_signals_is_exploration_not_a_match(self):
        r = Resource.objects.get(slug="how-scientists-ask-questions")
        self.assertEqual(match_item(learner_profile(self.student), r), {"level": "EXPLORE", "reasons": []})

    def test_levels_and_traceable_reasons(self):
        give_signals(self.student, investigative=80, value_discovery=70, exp_science=10, artistic=20)
        profile = learner_profile(self.student)
        science = match_item(profile, Resource.objects.get(slug="how-scientists-ask-questions"))
        self.assertEqual(science["level"], "STRONG_FIT")
        codes = [r["code"] for r in science["reasons"]]
        self.assertEqual(codes[:2], ["interest", "value"])
        self.assertIn("exposure_gap", codes)  # exp_science is low → first-hand experience
        self.assertTrue(all(r["label"] for r in science["reasons"]))

        art = match_item(profile, Resource.objects.get(slug="sketchbook-habit"))
        self.assertEqual(art["level"], "NEW_AREA")
        self.assertEqual(art["reasons"][0]["code"], "new_area")

    def test_emerging_interest_is_worth_exploring(self):
        give_signals(self.student, social=50, exp_helping=90)
        m = match_item(learner_profile(self.student), Resource.objects.get(slug="learn-a-language-through-projects"))
        self.assertEqual((m["level"], m["reasons"][0]["code"]), ("WORTH_EXPLORING", "emerging"))

    def test_mission_evidence_upgrades_a_single_clear_match(self):
        from apps.evidence.services import Contribution, record_evidence

        give_signals(self.student, artistic=75)
        item = Resource.objects.get(slug="sketchbook-habit")
        self.assertEqual(match_item(learner_profile(self.student), item)["level"], "WORTH_EXPLORING")
        record_evidence(learner=self.student, source_type=EvidenceSource.MISSION, source_id=999, title="m",
                        contributions=[Contribution("artistic", "INTEREST", 1)])
        m = match_item(learner_profile(self.student), item)
        self.assertEqual(m["level"], "STRONG_FIT")
        self.assertIn("evidence", [r["code"] for r in m["reasons"]])

    def test_match_opportunity_shape_has_no_scores(self):
        give_signals(self.student, investigative=80, independent_work=65)
        o = Opportunity.objects.get(slug="young-innovators-research-fellowship")
        result = match_opportunity(self.student, o)
        self.assertEqual(set(result), {"match_level", "reasons", "eligibility"})
        self.assertEqual(result["match_level"], "STRONG_FIT")
        self.assertEqual(result["eligibility"]["age"], {"min": 15, "max": 18, "status": "CHECK"})
        self.assertEqual(result["eligibility"]["location"]["status"], "ANYWHERE")
        dumped = json.dumps(result)
        self.assertNotIn("%", dumped)
        self.assertNotIn("score", dumped)

    def test_deterministic(self):
        give_signals(self.student, enterprising=70, social=60)
        a = self._c().get("/api/v1/opportunities/").json()
        b = self._c().get("/api/v1/opportunities/").json()
        self.assertEqual(a, b)


class ResourceApiTests(EcosystemBase):
    def test_roles(self):
        self.assertEqual(APIClient().get("/api/v1/resources/").status_code, 401)
        for url in ("/api/v1/resources/", "/api/v1/resources/plan-your-week/", "/api/v1/opportunities/",
                    "/api/v1/community/", "/api/v1/ecosystem/for-you/", "/api/v1/learning-paths/create-a-more-sustainable-world/"):
            self.assertEqual(self._c(self.parent).get(url).status_code, 403, url)

    def test_list_filters_and_featured_path(self):
        data = self._c().get("/api/v1/resources/").json()
        self.assertEqual(len(data["items"]), 12)
        path = data["featured_path"]
        self.assertEqual((path["slug"], path["resource_count"]), ("create-a-more-sustainable-world", 5))
        self.assertEqual(path["duration_minutes"], 8 + 12 + 25 + 30 + 120)
        self.assertTrue(data["items"][0]["organization"]["is_demo"])

        videos = self._c().get("/api/v1/resources/?type=VIDEO").json()["items"]
        self.assertTrue(videos and all(i["type"] == "VIDEO" for i in videos))
        env = self._c().get("/api/v1/resources/?category=ENVIRONMENT").json()["items"]
        self.assertEqual({i["category"] for i in env}, {"ENVIRONMENT"})
        found = self._c().get("/api/v1/resources/?q=robot").json()["items"]
        self.assertEqual([i["slug"] for i in found], ["intro-to-robotics"])
        shortest = self._c().get("/api/v1/resources/?sort=shortest").json()["items"]
        self.assertEqual(shortest[0]["slug"], "plan-your-week")

    def test_localized_and_search_in_language(self):
        uz = self._c(lang="uz").get("/api/v1/resources/plan-your-week/").json()
        self.assertEqual(uz["title"], "Haftangizni stresssiz rejalashtiring")
        self.assertIn("points", uz["content"])
        ru = self._c(lang="ru").get("/api/v1/resources/?q=робот").json()["items"]
        self.assertEqual([i["slug"] for i in ru], ["intro-to-robotics"])

    def test_bookmark_open_progress(self):
        c = self._c()
        d = c.post("/api/v1/resources/plan-your-week/action/", {"action": "save"}, format="json").json()
        self.assertTrue(d["saved"])
        saved = c.get("/api/v1/resources/?saved=1").json()["items"]
        self.assertEqual([i["slug"] for i in saved], ["plan-your-week"])
        c.post("/api/v1/resources/plan-your-week/action/", {"action": "unsave"}, format="json")
        self.assertEqual(c.get("/api/v1/resources/?saved=1").json()["items"], [])

        course = c.post("/api/v1/resources/build-your-first-ai-model/action/", {"action": "open"}, format="json").json()
        self.assertEqual(course["status"], "IN_PROGRESS")
        article = c.post("/api/v1/resources/plan-your-week/action/", {"action": "open"}, format="json").json()
        self.assertEqual(article["status"], "NOT_STARTED")  # articles don't have in-progress
        r = c.post("/api/v1/resources/plan-your-week/action/", {"action": "start"}, format="json")
        self.assertEqual(r.status_code, 400)
        done = c.post("/api/v1/resources/plan-your-week/action/", {"action": "complete"}, format="json").json()
        self.assertEqual(done["status"], "COMPLETED")
        self.assertEqual(c.post("/api/v1/resources/plan-your-week/action/", {"action": "nope"}, format="json").status_code, 400)
        self.assertEqual(c.get("/api/v1/resources/missing/").status_code, 404)

    def test_evidence_only_for_configured_resources(self):
        c = self._c()
        c.post("/api/v1/resources/plan-your-week/action/", {"action": "complete"}, format="json")
        self.assertFalse(Evidence.objects.filter(learner=self.student).exists())

        d = c.post("/api/v1/resources/sketchbook-habit/action/", {"action": "complete"}, format="json").json()
        self.assertTrue(d["produces_evidence"] and d["evidence_recorded"])
        ev = Evidence.objects.get(learner=self.student, source_type=EvidenceSource.RESOURCE)
        self.assertEqual([c.signal.key for c in ev.contributions.all()], ["exp_design"])
        self.assertEqual(ev.contributions.get().kind, "EXPOSURE")
        # complete → reset → complete never duplicates evidence
        c.post("/api/v1/resources/sketchbook-habit/action/", {"action": "reset"}, format="json")
        c.post("/api/v1/resources/sketchbook-habit/action/", {"action": "complete"}, format="json")
        self.assertEqual(Evidence.objects.filter(learner=self.student).count(), 1)

    def test_learning_path_progress(self):
        c = self._c()
        c.post("/api/v1/resources/ocean-conservation-young-people/action/", {"action": "complete"}, format="json")
        p = c.get("/api/v1/learning-paths/create-a-more-sustainable-world/").json()
        self.assertEqual([i["slug"] for i in p["items"]][0], "ocean-conservation-young-people")
        self.assertEqual((p["completed_count"], p["next_resource"]), (1, "design-thinking-for-real-change"))

    def test_inactive_content_is_hidden(self):
        Resource.objects.filter(slug="plan-your-week").update(active=False)
        self.assertEqual(self._c().get("/api/v1/resources/plan-your-week/").status_code, 404)
        slugs = [i["slug"] for i in self._c().get("/api/v1/resources/").json()["items"]]
        self.assertNotIn("plan-your-week", slugs)

    def test_signals_personalize_order(self):
        give_signals(self.student, realistic=85, logical_reasoning=70)
        first = self._c().get("/api/v1/resources/").json()["items"][0]
        self.assertEqual(first["slug"], "build-your-first-ai-model")
        self.assertEqual(first["match"]["level"], "STRONG_FIT")


class OpportunityApiTests(EcosystemBase):
    def test_list_hides_closed_by_default_and_filters(self):
        c = self._c()
        items = c.get("/api/v1/opportunities/").json()["items"]
        self.assertEqual(len(items), 9)
        self.assertNotIn("junior-lab-assistant-internship", [i["slug"] for i in items])
        every = c.get("/api/v1/opportunities/?deadline=all").json()["items"]
        self.assertEqual(every[-1]["eligibility"]["deadline"]["status"], "CLOSED")  # closed last

        online = c.get("/api/v1/opportunities/?mode=ONLINE").json()["items"]
        self.assertTrue(online and all(i["mode"] == "ONLINE" for i in online))
        in_person = c.get("/api/v1/opportunities/?mode=IN_PERSON").json()["items"]
        self.assertTrue(in_person and all(i["mode"] in ("IN_PERSON", "HYBRID") for i in in_person))
        stem = c.get("/api/v1/opportunities/?category=STEM").json()["items"]
        self.assertEqual({i["category"] for i in stem}, {"STEM"})
        twelve = c.get("/api/v1/opportunities/?age=12").json()["items"]
        self.assertTrue(all((i["age_min"] or 0) <= 12 <= (i["age_max"] or 99) for i in twelve))
        soon = c.get("/api/v1/opportunities/?deadline=closing_soon").json()["items"]
        self.assertEqual([i["slug"] for i in soon], ["ai-builders-weekend-hackathon"])
        hack = c.get("/api/v1/opportunities/?type=HACKATHON").json()["items"]
        self.assertEqual(len(hack), 1)

    def test_featured_is_personal_when_signals_exist(self):
        base = self._c().get("/api/v1/opportunities/").json()
        self.assertEqual(base["featured"]["slug"], "young-innovators-research-fellowship")  # admin-featured
        give_signals(self.student, enterprising=80, value_practical=70)
        data = self._c().get("/api/v1/opportunities/").json()
        self.assertEqual(data["featured"]["match"]["level"], "STRONG_FIT")
        self.assertEqual(data["featured"]["slug"], "young-entrepreneurs-program")

    def test_detail_and_interaction_states(self):
        c = self._c()
        url = "/api/v1/opportunities/young-innovators-research-fellowship/"
        d = c.get(url).json()
        self.assertEqual(d["state"], "NONE")
        self.assertTrue(d["application_url"].startswith("https://example.org/"))
        self.assertTrue(d["faqs"] and d["requirements"] and d["skills"])
        self.assertEqual(c.post(url + "action/", {"action": "view"}, format="json").json()["state"], "VIEWED")
        self.assertEqual(c.post(url + "action/", {"action": "save"}, format="json").json()["state"], "SAVED")
        opened = c.post(url + "action/", {"action": "open_link"}, format="json")
        self.assertEqual(opened.json()["state"], "APPLICATION_LINK_OPENED")
        self.assertNotIn("submitted", opened.content.decode().lower())
        self.assertNotIn("applied", opened.content.decode().lower())
        row = LearnerOpportunity.objects.get(learner=self.student)
        self.assertTrue(row.saved and row.link_opened_at and row.viewed_at)
        self.assertEqual(c.post(url + "action/", {"action": "apply"}, format="json").status_code, 400)
        saved = c.get("/api/v1/opportunities/?saved=1").json()["items"]
        self.assertEqual([i["slug"] for i in saved], ["young-innovators-research-fellowship"])

    def test_eligibility_states(self):
        c = self._c()
        region = c.get("/api/v1/opportunities/stem-excellence-scholarship/").json()["eligibility"]["location"]
        self.assertEqual((region["status"], region["country"]), ("ONLINE_REGION", "Uzbekistan"))
        site = c.get("/api/v1/opportunities/ai-builders-weekend-hackathon/").json()["eligibility"]
        self.assertEqual((site["location"]["status"], site["deadline"]["status"]), ("ON_SITE", "CLOSING_SOON"))
        rolling = c.get("/api/v1/opportunities/green-futures-volunteer-days/").json()["eligibility"]["deadline"]
        self.assertEqual(rolling["status"], "ROLLING")
        Opportunity.objects.filter(slug="green-futures-volunteer-days").update(application_open_at=local_day() + timedelta(days=5))
        later = c.get("/api/v1/opportunities/green-futures-volunteer-days/").json()["eligibility"]
        self.assertEqual((later["deadline"]["status"], later["open_now"]), ("NOT_YET_OPEN", False))

    def test_localized(self):
        d = self._c(lang="ru").get("/api/v1/opportunities/ai-builders-weekend-hackathon/").json()
        self.assertEqual((d["city"], d["country"]), ("Ташкент", "Узбекистан"))
        self.assertTrue(d["title"].startswith("Хакатон"))


class CommunityTests(EcosystemBase):
    def test_overview_counts_are_real(self):
        data = self._c().get("/api/v1/community/").json()
        science = next(c for c in data["circles"] if c["slug"] == "science-circle")
        self.assertEqual(science["member_count"], CommunityMembership.objects.filter(circle__slug="science-circle").count())
        self.assertEqual(data["my_circles"], [])
        self.assertTrue(len(data["events"]) >= 3)
        self.assertEqual(len(data["feed"]), 8)
        dumped = json.dumps(data)
        self.assertNotIn("@", dumped)  # no emails anywhere
        self.assertNotIn("likes", dumped)
        self.assertEqual(data["feed"][0]["author_name"], "Aziza Y.")

    def test_suggested_circles_follow_signals(self):
        give_signals(self.student, investigative=85, artistic=65)
        s = self._c().get("/api/v1/community/").json()["suggested"]
        self.assertEqual([c["slug"] for c in s[:2]], ["science-circle", "design-lab"])
        self.assertEqual(s[0]["reason"]["code"], "interest")
        give_signals(self.student, investigative=10, artistic=10, enterprising=80)
        s = self._c().get("/api/v1/community/").json()["suggested"]
        self.assertEqual(s[0]["slug"], "young-entrepreneurs")

    def test_join_leave_and_post_moderation(self):
        c = self._c()
        r = c.post("/api/v1/community/posts/", {"circle": "science-circle", "body": POST_TEXT}, format="json")
        self.assertEqual(r.status_code, 403)  # members only
        before = CommunityMembership.objects.filter(circle__slug="science-circle").count()
        joined = c.post("/api/v1/community/circles/science-circle/").json()
        self.assertEqual([m["slug"] for m in joined["my_circles"]], ["science-circle"])
        self.assertEqual(next(x for x in joined["circles"] if x["slug"] == "science-circle")["member_count"], before + 1)

        created = c.post("/api/v1/community/posts/", {"circle": "science-circle", "body": POST_TEXT, "post_type": "SHARE"}, format="json")
        self.assertEqual(created.status_code, 201)
        mine = created.json()["feed"][0]
        self.assertEqual((mine["status"], mine["mine"], mine["body"]), ("PENDING", True, POST_TEXT))
        # Others don't see it until approved.
        self.assertNotIn(POST_TEXT, self._c(self.other).get("/api/v1/community/").content.decode())
        CommunityPost.objects.filter(body=POST_TEXT).update(moderation_status=ModerationStatus.APPROVED)
        seen = self._c(self.other, lang="uz").get("/api/v1/community/").json()["feed"]
        post = next(p for p in seen if p["body"] == POST_TEXT)  # never translated
        self.assertEqual(post["author_name"], "Ada L.")

        self.assertEqual(c.post("/api/v1/community/posts/", {"circle": "science-circle", "body": "a"}, format="json").status_code, 400)
        left = c.delete("/api/v1/community/circles/science-circle/").json()
        self.assertEqual(left["my_circles"], [])

    def test_reports_send_post_back_to_review(self):
        post = CommunityPost.objects.filter(moderation_status=ModerationStatus.APPROVED).first()
        reporters = [User.objects.create_user(f"r{i}@test.dev", "pw12345!") for i in range(3)]
        self.assertEqual(self._c(post.author).post(f"/api/v1/community/posts/{post.id}/report/", {}, format="json").status_code, 400)
        r = self._c(reporters[0]).post(f"/api/v1/community/posts/{post.id}/report/", {"reason": "UNKIND"}, format="json")
        self.assertEqual(r.status_code, 204)
        # Reporter no longer sees it; others still do; reporting twice is idempotent.
        self.assertNotIn(post.body, self._c(reporters[0]).get("/api/v1/community/").content.decode())
        self.assertIn(post.body, self._c(self.other).get("/api/v1/community/").content.decode())
        self._c(reporters[0]).post(f"/api/v1/community/posts/{post.id}/report/", {}, format="json")
        self.assertEqual(CommunityReport.objects.filter(post=post).count(), 1)
        for u in reporters[1:]:
            self._c(u).post(f"/api/v1/community/posts/{post.id}/report/", {"reason": "SPAM"}, format="json")
        post.refresh_from_db()
        self.assertEqual(post.moderation_status, ModerationStatus.PENDING)
        self.assertNotIn(post.body, self._c(self.other).get("/api/v1/community/").content.decode())
        self.assertEqual(self._c(self.other).post(f"/api/v1/community/posts/{post.id}/report/", {}, format="json").status_code, 404)

    def test_inactive_circle_hidden(self):
        CommunityCircle.objects.filter(slug="science-circle").update(active=False)
        data = self._c().get("/api/v1/community/").json()
        self.assertNotIn("science-circle", [c["slug"] for c in data["circles"]])
        self.assertTrue(all(p["circle"]["slug"] != "science-circle" for p in data["feed"]))
        self.assertEqual(self._c().post("/api/v1/community/circles/science-circle/").status_code, 404)


class IntegrationAndPrivacyTests(EcosystemBase):
    def test_for_you(self):
        data = self._c().get("/api/v1/ecosystem/for-you/").json()
        self.assertFalse(data["has_signals"])
        self.assertTrue(data["resource"] and data["opportunity"] and data["circle"])
        give_signals(self.student, realistic=85, logical_reasoning=70)
        picks = for_you(self.student)
        self.assertEqual(picks["resource"]["slug"], "build-your-first-ai-model")
        self.assertEqual(picks["opportunity"]["slug"], "ai-builders-weekend-hackathon")
        self.assertEqual(picks["circle"]["slug"], "ai-builders")
        # Finished / opened / joined items are not suggested again.
        self._c().post("/api/v1/resources/build-your-first-ai-model/action/", {"action": "complete"}, format="json")
        self._c().post("/api/v1/opportunities/ai-builders-weekend-hackathon/action/", {"action": "open_link"}, format="json")
        self._c().post("/api/v1/community/circles/ai-builders/")
        again = for_you(self.student)
        self.assertNotEqual(again["resource"]["slug"], "build-your-first-ai-model")
        self.assertNotEqual(again["opportunity"]["slug"], "ai-builders-weekend-hackathon")
        self.assertNotEqual(again["circle"]["slug"], "ai-builders")

    def test_parent_never_sees_community_or_ecosystem_activity(self):
        c = self._c()
        c.post("/api/v1/community/circles/science-circle/")
        c.post("/api/v1/community/posts/", {"circle": "science-circle", "body": POST_TEXT}, format="json")
        c.post("/api/v1/opportunities/young-innovators-research-fellowship/action/", {"action": "save"}, format="json")
        overview = self._c(self.parent).get(f"/api/v1/parent/children/{self.student.id}/overview/")
        self.assertEqual(overview.status_code, 200)
        body = overview.content.decode()
        for private in (POST_TEXT, "Science Circle", "Young Innovators"):
            self.assertNotIn(private, body)

    def test_admin_registration_and_changelists(self):
        registered = set(admin.site._registry)
        for model in (LearnerResource, LearnerOpportunity, CommunityMembership):
            self.assertNotIn(model, registered, model.__name__)
        call_command("seed_demo", verbosity=0, stdout=io.StringIO())
        self.client.force_login(User.objects.get(email="admin@gifted.demo"))
        for url in ("organization", "resource", "learningpath", "opportunity", "communitycircle", "communityevent",
                    "communitypost", "communityreport"):
            self.assertEqual(self.client.get(f"/admin/ecosystem/{url}/").status_code, 200, url)
        r = Resource.objects.get(slug="plan-your-week")
        self.assertEqual(self.client.get(f"/admin/ecosystem/resource/{r.id}/change/").status_code, 200)
        path = LearningPath.objects.get()
        self.assertEqual(self.client.get(f"/admin/ecosystem/learningpath/{path.id}/change/").status_code, 200)

    def test_admin_moderation_actions(self):
        call_command("seed_demo", verbosity=0, stdout=io.StringIO())
        self.client.force_login(User.objects.get(email="admin@gifted.demo"))
        post = CommunityPost.objects.create(circle=CommunityCircle.objects.first(), author=self.student, body=POST_TEXT)
        self.client.post("/admin/ecosystem/communitypost/", {"action": "approve", "_selected_action": [post.id]})
        post.refresh_from_db()
        self.assertEqual(post.moderation_status, ModerationStatus.APPROVED)
        self.client.post("/admin/ecosystem/communitypost/", {"action": "reject", "_selected_action": [post.id]})
        post.refresh_from_db()
        self.assertEqual(post.moderation_status, ModerationStatus.REJECTED)

    def test_reset_demo_clears_interactions_and_keeps_catalog(self):
        call_command("seed_demo", verbosity=0, stdout=io.StringIO())
        demo = User.objects.get(email="student@gifted.demo")
        c = self._c(demo)
        c.post("/api/v1/resources/plan-your-week/action/", {"action": "save"}, format="json")
        c.post("/api/v1/opportunities/young-innovators-research-fellowship/action/", {"action": "open_link"}, format="json")
        c.post("/api/v1/community/circles/science-circle/")
        c.post("/api/v1/community/posts/", {"circle": "science-circle", "body": POST_TEXT}, format="json")
        counts = (Resource.objects.count(), Opportunity.objects.count(), CommunityCircle.objects.count())
        call_command("reset_demo", stdout=io.StringIO())
        call_command("reset_demo", stdout=io.StringIO())  # idempotent
        self.assertFalse(LearnerResource.objects.filter(learner=demo).exists())
        self.assertFalse(LearnerOpportunity.objects.filter(learner=demo).exists())
        self.assertFalse(CommunityMembership.objects.filter(learner=demo).exists())
        self.assertFalse(CommunityPost.objects.filter(author=demo).exists())
        self.assertEqual(counts, (Resource.objects.count(), Opportunity.objects.count(), CommunityCircle.objects.count()))
        self.assertEqual(CommunityPost.objects.filter(moderation_status=ModerationStatus.APPROVED).count(), 8)
