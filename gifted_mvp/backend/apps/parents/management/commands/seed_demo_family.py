"""Connect the demo parent to the demo student directly (idempotent). Does not touch the
student's progress, so a fresh demo still starts from NOT_STARTED."""
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.parents.models import ParentChild


class Command(BaseCommand):
    help = "Link parent@gifted.demo to student@gifted.demo."

    def handle(self, *args, **options):
        parent = User.objects.get(email="parent@gifted.demo")
        student = User.objects.get(email="student@gifted.demo")
        ParentChild.objects.get_or_create(parent=parent, learner=student, defaults={"relationship": "Parent"})
        # No standing code: a real learner generates a single-use, expiring code when needed.
        self.stdout.write("Demo parent connected to demo student.")
