"""Companion service layer: trusted learner context, suggested prompts, conversations.

- Context is built from the Passport read model (`build_passport`), so it reuses the same
  trusted sources as every other screen: deterministic `LearnerSignal`s, mission evidence
  dimensions and the saved interpretation. It never calls a model and sends no names,
  raw answers, scoring rules, parent data or other learners' data.
- Suggested prompts are chosen deterministically from learner state (no AI call).
- A send stores the USER turn and the ASSISTANT reply together or not at all, under a
  conversation row lock, and is idempotent by `client_id`.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from django.db import IntegrityError, transaction

from apps.ai.services.companion import generate_reply
from apps.passports.services import build_passport
from common.i18n import current_language

from .models import CompanionConversation, CompanionMessage, MessageRole

TITLE_CHARS = 60
MAX_MESSAGE_CHARS = 2000


# --- Context ------------------------------------------------------------------


def _labels(rows, category: str, limit: int) -> list[str]:
    return [r["label"] for r in rows if r["category"] == category and r["evidence_count"] > 0][:limit]


def build_context(passport: dict) -> dict:
    """Compact, source-labelled learner context for the model (labels in the request language)."""
    status = passport["status"]
    other = passport["other_signals"]
    mission_titles = [e["title"] for e in passport["recent_evidence"] if e["source_type"] == "MISSION"]
    context: dict = {
        "journey": {
            "passport_status": status,
            "stages_reached": [s["label"] for s in passport["journey"] if s["done"]],
            "assessment_completed": status != "EMPTY",
            "missions_completed": len(mission_titles),
        },
        "unknown": ["age", "grade", "personal goals"],
    }
    if status == "EMPTY":
        return context

    context["assessment"] = {
        "source": "assessment",
        "interests": [
            {
                "label": s["label"],
                "confidence": s["confidence"],
                "picked": s["evidence_count"],
                "chances": s["opportunity_count"],
            }
            for s in passport["signals"][:4]
        ],
        "early_reasoning": _labels(other, "APTITUDE", 2),
        "work_style": _labels(other, "WORK_STYLE", 3),
        "values": _labels(other, "VALUE", 3),
        "exposure_tried": _labels(other, "EXPOSURE", 5),
        "exposure_not_tried_yet": [o["label"] for o in other if o["category"] == "EXPOSURE" and o["evidence_count"] == 0][:5],
    }
    if mission_titles:
        context["missions"] = {
            "source": "mission",
            "meaning": "dimensions practised in short scenario challenges; not a measure of skill",
            "completed": mission_titles,
            "dimensions_explored": [{"label": d["label"], "kinds": d["kinds"]} for d in passport["explored_dimensions"][:6]],
        }
    context["interpretation"] = {
        "source": "ai_interpretation" if passport["insight_source"] == "AI" else "signal_based_summary",
        "written_from": "assessment only",
        "headline": passport["headline"],
        "emerging_strengths": [s["title"] for s in passport["emerging_strengths"][:3]],
    }
    mission = passport["recommended_mission"]
    context["next_exploration"] = {
        "suggested_step": passport["next_step"]["title"] if passport["next_step"] else None,
        "mission": {"title": mission["title"], "status": (mission["my_attempt"] or {}).get("status", "NOT_STARTED")}
        if mission
        else None,
    }
    return context


def suggested_prompts(passport: dict) -> list[dict]:
    """3-4 prompt keys (+ localized params) picked from learner state. The frontend owns the text."""
    status = passport["status"]
    if status == "EMPTY":
        return [
            {"key": "getting_started", "params": {}},
            {"key": "unsure_interests", "params": {}},
            {"key": "difficult_topic", "params": {}},
            {"key": "weekly_plan", "params": {}},
        ]
    prompts = []
    missions = [e["title"] for e in passport["recent_evidence"] if e["source_type"] == "MISSION"]
    if missions:
        prompts.append({"key": "reflect_mission", "params": {"mission": missions[0]}})
    lead = passport["signals"][0]["label"] if passport["signals"] else None
    prompts.append({"key": "interest_meaning", "params": {"interest": lead}} if lead else {"key": "current_interests", "params": {}})
    prompts.append({"key": "explore_next", "params": {}})
    prompts.append({"key": "skills_to_build", "params": {}})
    prompts.append({"key": "weekly_plan", "params": {}})
    return prompts[:4]


def about_card(passport: dict) -> dict:
    """What the Companion knows, shown to the learner (transparency; nothing hidden is used)."""
    status = passport["status"]
    stage = next((s["label"] for s in reversed(passport["journey"]) if s["done"]), None)
    other = passport.get("other_signals", [])
    return {
        "first_name": passport["learner"]["first_name"],
        "passport_status": status,
        "journey_stage": stage,
        "interests": [s["label"] for s in passport["signals"][:2]],
        "values": _labels(other, "VALUE", 2),
        "missions_completed": passport["evidence_summary"]["missions"],
        "next_exploration": passport["next_step"]["title"] if passport["next_step"] else None,
    }


def companion_overview(learner, language: str | None = None) -> dict:
    passport = build_passport(learner, language or current_language())
    return {"about": about_card(passport), "suggested_prompts": suggested_prompts(passport)}


# --- Conversations -------------------------------------------------------------


def start_conversation(learner) -> tuple[CompanionConversation, bool]:
    """New chat. Reuses the newest conversation if it is still empty, so repeated
    "New chat" clicks don't pile up blank conversations."""
    latest = CompanionConversation.objects.filter(learner=learner).order_by("-updated_at", "-id").first()
    if latest is not None and not latest.messages.exists():
        return latest, False
    return CompanionConversation.objects.create(learner=learner), True


