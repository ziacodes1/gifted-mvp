"""Seed demo accounts + demo content for local demo/testing (idempotent).

Delegates domain-specific content (assessment questions, signals, ...) to
each domain's own seed command so this stays a thin entrypoint.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.accounts.models import Role, User

DEMO_PASSWORD = "demo123"
DEMO_USERS = [
    {"email": "student@gifted.demo", "full_name": "Demo Student", "role": Role.STUDENT},
    {"email": "parent@gifted.demo", "full_name": "Demo Parent", "role": Role.PARENT},
    {"email": "admin@gifted.demo", "full_name": "Demo Admin", "role": Role.ADMIN,
     "is_staff": True, "is_superuser": True},
]


class Command(BaseCommand):
    help = "Create/refresh demo accounts (student, parent, admin)."

    def handle(self, *args, **options):
        for spec in DEMO_USERS:
            email = spec["email"]
            user, created = User.objects.get_or_create(
                email=email, defaults={k: v for k, v in spec.items() if k != "email"}
            )
            # Keep fields in sync + ensure a known password for demos.
            user.full_name = spec["full_name"]
            user.role = spec["role"]
            user.is_staff = spec.get("is_staff", False)
            user.is_superuser = spec.get("is_superuser", False)
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(
                f"  {'created' if created else 'updated'}: {email} ({spec['role']})"
            )
        self.stdout.write(self.style.SUCCESS("Demo accounts ready (password: demo123)."))

        call_command("seed_demo_assessment")
        call_command("seed_demo_mission")
        call_command("seed_demo_family")
        call_command("seed_demo_engagement")
