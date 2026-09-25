"""AI Parent Insight: calm, practical guidance for a connected parent.

Input is a compact dict prepared by `apps.parents.services` from trusted data only
(deterministic signals, evidence counts/dimensions, limited-evidence areas). No raw
answers, reflections or personal data. Persisted per learner Passport version, so the
model is called at most once per new evidence state.
"""
from __future__ import annotations

import re

from pydantic import ValidationError

from apps.assessments.models import AssessmentSession

from ..models import AIInsight, GenerationType
from ..prompts import PARENT_INSIGHT_SYSTEM, PARENT_PROMPT_VERSION
from ..schemas import PARENT_INSIGHT_JSON_SCHEMA, ParentInsightOutput
from .generation import FALLBACK_RETRY_AFTER, check_language, get_or_generate, run_structured, saved_insight
from .provider import get_provider

_FORBIDDEN = re.compile(
    r"is definitely|should become|should be an? |enrol+ (them|him|her|your child)|immediately|"
    r"weak at|bad at|no potential|future career is|destined|genius",
    re.IGNORECASE,
)


def input_version(passport_version: int) -> str:
    return f"{PARENT_PROMPT_VERSION}-v{passport_version}"


def validate_parent_output(raw: dict, data_in: dict | None = None) -> dict:
    try:
        data = ParentInsightOutput.model_validate(raw).model_dump()
    except ValidationError as exc:
        raise ValueError(f"schema: {exc.error_count()} errors") from exc
    check_language(data, _FORBIDDEN)
    if data_in is not None:
        check_source_grounding(data, data_in)
    return data


_MISSION_WORDS = re.compile(r"\bmissions?\b|\bchallenge\b|\bschool bag\b", re.IGNORECASE)


def check_source_grounding(data: dict, data_in: dict) -> None:
    """Deterministic guard: an item that ties a signal to missions is rejected unless a
    mission actually recorded that signal (explored_through_missions)."""
    mission_labels = {d["label"].lower() for d in data_in.get("explored_through_missions", [])}
    labels = {s["label"].lower() for s in data_in.get("signals", [])} | {
        o["label"].lower() for o in data_in.get("other_signals", [])
    }
    for item in data["what_we_are_seeing"]:
        text = f"{item['title']} {item['explanation']}".lower()
        if not _MISSION_WORDS.search(text):
            continue
        for label in labels:
            if label in text and label not in mission_labels:
                raise ValueError("grounding: assessment-only signal attributed to a mission")


def _join(labels: list[str]) -> str:
    return labels[0] if len(labels) == 1 else ", ".join(labels[:-1]) + " and " + labels[-1]


def build_parent_fallback(data: dict) -> dict:
    """Deterministic, signal-based guidance used without (or instead of) the model."""
    signals = data["signals"]
    lead = signals[0]["label"] if signals else None
    missions = data["missions_completed"]
    dims = [d["label"] for d in data["explored_through_missions"]][:3]
    limited = (data.get("exposure_not_tried") or data["limited_evidence_areas"])[:3]
    conf = {"HIGH": "a consistent", "MEDIUM": "a developing", "LOW": "an early"}

    seeing = [
        {
            "title": f"Interest in {s['label']}",
            "explanation": (
                f"Picked {s['evidence_count']} of {s['chances']} times in the assessment — "
                f"{conf[s['confidence']]} signal so far."
            ),
        }
        for s in signals[:2]
    ]
    if missions:
        seeing.append(
            {
                "title": "Early hands-on exploration",
                "explanation": f"Completed {_join(missions)}, adding evidence about {_join(dims).lower()}."
                if dims
                else f"Completed {_join(missions)}.",
            }
        )

    unclear = [f"There is still limited evidence in {_join(limited)}."] if limited else []
    unclear.append(
        "Most of the current picture comes from preferences, not yet from real-world experience."
        if not missions
        else "One mission is a single data point — patterns become clearer across several activities."
    )

    return {
        "summary": (
            f"The current evidence suggests a leaning toward {lead}"
            + (" alongside a first hands-on exploration" if missions else "")
            + ". This picture is still early and will change as your child tries more things."
            if lead
            else "There is not enough evidence yet to describe a clear picture."
        ),
        "what_we_are_seeing": seeing[:3],
        "what_is_still_unclear": unclear[:3],
        "support_at_home": [
            {
                "title": "Ask about the experience, not the result",
                "action": "Ask which part of their last activity felt most interesting — and why.",
            },
            {
                "title": "Offer a small try before a big commitment",
                "action": (
                    f"Suggest a short, free activity related to {lead} before considering any longer course."
                    if lead
                    else "Suggest one short, free activity in something new before any longer commitment."
                ),
            },
            {
                "title": "Notice what gives them energy",
                "action": "Pay attention to what they talk about unprompted this week, without steering it.",
            },
        ],
        "conversation_starter": (
            f"What did you enjoy most about {missions[0]}?" if missions else "If you could spend an afternoon making or exploring anything, what would it be?"
        ),
        "caution": "At this stage, exploring widely is more useful than making a fixed career decision.",
    }


def _generate(data: dict):
    return run_structured(
        provider=get_provider(),
        system=PARENT_INSIGHT_SYSTEM,
        payload=data,
        schema=PARENT_INSIGHT_JSON_SCHEMA,
        validate=lambda raw: validate_parent_output(raw, data),
        fallback=lambda: build_parent_fallback(data),
        max_tokens=1500,
        feature="parent_insight",
    )


def get_or_create_parent_insight(session: AssessmentSession, passport_version: int, data: dict) -> AIInsight:
    return get_or_generate(
        session=session,
        generation_type=GenerationType.PARENT_INSIGHT,
        input_version=input_version(passport_version),
        produce=lambda: _generate(data),
        retry_after=FALLBACK_RETRY_AFTER,
    )


def get_saved_parent_insight(session: AssessmentSession, passport_version: int) -> AIInsight | None:
    return saved_insight(session, GenerationType.PARENT_INSIGHT, input_version(passport_version))
