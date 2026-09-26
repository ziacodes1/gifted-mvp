"""Request language + localized reads of server-driven content.

- The frontend sends `Accept-Language: en|uz|ru` on every request; `LanguageMiddleware`
  normalizes it to one of `SUPPORTED` (unknown/missing → English) and activates it.
- Canonical content stays in the model's English columns. Uzbek/Russian live in a
  `translations` JSON field: {"uz": {"title": "...", "content": {...}}, "ru": {...}}.
- Internal keys (signal keys, option values, step keys, statuses) are never translated.
Language changes presentation only — never scores, mappings, evidence or progress.
"""
from __future__ import annotations

from django.utils import translation

SUPPORTED = ("en", "uz", "ru")
DEFAULT = "en"


def normalize_language(value: str | None) -> str:
    """First supported language in an Accept-Language-style value, else English."""
    for part in (value or "").split(","):
        code = part.split(";")[0].strip().lower().replace("_", "-").split("-")[0]
        if code in SUPPORTED:
            return code
    return DEFAULT


def current_language() -> str:
    return normalize_language(translation.get_language())


class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = normalize_language(request.META.get("HTTP_ACCEPT_LANGUAGE"))
        request.LANGUAGE_CODE = lang
        with translation.override(lang):
            response = self.get_response(request)
        response.headers.setdefault("Content-Language", lang)
        return response


def _merge(base, over):
    """Overlay translated values onto canonical content. Dicts merge recursively; lists
    of dicts merge by `key` when every base item has one, otherwise by position; any
    other translated value replaces the canonical one."""
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for k, v in over.items():
            out[k] = _merge(base.get(k), v) if k in base else v
        return out
    if isinstance(base, list) and isinstance(over, list) and over and all(isinstance(i, dict) for i in over):
        if all(isinstance(i, dict) and "key" in i for i in base):
            by_key = {i.get("key"): i for i in over}
            return [_merge(i, by_key[i["key"]]) if i["key"] in by_key else i for i in base]
        return [_merge(b, over[i]) if i < len(over) else b for i, b in enumerate(base)]
    return base if over in (None, "", [], {}) else over


def tr(obj, field: str, lang: str | None = None):
    """Localized value of `obj.<field>` (falls back to the canonical English value)."""
    base = getattr(obj, field)
    lang = lang or current_language()
    if lang == DEFAULT:
        return base
    over = (getattr(obj, "translations", None) or {}).get(lang, {}).get(field)
    if over is None:
        return base
    return _merge(base, over) if isinstance(base, (dict, list)) else over


# Small fixed vocabularies the backend returns as display text.
LABELS: dict[str, dict[str, dict[str, str]]] = {
    "journey": {
        "en": {"discover": "Discover", "explore": "Explore", "validate": "Validate", "develop": "Develop", "guide": "Guide"},
        "uz": {"discover": "Kashf qilish", "explore": "Izlanish", "validate": "Tasdiqlash", "develop": "Rivojlanish", "guide": "Yo‘nalish"},
        "ru": {"discover": "Открытие", "explore": "Исследование", "validate": "Проверка", "develop": "Развитие", "guide": "Направление"},
    },
    "evidence_kind": {
        "en": {"INTEREST": "Interest", "EXPOSURE": "Exposure", "ENGAGEMENT": "Engagement", "DECISION": "Decision-making", "REASONING": "Reasoning", "REFLECTION": "Reflection"},
        "uz": {"INTEREST": "Qiziqish", "EXPOSURE": "Tajriba", "ENGAGEMENT": "Faollik", "DECISION": "Qaror qabul qilish", "REASONING": "Mulohaza", "REFLECTION": "Fikr yuritish"},
        "ru": {"INTEREST": "Интерес", "EXPOSURE": "Опыт", "ENGAGEMENT": "Вовлечённость", "DECISION": "Принятие решений", "REASONING": "Рассуждение", "REFLECTION": "Рефлексия"},
    },
    "evidence_source": {
        "en": {"ASSESSMENT": "Assessment", "MISSION": "Mission", "VIRTUAL_LAB": "Virtual lab", "OPPORTUNITY": "Opportunity", "REAL_WORLD": "Real-world experience"},
        "uz": {"ASSESSMENT": "Test", "MISSION": "Missiya", "VIRTUAL_LAB": "Virtual laboratoriya", "OPPORTUNITY": "Imkoniyat", "REAL_WORLD": "Hayotiy tajriba"},
        "ru": {"ASSESSMENT": "Тест", "MISSION": "Миссия", "VIRTUAL_LAB": "Виртуальная лаборатория", "OPPORTUNITY": "Возможность", "REAL_WORLD": "Реальный опыт"},
    },
    "text": {
        "en": {
            "evolving": "Your Gifted Passport grows with you. Assessments are only the beginning — future missions and real experiences will add new evidence.",
            "privacy": "Gifted shares growth signals with parents, not every private response.",
            "exposure_note": "These are early signals from your first assessment. Real-world exploration will help confirm and refine them.",
            "mission_fallback": "Mission",
        },
        "uz": {
            "evolving": "Gifted pasportingiz siz bilan birga o‘sadi. Test — faqat boshlanish: keyingi missiyalar va hayotiy tajribalar yangi dalillar qo‘shadi.",
            "privacy": "Gifted ota-onalarga har bir shaxsiy javobni emas, faqat rivojlanish belgilarini ko‘rsatadi.",
            "exposure_note": "Bu birinchi testingizdan olingan dastlabki belgilar. Hayotda sinab ko‘rish ularni aniqlashtirishga yordam beradi.",
            "mission_fallback": "Missiya",
        },
        "ru": {
            "evolving": "Твой паспорт Gifted растёт вместе с тобой. Тест — это только начало: новые миссии и реальный опыт добавят новые данные.",
            "privacy": "Gifted показывает родителям сигналы развития, а не каждый личный ответ.",
            "exposure_note": "Это первые сигналы по итогам твоего первого теста. Реальные пробы помогут их уточнить.",
            "mission_fallback": "Миссия",
        },
    },
}


def label(group: str, key: str, lang: str | None = None) -> str:
    lang = lang or current_language()
    return LABELS[group].get(lang, LABELS[group][DEFAULT]).get(key) or LABELS[group][DEFAULT].get(key, key)
