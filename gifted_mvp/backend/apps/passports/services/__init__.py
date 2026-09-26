"""Passport service layer: lifecycle sync + one-shot read model.

Trust rules:
- Scores come only from `LearnerSignal` (deterministic assessment scoring).
- Non-assessment evidence (missions, later labs/opportunities) comes only from
  `apps.evidence` and is shown alongside — it never rewrites assessment scores.
- Interpretation comes only from the persisted `AIInsight`; if there is none
  the deterministic fallback is derived on the fly. No LLM call ever happens here,
  and new evidence does not trigger regeneration (that is a later explicit action).
- Display text follows the request language (`common.i18n`); scores, statuses and
  evidence never depend on it. A saved insight is only reused in its own language.
"""
from __future__ import annotations

from collections import OrderedDict

from django.db import transaction
from django.db.models import Count

from apps.ai.models import InsightSource
from apps.ai.services.profile_synthesis import (
    build_fallback,
    build_signal_input,
    get_saved_profile_insight,
)
from apps.assessments.models import AssessmentSession, SessionStatus
from apps.evidence.models import Evidence, EvidenceSource
from apps.missions.models import MissionAttempt
from apps.missions.serializers import evidence_title, mission_summary
from apps.missions.services import featured_mission, match_mission
from apps.signals.models import LearnerSignal
from common.i18n import current_language, label, tr

from ..models import Passport, PassportStatus

# Journey stages (labels in common.i18n). Discover = assessment; Explore = first exploration mission.
JOURNEY_STAGES = ["discover", "explore", "validate", "develop", "guide"]

_NON_ASSESSMENT = [s for s in EvidenceSource.values if s != EvidenceSource.ASSESSMENT]


def _latest_completed_session(learner) -> AssessmentSession | None:
    return (
        AssessmentSession.objects.filter(learner=learner, status=SessionStatus.COMPLETED)
        .select_related("assessment")
        .order_by("-completed_at")
        .first()
    )


@transaction.atomic
def sync_passport(learner, session: AssessmentSession | None = None) -> Passport:
    """Create the learner's Passport if missing and move it to the state the
    evidence supports. `version` bumps only when new evidence is reflected
    (new completed session or new evidence record) — never on plain reads.

    EMPTY → no completed assessment. EMERGING → assessment only.
    GROWING → at least one non-assessment evidence record (e.g. a mission).
    """
    passport, _ = Passport.objects.select_for_update().get_or_create(learner=learner)
    if session is None:
        session = _latest_completed_session(learner)

    evidence = Evidence.objects.filter(learner=learner)
    latest_evidence_id = evidence.order_by("-id").values_list("id", flat=True).first()
    if session is None:
        status = PassportStatus.EMPTY
    elif evidence.filter(source_type__in=_NON_ASSESSMENT).exists():
        status = PassportStatus.GROWING
    else:
        status = PassportStatus.EMERGING

    state = (status, session.id if session else None, latest_evidence_id)
    if state != (passport.status, passport.source_session_id, passport.last_evidence_id):
        new_evidence = (
            state[1] != passport.source_session_id or state[2] != passport.last_evidence_id
        ) and session is not None
        passport.status, passport.source_session_id, passport.last_evidence_id = state
        passport.version += 1 if new_evidence else 0
        passport.save()
    return passport


def _display_name(learner) -> str:
    return learner.full_name.strip() or learner.email.split("@")[0]


def _insight_for(session: AssessmentSession, language: str):
    """(insight dict, source, saved_row_or_None, responses_answered) in `language`.
    Read-only, never calls a provider."""
    saved = get_saved_profile_insight(session, language)
    if saved is not None:
        return saved.result, saved.source, saved, None
    signal_input = build_signal_input(session, language)
    return build_fallback(signal_input, language), InsightSource.FALLBACK, None, signal_input["questions_answered"]


def current_next_step(learner) -> dict | None:
    session = _latest_completed_session(learner)
    return _insight_for(session, current_language())[0]["next_step"] if session else None


def _recommended_mission(learner, next_step: dict | None) -> dict | None:
    mission = featured_mission()
    if mission is None:
        return None
    attempt = MissionAttempt.objects.filter(learner=learner, mission=mission).first()
    return {
        **mission_summary(mission),
        "match": match_mission(next_step, mission),
        "my_attempt": {"id": attempt.id, "status": attempt.status} if attempt else None,
    }


def _evidence_overview(learner) -> dict:
    """Counts, recent items and explored dimensions from non-assessment evidence."""
    counts = dict(
        Evidence.objects.filter(learner=learner)
        .values_list("source_type")
        .annotate(n=Count("id"))
        .values_list("source_type", "n")
    )
    recent = list(
        Evidence.objects.filter(learner=learner, source_type__in=_NON_ASSESSMENT)
        .prefetch_related("contributions__signal")
        .order_by("-created_at")[:5]
    )
    dimensions: OrderedDict[str, dict] = OrderedDict()
    recent_items = []
    for ev in recent:
        dims = []
        for c in sorted(ev.contributions.all(), key=lambda c: (-c.weight, c.signal.label)):
            signal_label, kind_label = tr(c.signal, "label"), label("evidence_kind", c.kind)
            dims.append({"key": c.signal.key, "label": signal_label, "kind_label": kind_label})
            d = dimensions.setdefault(
                c.signal.key, {"key": c.signal.key, "label": signal_label, "kinds": [], "activities": 0}
            )
            d["activities"] += 1
            if kind_label not in d["kinds"]:
                d["kinds"].append(kind_label)
        recent_items.append(
            {
                "id": ev.id,
                "title": evidence_title(ev),
                "source_type": ev.source_type,
                "source_label": label("evidence_source", ev.source_type),
                "created_at": ev.created_at,
                "dimensions": dims,
            }
        )
    return {
        "counts": counts,
        "recent": recent_items,
        "dimensions": list(dimensions.values()),
        "latest_at": recent[0].created_at if recent else None,
    }


