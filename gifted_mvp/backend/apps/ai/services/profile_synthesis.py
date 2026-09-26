"""AI Profile Synthesis + Next-Step Recommendation.

Flow: trusted deterministic signals (re-derived from the session's stored
responses) → compact JSON prompt → provider → schema + language validation →
persisted `AIInsight`. Any failure → deterministic fallback, also persisted.
The LLM never sees raw answers, the question bank, or personal data.
"""
from __future__ import annotations

import re
from datetime import timedelta

from django.utils import translation
from pydantic import ValidationError

from apps.assessments.models import AssessmentSession
from apps.assessments.services.scoring import score_session
from apps.signals.models import Signal, SignalCategory
from common.i18n import tr

from ..models import AIInsight, GenerationType
from ..prompts import PROFILE_SYNTHESIS_SYSTEM, PROMPT_VERSION, with_language
from ..schemas import PROFILE_SYNTHESIS_JSON_SCHEMA, ProfileInsight
from .generation import Generated, check_language, get_or_generate, run_structured, saved_insight
from .provider import get_provider

SCORING_VERSION = "s2"  # bump if apps.assessments.services.scoring semantics change
INPUT_VERSION = f"{SCORING_VERSION}-{PROMPT_VERSION}"
FALLBACK_RETRY_AFTER = timedelta(minutes=10)

# Deterministic phrases the product must never show (spec §4).
_Q = "[‘’'ʻʼ`]"  # Uzbek o‘/g‘ apostrophe variants
_FORBIDDEN = re.compile(
    r"you are definitely|you should become|you are bad at|no potential|"
    r"your future career is|you will become|you are destined|"
    # Uzbek
    rf"albatta .{{0,40}}bo{_Q}lasiz|bo{_Q}lishingiz shart|salohiyatingiz yo{_Q}q|qobiliyatingiz yo{_Q}q|"
    rf"kelajakdagi kasbingiz|taqdiringiz|yomon ekansiz|"
    # Russian
    r"(?:ты|вы) определ[её]нно|(?:тебе|вам) (?:следует|стоит|нужно) стать|(?:ты|вы) должн\w* стать|"
    r"нет (?:способностей|потенциала)|(?:твоя|ваша) будущая профессия|\b(?:ты станешь|вы станете)\b|суждено",
    re.IGNORECASE,
)


# --- Input -----------------------------------------------------------------