class CompanionUnavailable(Exception):
    """No trustworthy reply right now (provider down, rate limited or reply rejected)."""


@dataclass
class Turn:
    user: CompanionMessage
    assistant: CompanionMessage
    created: bool


def _existing_turn(conversation, client_id) -> Turn | None:
    user = (
        CompanionMessage.objects.filter(conversation=conversation, client_id=client_id, role=MessageRole.USER)
        .select_related("reply")
        .first()
    )
    if user is None:
        return None
    return Turn(user=user, assistant=user.reply, created=False)


def send_message(conversation: CompanionConversation, content: str, client_id: uuid.UUID, language: str) -> Turn:
    """Store the learner's message and the Companion's reply, or nothing.

    Runs under a lock on the conversation row: concurrent sends to one conversation are
    serialized, and a retry with the same `client_id` returns the stored turn without a
    second model call. Raises CompanionUnavailable when no reply could be produced."""
    content = content.strip()
    with transaction.atomic():
        CompanionConversation.objects.select_for_update().only("id").get(pk=conversation.pk)
        existing = _existing_turn(conversation, client_id)
        if existing is not None:
            return existing

        history = list(
            conversation.messages.order_by("-created_at", "-id").values_list("role", "content")[:20]
        )[::-1]
        context = build_context(build_passport(conversation.learner, language))
        generated = generate_reply(context=context, history=history, message=content, language=language)
        if generated is None:
            raise CompanionUnavailable

        reply, _provider, _model = generated
        try:
            with transaction.atomic():
                user = CompanionMessage.objects.create(
                    conversation=conversation, role=MessageRole.USER, content=content, client_id=client_id, language=language
                )
        except IntegrityError:  # same client_id raced in outside the lock (should not happen)
            return _existing_turn(conversation, client_id)
        assistant = CompanionMessage.objects.create(
            conversation=conversation, role=MessageRole.ASSISTANT, content=reply, reply_to=user, language=language
        )
        if not conversation.title:
            conversation.title = _title(content)
        conversation.save(update_fields=["title", "updated_at"])
        return Turn(user=user, assistant=assistant, created=True)


def _title(content: str) -> str:
    text = " ".join(content.split())
    return text if len(text) <= TITLE_CHARS else text[: TITLE_CHARS - 1].rsplit(" ", 1)[0] + "…"
