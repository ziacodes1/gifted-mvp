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
from typing import Callable

from django.db import transaction
from django.utils import timezone

from apps.assessments.models import AssessmentSession

from ..models import AIInsight, InsightSource
from .provider import LLMProvider, ProviderError, ProviderUnavailable

logger = logging.getLogger("apps.ai")

FALLBACK_RETRY_AFTER = timedelta(minutes=10)

Generated = tuple[dict, str, str, str]  # (result, source, provider_name, model)


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

    def log(outcome: str, level=logging.INFO, reason: str = "") -> None:
        logger.log(
            level,
            "ai feature=%s provider=%s model=%s outcome=%s latency_ms=%d%s",
            feature,
            provider.name,
            provider.model or "-",
            outcome,
            (time.monotonic() - started) * 1000,
            f" reason={reason}" if reason else "",
        )

    try:
        raw = provider.generate_structured(
            system=system,
            prompt=json.dumps(payload, separators=(",", ":"), default=str),
            schema=schema,
            max_tokens=max_tokens,
        )
        result = validate(raw)
        log("ai")
        return result, InsightSource.AI, provider.name, provider.model
    except ProviderUnavailable:
        log("fallback", reason="not_configured")
    except ProviderError as exc:
        log("fallback", logging.WARNING, reason=str(exc))
    except ValueError as exc:
        log("fallback", logging.WARNING, reason=f"rejected:{str(exc).split(':')[0]}")
    except Exception as exc:  # never let a page break on AI
        log("fallback", logging.ERROR, reason=type(exc).__name__)
    return fallback(), InsightSource.FALLBACK, "", ""


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
) -> AIInsight:
    retry_after = FALLBACK_RETRY_AFTER if retry_after is None else retry_after
    with transaction.atomic():
        AssessmentSession.objects.select_for_update().only("id").get(pk=session.pk)
        existing = saved_insight(session, generation_type, input_version, language)
        if existing and (
            existing.source == InsightSource.AI or timezone.now() - existing.updated_at < retry_after
        ):
            return existing

        result, source, provider_name, model = produce()

        if existing:
            if source == InsightSource.FALLBACK:
                existing.save(update_fields=["updated_at"])  # restart cooldown
                return existing
            existing.source, existing.provider, existing.model = source, provider_name, model
            existing.result = result
            existing.save()
            return existing

        return AIInsight.objects.create(
            learner_id=session.learner_id,
            session=session,
            generation_type=generation_type,
            input_version=input_version,
            language=language,
            source=source,
            provider=provider_name,
            model=model,
            result=result,
        )
