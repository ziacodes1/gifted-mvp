"""Parent ↔ learner connection. Every parent read is scoped through `ParentChild`."""
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ParentChild(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="child_links")
    learner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="parent_links")
    relationship = models.CharField(max_length=30, blank=True)  # e.g. "Mother", optional
    connected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "parents_parent_child"
        unique_together = ("parent", "learner")

    def __str__(self) -> str:
        return f"{self.parent_id}->{self.learner_id}"


# No 0/O, 1/I/L: easy to read aloud and type.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def new_code() -> str:
    """GFT-XXXX-XXXX: 8 random characters (~8.5e11 combinations) — not guessable within the
    connect-endpoint throttle, unlike the previous 5-digit codes."""
    chars = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
    return f"GFT-{chars[:4]}-{chars[4:]}"


_new_code = new_code  # referenced by migration 0001


def default_expiry():
    return timezone.now() + timedelta(hours=settings.PARENT_CODE_TTL_HOURS)


class LearnerConnectionCode(models.Model):
    """The learner's current code for connecting a parent. Created only by the learner
    (explicit consent), single-use, expiring and revocable; regenerating replaces it."""

    learner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="connection_code")
    code = models.CharField(max_length=16, unique=True, default=new_code)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "parents_connection_code"

    def __str__(self) -> str:
        return self.code

    @property
    def is_valid(self) -> bool:
        return self.used_at is None and self.revoked_at is None and self.expires_at > timezone.now()
