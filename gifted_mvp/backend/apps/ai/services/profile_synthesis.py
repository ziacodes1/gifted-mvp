"""AI Profile Synthesis + Next-Step Recommendation.

Flow: trusted deterministic signals (re-derived from the session's stored
responses) → compact JSON prompt → provider → schema + language validation →
persisted `AIInsight`. Any failure → deterministic fallback, also persisted.
The LLM never sees raw answers, the question bank, or personal data.
"""
from __future__ import annotations

import re
from datetime import timedelta

from pydantic import ValidationError

from apps.assessments.models import AssessmentSession
from apps.assessments.services.scoring import score_session
from apps.signals.models import Signal, SignalCategory

from ..models import AIInsight, GenerationType
from ..prompts import PROFILE_SYNTHESIS_SYSTEM, PROMPT_VERSION
from ..schemas import PROFILE_SYNTHESIS_JSON_SCHEMA, ProfileInsight
from .generation import Generated, check_language, get_or_generate, run_structured, saved_insight
from .provider import get_provider

SCORING_VERSION = "s2"  # bump if apps.assessments.services.scoring semantics change
INPUT_VERSION = f"{SCORING_VERSION}-{PROMPT_VERSION}"
FALLBACK_RETRY_AFTER = timedelta(minutes=10)

# Deterministic phrases the product must never show (spec §4).
_FORBIDDEN = re.compile(
    r"you are definitely|you should become|you are bad at|no potential|"
    r"your future career is|you will become|you are destined",
    re.IGNORECASE,
)


# --- Input -----------------------------------------------------------------

def build_signal_input(session: AssessmentSession) -> dict:
    """Compact, trusted input. Interests (incl. zero-evidence ones, to show gaps) are
    the primary signals; other categories are passed separately so the model can't
    blur interest, ability and exposure together."""
    results = score_session(session)
    scored = {r.key: r for r in results}
    signals = []
    for s in Signal.objects.filter(is_active=True, category=SignalCategory.INTEREST).order_by("key"):
        r = scored.get(s.key)
        signals.append(
            {
                "key": s.key,
                "label": s.label,
                "score": r.score if r else 0,
                "confidence": r.confidence if r else "LOW",
                "evidence_count": r.evidence_count if r else 0,
                "chances": r.opportunity_count if r else 0,
            }
        )
    signals.sort(key=lambda x: (-x["score"], x["key"]))
    other = [r for r in results if r.category != SignalCategory.INTEREST]
    return {
        "assessment": session.assessment.title,
        "questions_answered": session.responses.count(),
        "signal_notes": (
            "score = share of chances where the learner picked it. INTEREST = what they enjoy; "
            "APTITUDE = 1-2 short puzzles (early evidence only, never a verdict); WORK_STYLE and "
            "VALUE = self-described preferences; EXPOSURE = what they say they've tried (experience, not skill)."
        ),
        "signals": signals,
        "other_signals": [
            {
                "key": r.key,
                "label": r.label,
                "category": r.category,
                "picked": r.evidence_count,
                "chances": r.opportunity_count,
                "confidence": r.confidence,
            }
            for r in other
            if r.evidence_count > 0 and r.category != SignalCategory.EXPOSURE
        ],
        "exposure_tried": [r.label for r in other if r.category == SignalCategory.EXPOSURE and r.evidence_count > 0],
        "exposure_not_tried": [r.label for r in other if r.category == SignalCategory.EXPOSURE and r.evidence_count == 0],
    }


# --- Validation ------------------------------------------------------------

def validate_ai_output(raw: dict, known_keys: set[str]) -> dict:
    """Schema + product-language validation. Raises ValueError if unusable."""
    try:
        parsed = ProfileInsight.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(f"schema: {exc.error_count()} errors") from exc
    data = parsed.model_dump()
    if not data["profile"]["emerging_strengths"]:
        raise ValueError("schema: no emerging_strengths")
    check_language(data, _FORBIDDEN)
    used = [k for k in data["next_step"]["signals_used"] if k in known_keys]
    if not used:
        raise ValueError("signals_used references no known signal")
    data["next_step"]["signals_used"] = used
    return data


# --- Deterministic fallback -------------------------------------------------

