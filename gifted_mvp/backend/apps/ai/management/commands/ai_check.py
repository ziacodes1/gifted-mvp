"""Verify the configured AI provider with one tiny structured request.

Prints only provider, model, candidate models (Gemini) and outcome/latency —
never keys, headers or prompt content. Uses the same provider class the app uses.
"""
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.ai.services.provider import GeminiProvider, ProviderError, get_provider

PROBE_SCHEMA = {
    "type": "object",
    "properties": {"status": {"type": "string"}},
    "required": ["status"],
    "additionalProperties": False,
}


class Command(BaseCommand):
    help = "Probe the configured AI provider (AI_PROVIDER) with one tiny structured request."

    def handle(self, *args, **options):
        provider = get_provider()
        self.stdout.write(f"AI_PROVIDER={settings.AI_PROVIDER} -> active provider: {provider.name}")
        if provider.name == "stub":
            self.stdout.write("No live provider configured (missing key or AI_PROVIDER=stub). The app will use the signal-based fallback.")
            return
        if isinstance(provider, GeminiProvider):
            try:
                ranked = provider.rank_models(provider.available_models())
                self.stdout.write(f"Flash models available to this key (best first): {', '.join(ranked[:6]) or 'none'}")
            except Exception as exc:  # noqa: BLE001 — report category only
                self.stdout.write(f"Could not list models: {type(exc).__name__}")
        started = time.monotonic()
        try:
            data = provider.generate_structured(
                system="Reply with JSON only.", prompt='Return {"status": "ok"}.', schema=PROBE_SCHEMA, max_tokens=200
            )
            ms = (time.monotonic() - started) * 1000
            ok = data.get("status") == "ok"
            self.stdout.write(self.style.SUCCESS(f"model={provider.model} outcome={'ai' if ok else 'unexpected_json'} latency_ms={ms:.0f}"))
            if not settings.AI_MODEL.startswith("gemini") and provider.name == "gemini":
                self.stdout.write(f"Tip: pin it with AI_MODEL={provider.model}")
        except ProviderError as exc:
            ms = (time.monotonic() - started) * 1000
            self.stdout.write(self.style.WARNING(f"model={provider.model or '-'} outcome=fallback reason={exc} latency_ms={ms:.0f}"))
