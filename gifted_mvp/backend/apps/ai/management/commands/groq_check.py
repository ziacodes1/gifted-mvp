"""Check the Groq provider with one tiny strict structured-output request.

Prints provider, model, auth result, outcome and latency only — never the key or prompt.
"""
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.ai.services.provider import GroqProvider, ProviderError, get_provider

PROBE_SCHEMA = {
    "type": "object",
    "properties": {"status": {"type": "string"}},
    "required": ["status"],
    "additionalProperties": False,
}


class Command(BaseCommand):
    help = "Probe Groq (GROQ_API_KEY / AI_MODEL) with one tiny structured request."

    def handle(self, *args, **options):
        self.stdout.write(f"active_provider={get_provider().name}")
        if not settings.GROQ_API_KEY:
            self.stdout.write("provider=groq outcome=not_configured (GROQ_API_KEY is empty)")
            return
        provider = GroqProvider(
            api_key=settings.GROQ_API_KEY,
            model=settings.AI_MODEL,
            timeout=settings.AI_TIMEOUT_SECONDS,
            effort=settings.GROQ_REASONING_EFFORT,
        )
        self.stdout.write(f"provider=groq\nmodel={provider.model}\nreasoning_effort={settings.GROQ_REASONING_EFFORT}")
        started = time.monotonic()
        try:
            data = provider.generate_structured(
                system="Reply with JSON only.", prompt='Return {"status": "ok"}.', schema=PROBE_SCHEMA, max_tokens=200
            )
            outcome, auth = ("ai" if data.get("status") == "ok" else "unexpected_json"), "ok"
        except ProviderError as exc:
            outcome, auth = f"fallback reason={exc}", ("failed" if str(exc) == "auth_failed" else "ok")
        ms = (time.monotonic() - started) * 1000
        self.stdout.write(f"auth={auth}\noutcome={outcome}\nlatency_ms={ms:.0f}")