def build_signal_input(session: AssessmentSession, language: str = "en") -> dict:
    """Compact, trusted input. Interests (incl. zero-evidence ones, to show gaps) are
    the primary signals; other categories are passed separately so the model can't
    blur interest, ability and exposure together. Labels are in `language`; keys and
    numbers are language-independent."""
    with translation.override(language):
        results = score_session(session)
    scored = {r.key: r for r in results}
    signals = []
    for s in Signal.objects.filter(is_active=True, category=SignalCategory.INTEREST).order_by("key"):
        r = scored.get(s.key)
        signals.append(
            {
                "key": s.key,
                "label": tr(s, "label", language),
                "score": r.score if r else 0,
                "confidence": r.confidence if r else "LOW",
                "evidence_count": r.evidence_count if r else 0,
                "chances": r.opportunity_count if r else 0,
            }
        )
    signals.sort(key=lambda x: (-x["score"], x["key"]))
    other = [r for r in results if r.category != SignalCategory.INTEREST]
    return {
        "assessment": tr(session.assessment, "title", language),
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
# One template set per supported language, so a Uzbek/Russian page never shows an
# English fallback paragraph. Logic is identical across languages.

_EXPLORATIONS = {
    "en": {
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
        None: (
            "Try a short exploration activity",
            "reflection",
            "Try one small activity in your strongest area and notice what you enjoy.",
        ),
    },
    "uz": {
        "realistic": (
            "Amaliy qurish mashqini sinab ko‘ring",
            "challenge",
            "Taxminan 30 daqiqada kichik ishlaydigan model yasang: qog‘oz ko‘prik, oddiy elektr "
            "zanjiri yoki kartondan prototip.",
        ),
        "investigative": (
            "Uyda kichik tajriba o‘tkazing",
            "experiment",
            "Sizni qiziqtirgan savolni tanlang, natijani taxmin qiling, sinab ko‘ring va nima "
            "sizni hayron qoldirganini yozib qo‘ying.",
        ),
        "artistic": (
            "Bir sahifalik vizual g‘oya yarating",
            "project",
            "Siz uchun muhim bo‘lgan narsani tushuntiradigan plakat, eskiz yoki qisqa kadrlar "
            "ketma-ketligini chizing.",
        ),
        "social": (
            "Kimgadir biror narsani o‘rgating",
            "conversation",
            "20 daqiqa davomida do‘stingiz yoki oila a’zongizga biror ko‘nikmani tushuntiring, "
            "keyin bu sizga qanday tuyulganini o‘ylab ko‘ring.",
        ),
        "enterprising": (
            "Kichik g‘oyangizni taqdim eting",
            "challenge",
            "Maktabda yoki uyda biror narsani yaxshilash uchun kichik g‘oya o‘ylab toping va uni "
            "kimgadir ikki daqiqada tushuntirib bering.",
        ),
        None: (
            "Qisqa izlanish mashqini sinab ko‘ring",
            "reflection",
            "Eng kuchli yo‘nalishingizda bitta kichik mashg‘ulotni sinab ko‘ring va nimadan zavq "
            "olayotganingizga e’tibor bering.",
        ),
    },
    "ru": {
        "realistic": (
            "Попробуй практическое задание на конструирование",
            "challenge",
            "Собери примерно за 30 минут небольшую рабочую модель: бумажный мост, простую "
            "электрическую цепь или прототип из картона.",
        ),
        "investigative": (
            "Проведи мини-эксперимент дома",
            "experiment",
            "Выбери вопрос, который тебе интересен, сделай предположение, проверь его и запиши, "
            "что тебя удивило.",
        ),
        "artistic": (
            "Создай визуальную идею на одну страницу",
            "project",
            "Нарисуй постер, эскиз или короткую раскадровку о том, что для тебя важно.",
        ),
        "social": (
            "Научи кого-нибудь чему-то новому",
            "conversation",
            "Потрать 20 минут, чтобы объяснить другу или близкому какой-нибудь навык, а потом "
            "подумай, какие были ощущения.",
        ),
        "enterprising": (
            "Представь небольшую идею",
            "challenge",
            "Придумай небольшую идею, как улучшить что-то в школе или дома, и за две минуты "
            "расскажи о ней кому-нибудь.",
        ),
        None: (
            "Попробуй короткое исследовательское задание",
            "reflection",
            "Попробуй одно небольшое занятие в своём самом сильном направлении и обрати внимание, "
            "что тебе нравится.",
        ),
    },
}

_TEXT = {
    "en": {
        "conf": {"HIGH": "consistent", "MEDIUM": "moderate", "LOW": "early"},
        "headline_two": "Early signals point toward {a} and {b}",
        "headline_one": "An early signal points toward {a}",
        "summary": "Your current evidence suggests a stronger interest in {a}",
        "summary_then": ", followed by {b}",
        "summary_tail": (
            ". These signals come from one short assessment, so they are a starting point "
            "rather than a conclusion. This profile will evolve as more evidence is collected."
        ),
        "strength": "You picked this direction {n} of {m} times — {conf} evidence so far.",
        "not_tried": "You haven't tried {label} yet — that's an open area to explore.",
        "not_enough": "There is not enough evidence yet about {label}.",
        "uncertainty": [
            "These signals reflect preferences from one assessment, not real-world experience.",
            "Interests often shift with exposure — trying things is the best way to learn more.",
        ],
        "reason": (
            "{label} is currently your strongest signal. {how} Trying this may help "
            "clarify whether this interest grows with hands-on experience."
        ),
        "validation": (
            "Whether your interest in {label} holds up in a real activity, since your "
            "current evidence comes only from assessment choices."
        ),
        "confidence_note": (
            "This is a tentative suggestion based on early signals — it is one experiment, "
            "not a verdict."
        ),
    },
    "uz": {
        "conf": {"HIGH": "barqaror", "MEDIUM": "o‘rtacha", "LOW": "dastlabki"},
        "headline_two": "Dastlabki belgilar «{a}» va «{b}» yo‘nalishlariga ishora qilmoqda",
        "headline_one": "Dastlabki belgi «{a}» yo‘nalishiga ishora qilmoqda",
        "summary": "Hozirgi ma’lumotlarga ko‘ra, sizni ko‘proq «{a}» yo‘nalishi qiziqtiradi",
        "summary_then": ", undan keyin — «{b}»",
        "summary_tail": (
            ". Bu belgilar bitta qisqa testdan olingan, shuning uchun ular xulosa emas, balki "
            "boshlanish nuqtasi. Yangi ma’lumotlar to‘plangan sari profilingiz o‘zgarib boradi."
        ),
        "strength": "Siz bu yo‘nalishni {m} imkoniyatdan {n} marta tanladingiz — hozircha bu {conf} belgi.",
        "not_tried": "«{label}» hali sinab ko‘rilmagan — bu o‘rganish uchun ochiq soha.",
        "not_enough": "«{label}» haqida hali yetarli ma’lumot yo‘q.",
        "uncertainty": [
            "Bu belgilar hayotiy tajribani emas, bitta testdagi tanlovlaringizni aks ettiradi.",
            "Qiziqishlar yangi narsalarni sinab ko‘rgan sari o‘zgarishi mumkin — ko‘proq bilishning eng yaxshi yo‘li sinab ko‘rish.",
        ],
        "reason": (
            "Hozircha eng kuchli belgingiz — «{label}». {how} Bu qiziqish amaliy tajribada ham "
            "kuchayadimi, shuni aniqlashga yordam berishi mumkin."
        ),
        "validation": (
            "«{label}» yo‘nalishiga qiziqishingiz haqiqiy mashg‘ulotda ham saqlanadimi — chunki "
            "hozirgi ma’lumotlar faqat testdagi tanlovlardan olingan."
        ),
        "confidence_note": (
            "Bu dastlabki belgilarga asoslangan taxminiy tavsiya — bor-yo‘g‘i bitta tajriba, "
            "yakuniy xulosa emas."
        ),
    },
    "ru": {
        "conf": {"HIGH": "устойчивый", "MEDIUM": "умеренный", "LOW": "ранний"},
        "headline_two": "Первые сигналы указывают на направления «{a}» и «{b}»",
        "headline_one": "Первый сигнал указывает на направление «{a}»",
        "summary": "Судя по текущим данным, тебя больше всего привлекает направление «{a}»",
        "summary_then": ", а затем — «{b}»",
        "summary_tail": (
            ". Эти сигналы получены по итогам одного короткого теста, поэтому это отправная "
            "точка, а не вывод. Профиль будет меняться по мере появления новых данных."
        ),
        "strength": "Это направление выбрано в {n} из {m} случаев — пока это {conf} сигнал.",
        "not_tried": "«{label}» — пока не опробовано. Это открытая область для исследования.",
        "not_enough": "По направлению «{label}» пока недостаточно данных.",
        "uncertainty": [
            "Эти сигналы отражают предпочтения по одному тесту, а не реальный опыт.",
            "Интересы часто меняются, когда пробуешь новое, — пробовать и есть лучший способ узнать больше.",
        ],
        "reason": (
            "Сейчас самый сильный сигнал — «{label}». {how} Это поможет понять, растёт ли "
            "интерес, когда пробуешь на практике."
        ),
        "validation": (
            "Сохранится ли интерес к направлению «{label}» в реальном деле — ведь пока данные "
            "есть только по ответам в тесте."
        ),
        "confidence_note": (
            "Это осторожное предложение на основе первых сигналов — один эксперимент, а не приговор."
        ),
    },
}


def _exploration(key: str, language: str):
    table = _EXPLORATIONS.get(language, _EXPLORATIONS["en"])
    return table.get(key, table[None])


def build_fallback(signal_input: dict, language: str = "en") -> dict:
    t = _TEXT.get(language, _TEXT["en"])
    signals = signal_input["signals"]
    with_evidence = [s for s in signals if s["evidence_count"] > 0]
    top = with_evidence[:3] or signals[:1]
    gaps = [s for s in signals if s["evidence_count"] == 0 or s["confidence"] == "LOW"]
    lead = top[0]
    conf = t["conf"]

    if len(top) > 1:
        headline = t["headline_two"].format(a=top[0]["label"], b=top[1]["label"])
    else:
        headline = t["headline_one"].format(a=lead["label"])

    title, activity_type, how = _exploration(lead["key"], language)

    profile = {
        "headline": headline,
        "summary": (
            t["summary"].format(a=lead["label"])
            + (t["summary_then"].format(b=top[1]["label"]) if len(top) > 1 else "")
            + t["summary_tail"]
        ),
        "emerging_strengths": [
            {
                "title": s["label"],
                "reason": t["strength"].format(n=s["evidence_count"], m=s["chances"], conf=conf[s["confidence"]]),
            }
            for s in top
        ],
        "exposure_gaps": (
            [t["not_tried"].format(label=label.lower() if language == "en" else label) for label in signal_input.get("exposure_not_tried", [])[:2]]
            + [t["not_enough"].format(label=s["label"]) for s in gaps[:2]]
        )[:4],
        "uncertainty_notes": list(t["uncertainty"]),
        "suggested_explorations": [_exploration(s["key"], language)[0] for s in top[:3]],
    }
    next_step = {
        "title": title,
        "activity_type": activity_type,
        "reason": t["reason"].format(label=lead["label"], how=how),
        "signals_used": [lead["key"]],
        "intended_validation": t["validation"].format(label=lead["label"]),
        "confidence_note": t["confidence_note"],
    }
    return {"profile": profile, "next_step": next_step}


# --- Orchestration ----------------------------------------------------------

def _generate(signal_input: dict, language: str = "en") -> Generated:
    known = {s["key"] for s in signal_input["signals"]} | {s["key"] for s in signal_input.get("other_signals", [])}
    return run_structured(
        provider=get_provider(),
        system=with_language(PROFILE_SYNTHESIS_SYSTEM, language),
        payload=signal_input,
        schema=PROFILE_SYNTHESIS_JSON_SCHEMA,
        validate=lambda raw: validate_ai_output(raw, known),
        fallback=lambda: build_fallback(signal_input, language),
        feature=f"profile_synthesis lang={language}",
    )


def get_or_create_profile_insight(session: AssessmentSession, language: str = "en") -> AIInsight:
    """Idempotent get-or-generate per language (locked; FALLBACK rows retry after a cooldown)."""
    return get_or_generate(
        session=session,
        generation_type=GenerationType.PROFILE_SYNTHESIS,
        input_version=INPUT_VERSION,
        produce=lambda: _generate(build_signal_input(session, language), language),
        retry_after=FALLBACK_RETRY_AFTER,
        language=language,
    )


def get_saved_profile_insight(session: AssessmentSession, language: str = "en") -> AIInsight | None:
    """Read-only: the persisted insight for this session in `language`, if any. Never calls a provider."""
    return saved_insight(session, GenerationType.PROFILE_SYNTHESIS, INPUT_VERSION, language)
