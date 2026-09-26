"""Shared orchestration for persisted, structured AI generations.

Every AI feature (profile synthesis, parent insight, ...) follows the same rules:
- compact trusted JSON in, schema-validated JSON out (validator raises ValueError);
- any provider/validation failure → deterministic fallback, never a user-facing error;
- one persisted `AIInsight` per (session, generation_type, input_version, language),
  created under a row lock so concurrent requests can't trigger duplicate paid calls;
  an insight in one language is never served for another;
- AI rows are final; FALLBACK rows retry the provider after a cooldown.
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import timedelta
from typing import Callable, NamedTuple

from django.db import transaction
from django.utils import timezone

from apps.assessments.models import AssessmentSession

from ..models import AIInsight, InsightSource
from .provider import LLMProvider, ProviderError, ProviderUnavailable

logger = logging.getLogger("apps.ai")

FALLBACK_RETRY_AFTER = timedelta(minutes=10)

class Generated(NamedTuple):
    """One generation attempt. `reason` is a safe failure category (never provider text)."""

    result: dict
    source: str
    provider: str
    model: str
    latency_ms: int = 0
    reason: str = ""


def iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from iter_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from iter_strings(v)


def check_language(data: dict, forbidden: re.Pattern) -> None:
    for text in iter_strings(data):
        if forbidden.search(text):
            raise ValueError("language: deterministic claim")


def run_structured(
    *,
    provider: LLMProvider,
    system: str,
    payload: dict,
    schema: dict,
    validate: Callable[[dict], dict],
    fallback: Callable[[], dict],
    max_tokens: int = 2000,
    feature: str = "generation",
) -> Generated:
    """Logs only feature, provider, model, outcome and latency — never keys, prompts
    or learner text."""
    started = time.monotonic()

    def elapsed() -> int:
        return int((time.monotonic() - started) * 1000)

    def log(outcome: str, level=logging.INFO, reason: str = "") -> None:
        logger.log(
            level,
            "ai feature=%s provider=%s model=%s outcome=%s latency_ms=%d%s",
            feature,
            provider.name,
            provider.model or "-",
            outcome,
            elapsed(),
            f" reason={reason}" if reason else "",
        )

    reason, level = "", logging.INFO
    try:
        raw = provider.generate_structured(
            system=system,
            # Real UTF-8, not \uXXXX escapes: models misread escaped Cyrillic/Uzbek text.
            prompt=json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False),
            schema=schema,
            max_tokens=max_tokens,
        )
        result = validate(raw)
        log("ai")
        return Generated(result, InsightSource.AI, provider.name, provider.model, elapsed())
    except ProviderUnavailable:
        reason = "not_configured"
    except ProviderError as exc:
        reason, level = str(exc), logging.WARNING
    except ValueError as exc:
        reason, level = f"rejected:{str(exc).split(':')[0]}", logging.WARNING
    except Exception as exc:  # never let a page break on AI
        reason, level = type(exc).__name__, logging.ERROR
    log("fallback", level, reason=reason)
    return Generated(fallback(), InsightSource.FALLBACK, "", "", elapsed(), reason[:60])


def saved_insight(
    session: AssessmentSession, generation_type: str, input_version: str, language: str = "en"
) -> AIInsight | None:
    """Read-only lookup. Never calls a provider."""
    return AIInsight.objects.filter(
        session=session, generation_type=generation_type, input_version=input_version, language=language
    ).first()


def get_or_generate(
    *,
    session: AssessmentSession,
    generation_type: str,
    input_version: str,
    produce: Callable[[], Generated],
    retry_after: timedelta | None = None,
    language: str = "en",
    prompt_version: str = "",
    schema_version: str = "",
) -> AIInsight:
    retry_after = FALLBACK_RETRY_AFTER if retry_after is None else retry_after
    with transaction.atomic():
        AssessmentSession.objects.select_for_update().only("id").get(pk=session.pk)
        existing = saved_insight(session, generation_type, input_version, language)
        if existing and (
            existing.source == InsightSource.AI or timezone.now() - existing.updated_at < retry_after
        ):
            return existing

        gen = produce()
        trace = {
            "prompt_version": prompt_version,
            "schema_version": schema_version,
            "latency_ms": gen.latency_ms,
            "failure_reason": gen.reason,
        }

        if existing:
            if gen.source == InsightSource.FALLBACK:
                existing.failure_reason, existing.latency_ms = gen.reason, gen.latency_ms
                existing.save(update_fields=["updated_at", "failure_reason", "latency_ms"])  # restart cooldown
                return existing
            existing.source, existing.provider, existing.model = gen.source, gen.provider, gen.model
            existing.result = gen.result
            for k, v in trace.items():
                setattr(existing, k, v)
            existing.save()
            return existing

        return AIInsight.objects.create(
            learner_id=session.learner_id,
            session=session,
            generation_type=generation_type,
            input_version=input_version,
            language=language,
            source=gen.source,
            provider=gen.provider,
            model=gen.model,
            result=gen.result,
            **trace,
        )