_EXPLORATIONS = {
    "realistic": (
        "Try a hands-on build challenge",
        "challenge",
        "Build a small working model (a paper bridge, a simple circuit, or a cardboard "
        "prototype) in about 30 minutes.",
    ),
    "investigative": (
        "Run a mini home experiment",
        "experiment",
        "Pick a question you are curious about, make a prediction, test it, and write "
        "down what surprised you.",
    ),
    "artistic": (
        "Create a one-page visual idea",
        "project",
        "Design a poster, sketch, or short storyboard that explains something you care about.",
    ),
    "social": (
        "Help someone learn something",
        "conversation",
        "Spend 20 minutes explaining or teaching a skill to a friend or family member, then "
        "reflect on how it felt.",
    ),
    "enterprising": (
        "Pitch a small idea",
        "challenge",
        "Come up with a small idea to improve something at school or home and pitch it in "
        "two minutes to someone.",
    ),
}
_DEFAULT_EXPLORATION = (
    "Try a short exploration activity",
    "reflection",
    "Try one small activity in your strongest area and notice what you enjoy.",
)


def build_fallback(signal_input: dict) -> dict:
    signals = signal_input["signals"]
    with_evidence = [s for s in signals if s["evidence_count"] > 0]
    top = with_evidence[:3] or signals[:1]
    gaps = [s for s in signals if s["evidence_count"] == 0 or s["confidence"] == "LOW"]
    lead = top[0]
    conf = {"HIGH": "consistent", "MEDIUM": "moderate", "LOW": "early"}

    if len(top) > 1:
        headline = f"Early signals point toward {top[0]['label']} and {top[1]['label']}"
    else:
        headline = f"An early signal points toward {lead['label']}"

    title, activity_type, how = _EXPLORATIONS.get(lead["key"], _DEFAULT_EXPLORATION)

    profile = {
        "headline": headline,
        "summary": (
            f"Your current evidence suggests a stronger interest in {lead['label']}"
            + (f", followed by {top[1]['label']}" if len(top) > 1 else "")
            + ". These signals come from one short assessment, so they are a starting point "
            "rather than a conclusion. This profile will evolve as more evidence is collected."
        ),
        "emerging_strengths": [
            {
                "title": s["label"],
                "reason": (
                    f"You picked this direction {s['evidence_count']} of {s['chances']} times — "
                    f"{conf[s['confidence']]} evidence so far."
                ),
            }
            for s in top
        ],
        "exposure_gaps": (
            [f"You haven't tried {label.lower()} yet — that's an open area to explore." for label in signal_input.get("exposure_not_tried", [])[:2]]
            + [f"There is not enough evidence yet about {s['label']}." for s in gaps[:2]]
        )[:4],
        "uncertainty_notes": [
            "These signals reflect preferences from one assessment, not real-world experience.",
            "Interests often shift with exposure — trying things is the best way to learn more.",
        ],
        "suggested_explorations": [
            _EXPLORATIONS.get(s["key"], _DEFAULT_EXPLORATION)[0] for s in top[:3]
        ],
    }
    next_step = {
        "title": title,
        "activity_type": activity_type,
        "reason": (
            f"{lead['label']} is currently your strongest signal. {how} Trying this may help "
            "clarify whether this interest grows with hands-on experience."
        ),
        "signals_used": [lead["key"]],
        "intended_validation": (
            f"Whether your interest in {lead['label']} holds up in a real activity, since your "
            "current evidence comes only from assessment choices."
        ),
        "confidence_note": (
            "This is a tentative suggestion based on early signals — it is one experiment, "
            "not a verdict."
        ),
    }
    return {"profile": profile, "next_step": next_step}


# --- Orchestration ----------------------------------------------------------

def _generate(signal_input: dict) -> Generated:
    known = {s["key"] for s in signal_input["signals"]} | {s["key"] for s in signal_input.get("other_signals", [])}
    return run_structured(
        provider=get_provider(),
        system=PROFILE_SYNTHESIS_SYSTEM,
        payload=signal_input,
        schema=PROFILE_SYNTHESIS_JSON_SCHEMA,
        validate=lambda raw: validate_ai_output(raw, known),
        fallback=lambda: build_fallback(signal_input),
        feature="profile_synthesis",
    )


def get_or_create_profile_insight(session: AssessmentSession) -> AIInsight:
    """Idempotent get-or-generate (locked; FALLBACK rows retry after a cooldown)."""
    return get_or_generate(
        session=session,
        generation_type=GenerationType.PROFILE_SYNTHESIS,
        input_version=INPUT_VERSION,
        produce=lambda: _generate(build_signal_input(session)),
        retry_after=FALLBACK_RETRY_AFTER,
    )


def get_saved_profile_insight(session: AssessmentSession) -> AIInsight | None:
    """Read-only: the persisted insight for this session, if any. Never calls a provider."""
    return saved_insight(session, GenerationType.PROFILE_SYNTHESIS, INPUT_VERSION)
