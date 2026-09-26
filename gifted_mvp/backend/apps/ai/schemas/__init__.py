"""Provider-agnostic structured contracts for AI services.

`PROFILE_SYNTHESIS_JSON_SCHEMA` is what a provider is asked to produce;
`ProfileInsight` (pydantic, extra=forbid) is what we actually accept. Anything
that fails validation is rejected and the deterministic fallback is used.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EmergingStrength(_Strict):
    title: str = Field(min_length=1, max_length=80)
    reason: str = Field(min_length=1, max_length=400)


class ProfileSynthesis(_Strict):
    headline: str = Field(min_length=1, max_length=140)
    summary: str = Field(min_length=1, max_length=900)
    emerging_strengths: list[EmergingStrength] = Field(max_length=4)
    exposure_gaps: list[str] = Field(max_length=5)
    uncertainty_notes: list[str] = Field(max_length=4)
    suggested_explorations: list[str] = Field(max_length=4)


class NextStepRecommendation(_Strict):
    title: str = Field(min_length=1, max_length=120)
    activity_type: str = Field(min_length=1, max_length=40)
    reason: str = Field(min_length=1, max_length=600)
    signals_used: list[str] = Field(max_length=5)
    intended_validation: str = Field(min_length=1, max_length=400)
    confidence_note: str = Field(min_length=1, max_length=400)


class ProfileInsight(_Strict):
    profile: ProfileSynthesis
    next_step: NextStepRecommendation


def keep_first(raw, limits: dict[str, int], nested: dict[str, dict[str, int]] | None = None):
    """Models sometimes return more list items than asked for (e.g. 5 where the prompt says 1-3).
    Keep the first N instead of discarding an otherwise valid answer; everything else is still
    validated strictly (types, lengths, banned phrases, grounding)."""
    if not isinstance(raw, dict):
        return raw
    out = dict(raw)
    for key, limit in limits.items():
        if isinstance(out.get(key), list):
            out[key] = out[key][:limit]
    for key, sub in (nested or {}).items():
        out[key] = keep_first(out.get(key), sub)
    return out


PARENT_LIST_LIMITS = {"what_we_are_seeing": 3, "what_is_still_unclear": 3, "support_at_home": 3}
PROFILE_LIST_LIMITS = {
    "profile": {"emerging_strengths": 4, "exposure_gaps": 5, "uncertainty_notes": 4, "suggested_explorations": 4},
    "next_step": {"signals_used": 5},
}


def _obj(props: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": props,
        "required": required or list(props),
        "additionalProperties": False,
    }


_STR = {"type": "string"}
_STR_LIST = {"type": "array", "items": _STR}

PROFILE_SYNTHESIS_JSON_SCHEMA: dict = _obj(
    {
        "profile": _obj(
            {
                "headline": _STR,
                "summary": _STR,
                "emerging_strengths": {
                    "type": "array",
                    "items": _obj({"title": _STR, "reason": _STR}),
                },
                "exposure_gaps": _STR_LIST,
                "uncertainty_notes": _STR_LIST,
                "suggested_explorations": _STR_LIST,
            }
        ),
        "next_step": _obj(
            {
                "title": _STR,
                "activity_type": _STR,
                "reason": _STR,
                "signals_used": _STR_LIST,
                "intended_validation": _STR,
                "confidence_note": _STR,
            }
        ),
    }
)


# --- Parent insight ---------------------------------------------------------------


class SeeingItem(_Strict):
    title: str = Field(min_length=1, max_length=90)
    explanation: str = Field(min_length=1, max_length=400)


class SupportItem(_Strict):
    title: str = Field(min_length=1, max_length=90)
    action: str = Field(min_length=1, max_length=320)


class ParentInsightOutput(_Strict):
    summary: str = Field(min_length=1, max_length=700)
    what_we_are_seeing: list[SeeingItem] = Field(min_length=1, max_length=3)
    what_is_still_unclear: list[str] = Field(min_length=1, max_length=3)
    support_at_home: list[SupportItem] = Field(min_length=2, max_length=3)
    conversation_starter: str = Field(min_length=1, max_length=260)
    caution: str = Field(min_length=1, max_length=320)


PARENT_INSIGHT_JSON_SCHEMA: dict = _obj(
    {
        "summary": _STR,
        "what_we_are_seeing": {"type": "array", "items": _obj({"title": _STR, "explanation": _STR})},
        "what_is_still_unclear": _STR_LIST,
        "support_at_home": {"type": "array", "items": _obj({"title": _STR, "action": _STR})},
        "conversation_starter": _STR,
        "caution": _STR,
    }
)


# --- AI Companion ---------------------------------------------------------------


class CompanionReply(_Strict):
    reply: str = Field(min_length=1, max_length=3000)
    suggest_diary: bool = False  # the student's message is a personal moment worth keeping


COMPANION_REPLY_JSON_SCHEMA: dict = _obj({"reply": _STR, "suggest_diary": {"type": "boolean"}})
