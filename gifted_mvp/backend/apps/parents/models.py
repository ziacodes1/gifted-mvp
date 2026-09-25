"""Parent ↔ learner connection. Every parent read is scoped through `ParentChild`."""
import secrets

from django.conf import settings
from django.db import models


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


def _new_code() -> str:
    return f"GFT-{secrets.randbelow(90000) + 10000}"


class LearnerConnectionCode(models.Model):
    """Short code a learner shares so a parent can connect (e.g. GFT-48291)."""

    learner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="connection_code")
    code = models.CharField(max_length=12, unique=True, default=_new_code)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "parents_connection_code"

    def __str__(self) -> str:
        return self.code
