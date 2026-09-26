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
from ..prompts import PARENT_INSIGHT_SYSTEM, PARENT_PROMPT_VERSION, with_language
from ..schemas import PARENT_INSIGHT_JSON_SCHEMA, ParentInsightOutput
from .generation import FALLBACK_RETRY_AFTER, check_language, get_or_generate, run_structured, saved_insight
from .provider import get_provider

_Q = "[‘’'ʻʼ`]"  # Uzbek o‘/g‘ apostrophe variants
_FORBIDDEN = re.compile(
    r"is definitely|should become|should be an? |enrol+ (them|him|her|your child)|immediately|"
    r"weak at|bad at|no potential|future career is|destined|genius|"
    # Uzbek
    rf"darhol|zudlik bilan|albatta .{{0,40}}bo{_Q}ladi|bo{_Q}lishi shart|salohiyati yo{_Q}q|qobiliyati yo{_Q}q|"
    rf"kelajakdagi kasbi|taqdiri|daho|yomon ekan|kuchsiz ekan|"
    # Russian
    r"немедленно|срочно|определ[её]нно|(?:должен|должна|следует|стоит|нужно) стать|слаб\w* в |"
    r"плохо (?:даётся|дается|получается)|нет потенциала|будущая профессия|гени(?:й|альн)|суждено",
    re.IGNORECASE,
)


def input_version(passport_version: int) -> str:
    # Language is a separate column on AIInsight, not part of this version string.
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


_MISSION_WORDS = re.compile(
    r"\bmissions?\b|\bchallenge\b|\bschool bag\b|missiya|sumka|мисси|челлендж|рюкзак|портфел",
    re.IGNORECASE,
)


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


_PARENT_TEXT = {
    "en": {
        "and": " and ",
        "conf": {"HIGH": "a consistent", "MEDIUM": "a developing", "LOW": "an early"},
        "seeing_title": "Interest in {label}",
        "seeing_expl": "Picked {n} of {m} times in the assessment — {conf} signal so far.",
        "mission_title": "Early hands-on exploration",
        "mission_dims": "Completed {missions}, adding evidence about {dims}.",
        "mission_only": "Completed {missions}.",
        "limited": "There is still limited evidence in {areas}.",
        "no_missions": "Most of the current picture comes from preferences, not yet from real-world experience.",
        "one_mission": "One mission is a single data point — patterns become clearer across several activities.",
        "summary": "The current evidence suggests a leaning toward {lead}",
        "summary_mission": " alongside a first hands-on exploration",
        "summary_tail": ". This picture is still early and will change as your child tries more things.",
        "summary_empty": "There is not enough evidence yet to describe a clear picture.",
        "support": [
            ("Ask about the experience, not the result",
             "Ask which part of their last activity felt most interesting — and why."),
            ("Offer a small try before a big commitment",
             "Suggest a short, free activity related to {lead} before considering any longer course.",
             "Suggest one short, free activity in something new before any longer commitment."),
            ("Notice what gives them energy",
             "Pay attention to what they talk about unprompted this week, without steering it."),
        ],
        "starter_mission": "What did you enjoy most about {mission}?",
        "starter": "If you could spend an afternoon making or exploring anything, what would it be?",
        "caution": "At this stage, exploring widely is more useful than making a fixed career decision.",
    },
    "uz": {
        "and": " va ",
        "conf": {"HIGH": "barqaror", "MEDIUM": "shakllanayotgan", "LOW": "dastlabki"},
        "seeing_title": "«{label}» yo‘nalishiga qiziqish",
        "seeing_expl": "Testda {m} imkoniyatdan {n} marta tanlangan — hozircha bu {conf} belgi.",
        "mission_title": "Dastlabki amaliy izlanish",
        "mission_dims": "«{missions}» bajarildi va {dims} bo‘yicha yangi ma’lumot qo‘shildi.",
        "mission_only": "«{missions}» bajarildi.",
        "limited": "{areas} bo‘yicha hali ma’lumot kam.",
        "no_missions": "Hozirgi manzara asosan hayotiy tajribadan emas, farzandingizning tanlovlaridan olingan.",
        "one_mission": "Bitta missiya — bu bitta ma’lumot nuqtasi; qonuniyatlar bir nechta mashg‘ulotdan keyin aniqroq ko‘rinadi.",
        "summary": "Hozirgi ma’lumotlar farzandingizda «{lead}» yo‘nalishiga moyillik borligini ko‘rsatmoqda",
        "summary_mission": ", shuningdek, birinchi amaliy izlanish ham bor",
        "summary_tail": ". Bu hali dastlabki manzara va farzandingiz yangi narsalarni sinab ko‘rgan sari o‘zgarib boradi.",
        "summary_empty": "Aniq manzarani tasvirlash uchun hali yetarli ma’lumot yo‘q.",
        "support": [
            ("Natija haqida emas, tajriba haqida so‘rang",
             "Oxirgi mashg‘ulotning qaysi qismi eng qiziqarli bo‘lganini va nima uchunligini so‘rang."),
            ("Katta qarordan oldin kichik sinovni taklif qiling",
             "Uzoq kurs haqida o‘ylashdan oldin «{lead}» bilan bog‘liq qisqa, bepul mashg‘ulotni taklif qiling.",
             "Uzoq muddatli qarordan oldin yangi sohada bitta qisqa, bepul mashg‘ulotni taklif qiling."),
            ("Unga nima kuch berishini kuzating",
             "Bu hafta farzandingiz hech kim so‘ramasa ham nima haqida gapirayotganiga e’tibor bering — uni yo‘naltirmasdan."),
        ],
        "starter_mission": "«{mission}» missiyasida senga eng ko‘p nima yoqdi?",
        "starter": "Agar butun kunni istalgan narsani yasash yoki o‘rganishga sarflay olsang, nimani tanlarding?",
        "caution": "Hozircha keng izlanish qat’iy kasb tanlashdan ko‘ra foydaliroq.",
    },
    "ru": {
        "and": " и ",
        "conf": {"HIGH": "устойчивый", "MEDIUM": "формирующийся", "LOW": "ранний"},
        "seeing_title": "Интерес к направлению «{label}»",
        "seeing_expl": "Выбрано в {n} из {m} случаев в тесте — пока это {conf} сигнал.",
        "mission_title": "Первое практическое исследование",
        "mission_dims": "Выполнено: «{missions}». Это добавило данные о направлениях: {dims}.",
        "mission_only": "Выполнено: «{missions}».",
        "limited": "Пока мало данных по направлениям: {areas}.",
        "no_missions": "Сейчас картина складывается в основном из предпочтений, а не из реального опыта.",
        "one_mission": "Одна миссия — это лишь одна точка данных; закономерности станут яснее после нескольких занятий.",
        "summary": "Текущие данные указывают на склонность к направлению «{lead}»",
        "summary_mission": " и первый практический опыт",
        "summary_tail": ". Эта картина пока ранняя и будет меняться по мере того, как ребёнок пробует новое.",
        "summary_empty": "Пока недостаточно данных, чтобы описать понятную картину.",
        "support": [
            ("Спрашивайте об опыте, а не о результате",
             "Спросите, какая часть последнего занятия показалась самой интересной — и почему."),
            ("Предложите небольшую пробу до серьёзного решения",
             "Предложите короткое бесплатное занятие, связанное с направлением «{lead}», прежде чем думать о длительном курсе.",
             "Предложите одно короткое бесплатное занятие в чём-то новом, прежде чем принимать долгосрочные решения."),
            ("Замечайте, что даёт ребёнку энергию",
             "Обратите внимание, о чём ребёнок сам заговаривает на этой неделе, не подталкивая его."),
        ],
        "starter_mission": "Что тебе больше всего понравилось в миссии «{mission}»?",
        "starter": "Чем бы тебе хотелось заняться, если бы целый день можно было что-то создавать или исследовать?",
        "caution": "Сейчас широкий поиск полезнее, чем окончательный выбор профессии.",
    },
}


