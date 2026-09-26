"""AI Companion reply generation, on the shared provider layer (`run_structured`).

Input is compact JSON: the trusted learner context assembled by `apps.companion`
(deterministic signals, mission dimensions, journey — no names, scores rules or raw
answers), the last few turns of this conversation and the new message. Output is a
single validated `reply` string in the request language.

Unlike profile synthesis there is no deterministic fallback text: if the provider fails
or the reply is rejected, `generate_reply` returns None and the caller shows a calm
"try again" state. A chat must never show a fake answer.
"""
from __future__ import annotations

import re

from pydantic import ValidationError

from ..prompts import COMPANION_PROMPT_VERSION, companion_system
from ..schemas import COMPANION_REPLY_JSON_SCHEMA, CompanionReply
from .generation import check_language, run_structured
from .provider import get_provider

HISTORY_TURNS = 10  # previous messages sent with each request
HISTORY_CHARS = 1200  # per previous message

_Q = "[‘’'ʻʼ`]"  # Uzbek o‘/g‘ apostrophe variants
_FORBIDDEN = re.compile(
    r"you(?: are|'re|’re) definitely|you should become|this proves|you(?: are|'re|’re) not suited|"
    r"you(?: are|'re|’re) (?:clearly )?meant to be|you(?: are|'re|’re) destined|no potential|your future career is|"
    # Uzbek
    rf"albatta .{{0,40}}bo{_Q}lasiz|bo{_Q}lishingiz shart|salohiyatingiz yo{_Q}q|qobiliyatingiz yo{_Q}q|"
    rf"kelajakdagi kasbingiz|taqdiringiz|sizga to{_Q}g{_Q}ri kelmaydi|"
    # Russian
    r"(?:ты|вы) определ[её]нно|(?:тебе|вам) (?:следует|стоит|нужно) стать|(?:ты|вы) должн\w* стать|"
    r"нет (?:способностей|потенциала)|(?:твоя|ваша) будущая профессия|это доказывает|суждено|"
    r"(?:тебе|вам) не подходит",
    re.IGNORECASE,
)


def validate_reply(raw: dict) -> dict:
    try:
        data = CompanionReply.model_validate(raw).model_dump()
    except ValidationError as exc:
        raise ValueError(f"schema: {exc.error_count()} errors") from exc
    check_language(data, _FORBIDDEN)
    return data


# Deterministic safety net: if the learner's message suggests they may be at risk and the
# reply doesn't already point them to a trusted adult, a short support line is appended.
# Not a diagnosis and nothing is stored beyond the reply itself.
_RISK = re.compile(
    r"kill myself|suicid|end my life|want to die|wanna die|hurt(?:ing)? myself|self[- ]?harm|cut myself|"
    r"want to disappear|don.?t want to (?:be here|live|exist)|no reason to live|better off without me|"
    rf"o{_Q}zimni o{_Q}ldir|o{_Q}lgim kel|yashagim kelmay|g{_Q}oyib bo{_Q}lgim|yo{_Q}q bo{_Q}lib ketgim|o{_Q}zimga zarar|"
    r"убить себя|убью себя|покончить с собой|суицид|хочу умереть|не хочу жить|хочу исчезнуть|"
    r"навредить себе|порезать себя|режу себя|лучше бы меня не было",
    re.IGNORECASE,
)
_POINTS_TO_ADULT = re.compile(
    rf"trusted adult|counsel|teacher|emergency|ishonchli|kattalar|o{_Q}qituvchi|psixolog|favqulodda|"
    r"взросл|учител|психолог|экстренн",
    re.IGNORECASE,
)
SUPPORT_LINE = {
    "en": "What you’re feeling matters. If you ever feel unsafe or think about hurting yourself, please talk to a trusted adult today — a parent, teacher or school counsellor — or call your local emergency number.",
    "uz": "His qilayotganlaringiz muhim. Agar o‘zingizni xavf ostida his qilsangiz yoki o‘zingizga zarar yetkazish haqida o‘ylasangiz, iltimos, bugunoq ishonchli kattalar — ota-onangiz, o‘qituvchingiz yoki maktab psixologi bilan gaplashing yoki favqulodda xizmatlarga qo‘ng‘iroq qiling.",
    "ru": "То, что ты чувствуешь, важно. Если тебе небезопасно или ты думаешь о том, чтобы навредить себе, пожалуйста, поговори сегодня со взрослым, которому доверяешь, — с родителем, учителем или школьным психологом — или позвони в местную экстренную службу.",
}


def with_safety_line(message: str, reply: str, language: str) -> str:
    if _RISK.search(message) and not _POINTS_TO_ADULT.search(reply):
        return f"{reply.rstrip()}\n\n{SUPPORT_LINE.get(language, SUPPORT_LINE['en'])}"
    return reply


def build_payload(context: dict, history: list[tuple[str, str]], message: str) -> dict:
    """`history` = [(role, content)] oldest first, roles USER|ASSISTANT."""
    # The message comes first so the model answers it rather than the profile.
    return {
        "student_message": message,
        "conversation": [
            {"from": "student" if role == "USER" else "companion", "text": text[:HISTORY_CHARS]}
            for role, text in history[-HISTORY_TURNS:]
        ],
        "learner_context": context,
    }


def generate_reply(
    *, context: dict, history: list[tuple[str, str]], message: str, language: str = "en"
) -> tuple[str, bool, str, str] | None:
    """(reply, suggest_diary, provider, model), or None when no trustworthy reply could be produced.
    `suggest_diary` is only a hint to *offer* saving; it is never offered for risk messages."""
    provider = get_provider()
    result, source, provider_name, model = run_structured(
        provider=provider,
        system=companion_system(language),
        payload=build_payload(context, history, message),
        schema=COMPANION_REPLY_JSON_SCHEMA,
        validate=validate_reply,
        fallback=lambda: None,
        max_tokens=1200,
        feature=f"companion lang={language} v={COMPANION_PROMPT_VERSION}",
    )
    if result is None:
        return None
    suggest = bool(result["suggest_diary"]) and not _RISK.search(message)
    return with_safety_line(message, result["reply"], language), suggest, provider_name, model
