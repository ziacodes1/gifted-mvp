"""Parent read model. Reuses the Passport aggregate (no duplicated business logic)
and projects it into a parent-safe shape.

Privacy boundary — parents get growth signals, not private responses:
- no raw assessment answers, no mission responses or reflection text,
- no evidence metadata, scoring rules or AI provider/model details.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from django.http import Http404

from apps.ai.services.parent_insight import get_or_create_parent_insight, get_saved_parent_insight
from apps.assessments.models import AssessmentSession, SessionStatus
from apps.passports.services import build_passport
from apps.signals.models import Signal, SignalCategory
from common.i18n import current_language, label, tr

from .models import LearnerConnectionCode, ParentChild, default_expiry, new_code


def connected_learners(parent):
    return [link.learner for link in ParentChild.objects.filter(parent=parent).select_related("learner")]


def get_connected_learner(parent, learner_id: int):
    """The only way parent views resolve a learner. Unconnected → 404 (no existence leak)."""
    link = ParentChild.objects.filter(parent=parent, learner_id=learner_id).select_related("learner").first()
    if link is None:
        raise Http404
    return link.learner


@transaction.atomic
def connect_with_code(parent, code: str):
    """A parent redeems the learner's code. Unknown, expired, revoked or already-used codes all
    give the same 404 (no hint which), and the endpoint is throttled. Single-use: the code is
    consumed by the first successful connection."""
    entry = (
        LearnerConnectionCode.objects.select_for_update()
        .filter(code=code.strip().upper())
        .select_related("learner")
        .first()
    )
    if entry is None or not entry.is_valid or entry.learner.role != "STUDENT" or not entry.learner.is_active:
        raise Http404
    ParentChild.objects.get_or_create(parent=parent, learner=entry.learner)
    entry.used_at = timezone.now()
    entry.save(update_fields=["used_at"])
    return entry.learner


# --- Learner side: the learner controls who is connected ------------------------------------


@transaction.atomic
def issue_code(learner) -> LearnerConnectionCode:
    """New single-use code (replaces any previous one)."""
    entry, _ = LearnerConnectionCode.objects.select_for_update().get_or_create(learner=learner)
    entry.code = new_code()
    entry.created_at = timezone.now()
    entry.expires_at = default_expiry()
    entry.used_at = entry.revoked_at = None
    entry.save()
    return entry


def revoke_code(learner) -> None:
    LearnerConnectionCode.objects.filter(learner=learner, revoked_at__isnull=True).update(revoked_at=timezone.now())


def parent_access(learner) -> dict:
    entry = LearnerConnectionCode.objects.filter(learner=learner).first()
    return {
        "code": {"code": entry.code, "expires_at": entry.expires_at} if entry and entry.is_valid else None,
        "parents": [
            {"id": link.parent_id, "display_name": link.parent.full_name.strip() or "Parent", "connected_at": link.connected_at}
            for link in ParentChild.objects.filter(learner=learner).select_related("parent").order_by("connected_at")
        ],
    }


def disconnect_parent(learner, parent_id: int) -> bool:
    deleted, _ = ParentChild.objects.filter(learner=learner, parent_id=parent_id).delete()
    return bool(deleted)


def _latest_session(learner):
    return (
        AssessmentSession.objects.filter(learner=learner, status=SessionStatus.COMPLETED)
        .order_by("-completed_at")
        .first()
    )


def parent_insight_input(passport: dict, language: str = "en") -> dict:
    """Compact, trusted input for the Parent Insight model — no names, answers or reflections.
    Labels come from `passport` (built in `language`); keys and numbers are language-independent."""
    evidence = passport["evidence_summary"]
    have = {s["key"] for s in passport["signals"]}
    limited = [
        tr(s, "label", language)
        for s in Signal.objects.filter(is_active=True, category=SignalCategory.INTEREST)
        .exclude(key__in=have)
        .order_by("label")
    ]
    return {
        "passport_status": passport["status"],
        "journey_stages_reached": [s["label"] for s in passport["journey"] if s["done"]],
        # Every item carries its explicit evidence source; the model may not merge them.
        "signals": [
            {k: s[k] for k in ("key", "label", "score", "confidence", "evidence_count")}
            | {"chances": s["opportunity_count"], "evidence_source": "assessment"}
            for s in passport["signals"][:3]
        ],
        "evidence": {
            "assessment_responses": evidence["assessment"],
            "missions": evidence["missions"],
            "opportunities": evidence["opportunities"],
            "real_world": evidence["experiences"],
        },
        "missions_completed": [e["title"] for e in passport["recent_evidence"] if e["source_type"] == "MISSION"],
        "explored_through_missions": [
            {"label": d["label"], "kinds": d["kinds"], "evidence_source": "mission"} for d in passport["explored_dimensions"]
        ],
        "limited_evidence_areas": limited,
        "other_signals": [
            {
                "label": o["label"],
                "category": o["category"],
                "picked": o["evidence_count"],
                "chances": o["opportunity_count"],
                "evidence_source": "assessment",
            }
            for o in passport["other_signals"]
            if o["evidence_count"] > 0 and o["category"] != "EXPOSURE"
        ],
        "exposure_tried": [o["label"] for o in passport["other_signals"] if o["category"] == "EXPOSURE" and o["evidence_count"] > 0],
        "exposure_not_tried": [o["label"] for o in passport["other_signals"] if o["category"] == "EXPOSURE" and o["evidence_count"] == 0],
        "next_exploration": passport["next_step"]["title"] if passport["next_step"] else None,
    }


def _insight_payload(insight) -> dict | None:
    if insight is None:
        return None
    return {"source": insight.source, "content": insight.result, "generated_at": insight.updated_at}


def build_parent_overview(learner, language: str | None = None) -> dict:
    """Single aggregate for the parent dashboard + insights page. Never calls a model."""
    language = language or current_language()
    passport = build_passport(learner, language)
    stage = next((s["label"] for s in reversed(passport["journey"]) if s["done"]), None)
    base = {
        "learner": {
            "id": learner.id,
            "display_name": passport["learner"]["display_name"],
            "first_name": passport["learner"]["first_name"],
            "passport_status": passport["status"],
            "passport_number": passport["passport_number"],
            "journey_stage": stage,
        },
        "status": passport["status"],
        "journey": passport["journey"],
        "privacy_note": label("text", "privacy", language),
        "updated_at": passport["updated_at"],
    }
    if passport["status"] == "EMPTY":
        return {**base, "has_evidence": False, "parent_insight": None, "parent_insight_state": "NOT_AVAILABLE"}

    session = _latest_session(learner)
    saved = get_saved_parent_insight(session, passport["version"], language)
    mission = passport["recommended_mission"]
    return {
        **base,
        "has_evidence": True,
        "headline": passport["headline"],
        "current_signals": [
            {k: s[k] for k in ("key", "label", "score", "confidence", "evidence_count", "opportunity_count")}
            for s in passport["signals"]
        ],
        "other_signals": passport["other_signals"],
        "evidence": passport["evidence_summary"],
        "explored_dimensions": passport["explored_dimensions"],
        "recent_activity": [
            {k: e[k] for k in ("id", "title", "source_label", "created_at")}
            | {"dimensions": [d["label"] for d in e["dimensions"]]}
            for e in passport["recent_evidence"]
        ],
        "emerging_strengths": passport["emerging_strengths"],
        "areas_to_explore": passport["exploration_gaps"],
        "uncertainty_notes": passport["uncertainty_notes"],
        "next_step": {
            "title": passport["next_step"]["title"],
            "activity_type": passport["next_step"]["activity_type"],
            "signals": [s["label"] for s in passport["next_step"]["signals_used"]],
        }
        if passport["next_step"]
        else None,
        "next_mission": {
            "title": mission["title"],
            "short_description": mission["short_description"],
            "time_label": mission["time_label"],
            "focus_areas": mission["focus_areas"],
            "status": mission["my_attempt"]["status"] if mission["my_attempt"] else "NOT_STARTED",
        }
        if mission
        else None,
        "parent_insight": _insight_payload(saved),
        "parent_insight_state": "READY" if saved else "PENDING",
    }


def ensure_parent_insight(learner, language: str | None = None) -> dict | None:
    """Get-or-generate the Parent Insight for the learner's current Passport version in the
    request language. Idempotent and locked; at most one model call per evidence state and language."""
    language = language or current_language()
    passport = build_passport(learner, language)
    if passport["status"] == "EMPTY":
        return None
    insight = get_or_create_parent_insight(
        _latest_session(learner), passport["version"], parent_insight_input(passport, language), language
    )
    return _insight_payload(insight)