def _join(labels: list[str], sep: str = " and ") -> str:
    return labels[0] if len(labels) == 1 else ", ".join(labels[:-1]) + sep + labels[-1]


def build_parent_fallback(data: dict, language: str = "en") -> dict:
    """Deterministic, signal-based guidance used without (or instead of) the model,
    in the requested language (labels in `data` are already localized)."""
    t = _PARENT_TEXT.get(language, _PARENT_TEXT["en"])
    join = lambda items: _join(items, t["and"])  # noqa: E731
    signals = data["signals"]
    lead = signals[0]["label"] if signals else None
    missions = data["missions_completed"]
    dims = [d["label"] for d in data["explored_through_missions"]][:3]
    limited = (data.get("exposure_not_tried") or data["limited_evidence_areas"])[:3]
    conf = t["conf"]

    seeing = [
        {
            "title": t["seeing_title"].format(label=s["label"]),
            "explanation": t["seeing_expl"].format(n=s["evidence_count"], m=s["chances"], conf=conf[s["confidence"]]),
        }
        for s in signals[:2]
    ]
    if missions:
        dims_text = (join(dims).lower() if language == "en" else join(dims)) if dims else ""
        seeing.append(
            {
                "title": t["mission_title"],
                "explanation": t["mission_dims"].format(missions=join(missions), dims=dims_text)
                if dims
                else t["mission_only"].format(missions=join(missions)),
            }
        )

    unclear = [t["limited"].format(areas=join(limited))] if limited else []
    unclear.append(t["one_mission"] if missions else t["no_missions"])

    (s1_title, s1_action), (s2_title, s2_lead, s2_plain), (s3_title, s3_action) = t["support"]
    return {
        "summary": (
            t["summary"].format(lead=lead) + (t["summary_mission"] if missions else "") + t["summary_tail"]
            if lead
            else t["summary_empty"]
        ),
        "what_we_are_seeing": seeing[:3],
        "what_is_still_unclear": unclear[:3],
        "support_at_home": [
            {"title": s1_title, "action": s1_action},
            {"title": s2_title, "action": s2_lead.format(lead=lead) if lead else s2_plain},
            {"title": s3_title, "action": s3_action},
        ],
        "conversation_starter": (
            t["starter_mission"].format(mission=missions[0]) if missions else t["starter"]
        ),
        "caution": t["caution"],
    }


def _generate(data: dict, language: str = "en"):
    return run_structured(
        provider=get_provider(),
        system=with_language(PARENT_INSIGHT_SYSTEM, language),
        payload=data,
        schema=PARENT_INSIGHT_JSON_SCHEMA,
        validate=lambda raw: validate_parent_output(raw, data),
        fallback=lambda: build_parent_fallback(data, language),
        max_tokens=1500,
        feature=f"parent_insight lang={language}",
    )


def get_or_create_parent_insight(
    session: AssessmentSession, passport_version: int, data: dict, language: str = "en"
) -> AIInsight:
    """`data` must already carry labels in `language` (see apps.parents.services)."""
    return get_or_generate(
        session=session,
        generation_type=GenerationType.PARENT_INSIGHT,
        input_version=input_version(passport_version),
        produce=lambda: _generate(data, language),
        retry_after=FALLBACK_RETRY_AFTER,
        language=language,
    )


def get_saved_parent_insight(session: AssessmentSession, passport_version: int, language: str = "en") -> AIInsight | None:
    return saved_insight(session, GenerationType.PARENT_INSIGHT, input_version(passport_version), language)
