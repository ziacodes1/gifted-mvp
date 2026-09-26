"""Restore the demo to a clean presentation state (idempotent).

Removes only the demo student's *activity* (sessions, responses, learner signals,
evidence, mission attempts, AI insights, diary entries + photos, engagement (activity, badges, redemptions), Companion conversations, Passport). Seeded content — assessment,
questions, signals, mappings, the flagship mission — is kept and re-synced, and
the demo accounts + parent link are re-ensured via `seed_demo`.
"""
import io
from contextlib import redirect_stdout

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.ai.models import AIInsight
from apps.assessments.models import AssessmentSession
from apps.companion.models import CompanionConversation
from apps.diary.models import DiaryEntry
from apps.engagement.models import ActivityEvent, RewardRedemption, StudentBadge
from apps.evidence.models import Evidence
from apps.missions.models import MissionAttempt
from apps.passports.models import Passport
from apps.signals.models import LearnerSignal

STUDENT = "student@gifted.demo"
PARENT = "parent@gifted.demo"


class Command(BaseCommand):
    help = "Reset the demo student to NOT_STARTED and keep seeded content + demo accounts."

    def handle(self, *args, **options):
        with redirect_stdout(io.StringIO()):  # keep the summary readable
            call_command("seed_demo", stdout=io.StringIO())  # accounts, content, parent link

        with transaction.atomic():
            student = User.objects.get(email=STUDENT)
            removed = {}
            # Order matters only for readability; FKs cascade (responses, contributions).
            for label, qs in [
                ("AI insights", AIInsight.objects.filter(learner=student)),
                ("diary entries", DiaryEntry.objects.filter(learner=student)),  # photos removed by signal
                ("activity events", ActivityEvent.objects.filter(learner=student)),
                ("badges", StudentBadge.objects.filter(learner=student)),
                ("reward redemptions", RewardRedemption.objects.filter(learner=student)),
                ("companion conversations", CompanionConversation.objects.filter(learner=student)),
                ("evidence", Evidence.objects.filter(learner=student)),
                ("mission attempts", MissionAttempt.objects.filter(learner=student)),
                ("learner signals", LearnerSignal.objects.filter(learner=student)),
                ("assessment sessions", AssessmentSession.objects.filter(learner=student)),
                ("passport", Passport.objects.filter(learner=student)),
            ]:
                removed[label] = qs.count()  # top-level records; children cascade
                qs.delete()

        cleared = ", ".join(f"{n} {k}" for k, n in removed.items() if n) or "nothing to clear"
        self.stdout.write(
            self.style.SUCCESS("Gifted demo reset complete.")
            + f"\nStudent: {STUDENT} / demo123\nParent:  {PARENT} / demo123 (connected)"
            + "\nStudent state: NOT_STARTED"
            + f"\nCleared: {cleared}"
        )