def passport_snapshot(learner) -> dict:
    """Tiny status payload for post-mission screens."""
    passport = sync_passport(learner)
    missions = Evidence.objects.filter(learner=learner, source_type=EvidenceSource.MISSION).count()
    return {"status": passport.status, "version": passport.version, "missions": missions}


def build_passport(learner, language: str | None = None) -> dict:
    language = language or current_language()
    session = _latest_completed_session(learner)
    passport = sync_passport(learner, session)
    overview = _evidence_overview(learner) if session else None
    missions_done = overview["counts"].get(EvidenceSource.MISSION, 0) if overview else 0

    base = {
        "learner": {
            "display_name": _display_name(learner),
            "first_name": _display_name(learner).split(" ")[0],
            "member_since": learner.date_joined,
        },
        "passport_number": passport.passport_number,
        "version": passport.version,
        "status": passport.status,
        "journey": [
            {
                "key": key,
                "label": label("journey", key, language),
                "done": (key == "discover" and session is not None) or (key == "explore" and missions_done > 0),
            }
            for key in JOURNEY_STAGES
        ],
        "message": label("text", "evolving", language),
        "updated_at": passport.updated_at,
    }

    if session is None:
        return {
            **base,
            "headline": None,
            "summary": None,
            "insight_source": None,
            "insight_covers_new_evidence": True,
            "signals": [],
            "other_signals": [],
            "emerging_strengths": [],
            "exploration_gaps": [],
            "uncertainty_notes": [],
            "suggested_explorations": [],
            "next_step": None,
            "recommended_mission": None,
            "evidence_summary": {"total": 0, "assessment": 0, "missions": 0, "opportunities": 0, "experiences": 0},
            "evidence_sources": {"assessments": 0, "missions": 0},
            "recent_evidence": [],
            "explored_dimensions": [],
        }

    learner_signals = list(
        LearnerSignal.objects.filter(learner=learner, opportunity_count__gt=0)
        .select_related("signal")
        .order_by("-score", "signal__key")
    )

    def row(ls):
        return {
            "key": ls.signal.key,
            "label": tr(ls.signal, "label", language),
            "category": ls.signal.category,
            "score": ls.score,
            "confidence": ls.confidence,
            "evidence_count": ls.evidence_count,
            "opportunity_count": ls.opportunity_count,
        }

    # `signals` = interests with evidence (cards, AI, parent picture). Other categories
    # (aptitude, work style, values, exposure incl. "not tried yet") are grouped separately.
    signals = [row(ls) for ls in learner_signals if ls.signal.category == "INTEREST" and ls.evidence_count > 0]
    other_signals = [row(ls) for ls in learner_signals if ls.signal.category != "INTEREST"]
    labels = {s["key"]: s["label"] for s in signals}

    insight, source, saved, answered = _insight_for(session, language)
    profile, step = insight["profile"], insight["next_step"]
    assessment_responses = answered if answered is not None else session.responses.count()
    counts = overview["counts"]
    opportunities = counts.get(EvidenceSource.OPPORTUNITY, 0)
    experiences = counts.get(EvidenceSource.REAL_WORLD, 0)
    updated_at = max(t for t in (passport.updated_at, saved and saved.updated_at, overview["latest_at"]) if t)

    return {
        **base,
        "updated_at": updated_at,
        "headline": profile["headline"],
        "summary": profile["summary"],
        "insight_source": source,
        # The interpretation (AI or fallback) is built from assessment signals only;
        # once mission/other evidence exists the UI says so instead of re-generating.
        "insight_covers_new_evidence": overview["latest_at"] is None,
        "signals": signals,
        "other_signals": other_signals,
        "emerging_strengths": profile["emerging_strengths"],
        "exploration_gaps": profile["exposure_gaps"],
        "uncertainty_notes": profile["uncertainty_notes"],
        "suggested_explorations": profile["suggested_explorations"],
        "next_step": {
            "title": step["title"],
            "activity_type": step["activity_type"],
            "reason": step["reason"],
            "intended_validation": step["intended_validation"],
            "confidence_note": step["confidence_note"],
            "signals_used": [{"key": k, "label": labels.get(k, k)} for k in step["signals_used"]],
        },
        "recommended_mission": _recommended_mission(learner, step),
        "evidence_summary": {
            "total": assessment_responses + missions_done + opportunities + experiences,
            "assessment": assessment_responses,
            "missions": missions_done,
            "opportunities": opportunities,
            "experiences": experiences,
        },
        "evidence_sources": {
            # Pre-evidence-era sessions have no ASSESSMENT evidence row; a session exists here.
            "assessments": max(counts.get(EvidenceSource.ASSESSMENT, 0), 1),
            "missions": missions_done,
        },
        "recent_evidence": overview["recent"],
        "explored_dimensions": overview["dimensions"],
    }
