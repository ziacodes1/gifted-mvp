"""AI Companion: a student's private conversations with their thinking partner.

Privacy boundary — these rows belong to the learner only. No parent endpoint, parent
read model or parent AI input may read them, and they are deliberately not registered
in the Django admin.

A USER message is stored only together with its ASSISTANT reply (one transaction), so
a failed model call leaves no half-answered turn. `client_id` makes a send idempotent:
retrying or re-sending the same turn returns the stored pair instead of a second reply.
"""
from django.conf import settings
from django.db import models


class MessageRole(models.TextChoices):
    USER = "USER", "User"
    ASSISTANT = "ASSISTANT", "Assistant"


class DiaryOffer(models.TextChoices):
    """On an ASSISTANT turn: whether to offer saving the student's message to My Diary.
    Offering never saves anything; only the student's explicit action does."""

    NONE = "NONE", "No offer"
    OFFERED = "OFFERED", "Offered"
    DISMISSED = "DISMISSED", "Kept only in chat"


class CompanionConversation(models.Model):
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="companion_conversations"
    )
    title = models.CharField(max_length=80, blank=True)  # first words of the first message; no AI call
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "companion_conversation"
        ordering = ["-updated_at", "-id"]
        indexes = [models.Index(fields=["learner", "-updated_at"])]

    def __str__(self) -> str:
        return f"{self.learner_id}:{self.pk}"


class CompanionMessage(models.Model):
    conversation = models.ForeignKey(CompanionConversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=MessageRole.choices)
    content = models.TextField()
    # USER turns: the client's idempotency key. ASSISTANT turns: the USER message answered.
    client_id = models.UUIDField(null=True, blank=True)
    reply_to = models.OneToOneField("self", null=True, blank=True, on_delete=models.CASCADE, related_name="reply")
    language = models.CharField(max_length=5, default="en")  # en | uz | ru (request language)
    diary_offer = models.CharField(max_length=10, choices=DiaryOffer.choices, default=DiaryOffer.NONE)
    # ASSISTANT turns: which provider/model/prompt produced the reply (no prompt text stored).
    ai_provider = models.CharField(max_length=32, blank=True)
    ai_model = models.CharField(max_length=64, blank=True)
    prompt_version = models.CharField(max_length=16, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "companion_message"
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "client_id"],
                condition=models.Q(client_id__isnull=False),
                name="uniq_companion_client_id_per_conversation",
            )
        ]

    def __str__(self) -> str:
        return f"{self.conversation_id}:{self.role}:{self.pk}"
