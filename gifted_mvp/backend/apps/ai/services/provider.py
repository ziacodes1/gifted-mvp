"""Provider-agnostic LLM boundary.

Product code only ever calls `get_provider().generate_structured(...)` and
handles `ProviderError`. Concrete providers live here; selection is driven by
settings (`AI_PROVIDER` = stub | anthropic | gemini | groq, optional
`AI_SECONDARY_PROVIDER`, `AI_MODEL`, and `AI_API_KEY` / `GEMINI_API_KEY` / `GROQ_API_KEY`).
Keys never leave the backend and are never logged.
"""
from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod

from django.conf import settings

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    """Any provider failure. Message is safe to log, never shown to users."""


class ProviderUnavailable(ProviderError):
    """Provider not configured (e.g. stub / missing key)."""


class LLMProvider(ABC):
    name: str = "unknown"
    model: str = ""

    @abstractmethod
    def generate_structured(
        self, *, system: str, prompt: str, schema: dict, max_tokens: int = 2000
    ) -> dict:
        """Return a JSON object shaped by `schema`. Raise ProviderError on failure.
        Callers still validate the result — providers are not trusted."""


class StubProvider(LLMProvider):
    """No live model configured: always defers to the deterministic fallback."""

    name = "stub"

    def generate_structured(self, **kwargs) -> dict:
        raise ProviderUnavailable("AI provider not configured")


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    DEFAULT_MODEL = "claude-opus-5"

    def __init__(self, *, api_key: str, model: str, timeout: float, effort: str):
        import anthropic  # local import: only needed when this provider is selected

        self._anthropic = anthropic
        self._client = anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=1)
        self.model = model or self.DEFAULT_MODEL
        self._effort = effort

    def generate_structured(
        self, *, system: str, prompt: str, schema: dict, max_tokens: int = 2000
    ) -> dict:
        a = self._anthropic
        try:
            response = self._client.beta.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
                output_config={
                    "effort": self._effort,
                    "format": {"type": "json_schema", "schema": schema},
                },
                # Server-side refusal fallback: routes a declined request to a
                # suitable model inside the same call.
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except a.APITimeoutError as exc:
            raise ProviderError("timeout") from exc
        except a.RateLimitError as exc:
            raise ProviderError("rate_limited") from exc
        except a.AuthenticationError as exc:
            raise ProviderError("auth_failed") from exc
        except a.APIStatusError as exc:
            raise ProviderError(_safe_status_reason(exc)) from exc
        except a.APIConnectionError as exc:
            raise ProviderError("connection_error") from exc

        if response.stop_reason in ("refusal", "max_tokens"):
            raise ProviderError(f"stop_reason_{response.stop_reason}")
        text = next((b.text for b in response.content if b.type == "text"), None)
        if not text:
            raise ProviderError("empty_response")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderError("invalid_json") from exc
        if not isinstance(data, dict):
            raise ProviderError("non_object_json")
        return data


def _strip_additional_properties(schema):
    """Gemini's JSON-schema subset doesn't need `additionalProperties`; extra keys are
    still rejected afterwards by Gifted's own pydantic validation (extra=forbid)."""
    if isinstance(schema, dict):
        return {k: _strip_additional_properties(v) for k, v in schema.items() if k != "additionalProperties"}
    if isinstance(schema, list):
        return [_strip_additional_properties(v) for v in schema]
    return schema


class GeminiProvider(LLMProvider):
    """Google Gemini via the official `google-genai` SDK, JSON-schema structured output.

    Model: `AI_MODEL` when it names a Gemini model; otherwise the newest stable Flash
    model this key can use (resolved once from the key's own model list, then cached)."""

    name = "gemini"
    _resolved: dict[str, str] = {}  # per-process cache: key fingerprint -> model

    def __init__(self, *, api_key: str, model: str, timeout: float):
        from google import genai
        from google.genai import types

        self._types = types
        self._client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=int(timeout * 1000)))
        self._cache_key = str(hash(api_key))
        configured = (model or "").strip()
        if configured and not configured.startswith("gemini"):
            logger.warning("AI_MODEL=%s is not a Gemini model; auto-selecting a Flash model", configured)
            configured = ""
        self.model = configured or self._resolved.get(self._cache_key, "")

    # --- model selection -------------------------------------------------------
    @staticmethod
    def rank_models(names: list[str]) -> list[str]:
        """Stable Flash models first (newest version first, full Flash before Flash-Lite),
        then previews. Excludes non-text variants (image, tts, live, audio, embedding)."""
        ranked = []
        for full in names:
            name = full.split("/")[-1]
            m = re.fullmatch(r"gemini-(\d+(?:\.\d+)?)-flash(-lite)?(-preview(?:-[\w-]+)?|-\d{3})?", name)
            if not m or re.search(r"image|tts|live|audio|embedding|thinking|exp", name):
                continue
            version, lite, suffix = float(m.group(1)), bool(m.group(2)), m.group(3) or ""
            preview = suffix.startswith("-preview")
            ranked.append(((preview, -version, lite, bool(suffix)), name))
        return [name for _, name in sorted(ranked)]

    def available_models(self) -> list[str]:
        return [
            m.name
            for m in self._client.models.list()
            if not m.supported_actions or "generateContent" in m.supported_actions
        ]

    def _ensure_model(self) -> str:
        if self.model:
            return self.model
        ranked = self.rank_models(self.available_models())
        if not ranked:
            raise ProviderError("model_not_found:no_flash_model")
        self.model = self._resolved[self._cache_key] = ranked[0]
        return self.model

    # --- generation ------------------------------------------------------------
    def generate_structured(self, *, system: str, prompt: str, schema: dict, max_tokens: int = 2000) -> dict:
        from google.genai import errors
        import httpx

        t = self._types
        try:
            model = self._ensure_model()
            response = self._client.models.generate_content(
                model=model,
                contents=prompt,
                config=t.GenerateContentConfig(
                    system_instruction=system,
                    response_mime_type="application/json",
                    response_json_schema=_strip_additional_properties(schema),
                    # Headroom: newer Flash models may spend output tokens on thinking.
                    max_output_tokens=max(max_tokens * 2, 4096),
                    temperature=0.4,
                ),
            )
        except errors.APIError as exc:
            raise ProviderError(_gemini_reason(exc)) from exc
        except httpx.TimeoutException as exc:
            raise ProviderError("timeout") from exc
        except httpx.HTTPError as exc:
            raise ProviderError("connection_error") from exc

        candidate = (response.candidates or [None])[0]
        finish = str(getattr(candidate, "finish_reason", "") or "").split(".")[-1].upper()
        if finish and finish not in ("STOP", "FINISH_REASON_UNSPECIFIED"):
            raise ProviderError(f"finish_reason_{finish.lower()}")
        text = response.text
        if not text:
            raise ProviderError("empty_response")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderError("invalid_json") from exc
        if not isinstance(data, dict):
            raise ProviderError("non_object_json")
        return data


def _gemini_reason(exc) -> str:
    """Safe category from a google-genai APIError (code + status only; no message text,
    which could echo request content)."""
    code, status = getattr(exc, "code", None), str(getattr(exc, "status", "") or "").upper()
    message = str(getattr(exc, "message", "") or "").lower()
    if code == 429 or status == "RESOURCE_EXHAUSTED":
        return "quota_exceeded"
    if code in (401, 403) or status in ("UNAUTHENTICATED", "PERMISSION_DENIED") or "api key" in message:
        return "auth_failed"
    if code == 404 or status == "NOT_FOUND":
        return "model_not_found"
    if code and code >= 500:
        return f"server_error_{code}"
    category = "schema_issue" if "schema" in message else "other"
    return f"api_status_{code}:{status or 'unknown'}:{category}"


class GroqProvider(LLMProvider):
    """Groq (official `groq` SDK), strict JSON-schema Structured Outputs.

    Gifted's schemas mark every property required and set additionalProperties=false
    at every level, which is what Groq's strict mode requires. Output is still
    validated afterwards by Gifted's own pydantic + banned-phrase checks."""

    name = "groq"
    DEFAULT_MODEL = "openai/gpt-oss-20b"

    def __init__(self, *, api_key: str, model: str, timeout: float, effort: str):
        from groq import Groq

        self._client = Groq(api_key=api_key, timeout=timeout, max_retries=1)
        configured = (model or "").strip()
        if configured.startswith(("claude", "gemini")):
            configured = ""  # a model name for another provider is ignored
        self.model = configured or self.DEFAULT_MODEL
        self._effort = effort if effort in ("low", "medium", "high") else "medium"

    MAX_ATTEMPTS = 2  # one retry, only for malformed output (measured ~1 in 3 on gpt-oss-20b)

    def generate_structured(self, *, system: str, prompt: str, schema: dict, max_tokens: int = 2000) -> dict:
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                return self._generate_once(system=system, prompt=prompt, schema=schema, max_tokens=max_tokens)
            except ProviderError as exc:
                if not str(exc).startswith("invalid_output") or attempt == self.MAX_ATTEMPTS:
                    raise
                logger.info("ai provider=groq retry reason=%s", exc)
        raise ProviderError("invalid_output")  # unreachable; keeps type checkers happy

    def _generate_once(self, *, system: str, prompt: str, schema: dict, max_tokens: int) -> dict:
        import groq as g

        extra = {}
        if self.model.startswith("openai/gpt-oss"):
            # Short synthesis: keep reasoning light and out of the response.
            extra = {"reasoning_effort": self._effort, "include_reasoning": False}
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "gifted_output", "strict": True, "schema": schema},
                },
                max_completion_tokens=max(max_tokens, 2000),
                temperature=0.4,
                **extra,
            )
        except g.APITimeoutError as exc:
            raise ProviderError("timeout") from exc
        except (g.AuthenticationError, g.PermissionDeniedError) as exc:
            raise ProviderError("auth_failed") from exc
        except g.RateLimitError as exc:
            raise ProviderError("rate_limited") from exc
        except g.APIStatusError as exc:
            raise ProviderError(_groq_status_reason(exc)) from exc
        except g.APIConnectionError as exc:
            raise ProviderError("connection_error") from exc

        choice = response.choices[0] if response.choices else None
        if choice is None or choice.finish_reason not in ("stop", None):
            raise ProviderError(f"invalid_output:finish_{getattr(choice, 'finish_reason', 'none')}")
        text = choice.message.content
        if not text:
            raise ProviderError("invalid_output:empty")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderError("invalid_output:json") from exc
        if not isinstance(data, dict):
            raise ProviderError("invalid_output:not_object")
        return data


def _groq_status_reason(exc) -> str:
    """Safe category from a Groq APIStatusError (status + error code only)."""
    status = getattr(exc, "status_code", 0) or 0
    body = exc.body if isinstance(getattr(exc, "body", None), dict) else {}
    err = body.get("error", body) if isinstance(body.get("error", body), dict) else {}
    code = str(err.get("code", "") or err.get("type", "") or "unknown")
    if status >= 500:
        return "server_error"
    if status == 404:
        return "model_not_found"
    if status == 400 and ("json" in code or "schema" in code or "validate" in code):
        return "invalid_output"  # model output failed Groq's schema validation
    return f"api_status_{status}:{code}"


TRANSIENT_REASONS = ("rate_limited", "timeout", "server_error", "connection_error", "quota_exceeded")


class FailoverProvider(LLMProvider):
    """Primary → secondary on *transient* failures only (rate limit, timeout, 5xx,
    connection). Anything else (bad key, invalid output) goes straight to Gifted's
    deterministic fallback. `name`/`model` report whichever provider actually answered."""

    def __init__(self, primary: LLMProvider, secondary: LLMProvider):
        self.primary, self.secondary = primary, secondary
        self.name, self.model = primary.name, primary.model

    def generate_structured(self, **kwargs) -> dict:
        try:
            result = self.primary.generate_structured(**kwargs)
            self.name, self.model = self.primary.name, self.primary.model
            return result
        except ProviderError as exc:
            if not str(exc).startswith(TRANSIENT_REASONS):
                raise
            logger.warning("ai failover from=%s reason=%s to=%s", self.primary.name, exc, self.secondary.name)
            self.name, self.model = self.secondary.name, self.secondary.model
            return self.secondary.generate_structured(**kwargs)


def _safe_status_reason(exc) -> str:
    """Short, loggable reason from an API error: status + error type + a category.
    Never includes keys, headers or prompt content."""
    body = exc.body if isinstance(getattr(exc, "body", None), dict) else {}
    err = body.get("error", {}) if isinstance(body.get("error"), dict) else {}
    message = str(err.get("message", "")).lower()
    category = next(
        (
            label
            for needle, label in (
                ("credit balance", "billing_credit_low"),
                ("model", "model_issue"),
                ("output_config", "output_config_issue"),
                ("schema", "schema_issue"),
                ("effort", "effort_issue"),
                ("fallback", "fallback_param_issue"),
            )
            if needle in message
        ),
        "other",
    )
    return f"api_status_{exc.status_code}:{err.get('type', 'unknown')}:{category}"


def _build_provider(provider: str) -> LLMProvider | None:
    """Construct one provider by name, or None when it isn't configured (missing key)."""
    provider = (provider or "").lower()
    if provider == "anthropic":
        if not settings.AI_API_KEY:
            return None
        return AnthropicProvider(
            api_key=settings.AI_API_KEY,
            model=settings.AI_MODEL if settings.AI_MODEL.startswith("claude") else "",
            timeout=settings.AI_TIMEOUT_SECONDS,
            effort=settings.AI_EFFORT,
        )
    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            return None
        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.AI_MODEL, timeout=settings.AI_TIMEOUT_SECONDS)
    if provider == "groq":
        if not settings.GROQ_API_KEY:
            return None
        return GroqProvider(
            api_key=settings.GROQ_API_KEY,
            model=settings.AI_MODEL,
            timeout=settings.AI_TIMEOUT_SECONDS,
            effort=settings.GROQ_REASONING_EFFORT,
        )
    return None


def get_provider() -> LLMProvider:
    name = (settings.AI_PROVIDER or "stub").lower()
    primary = _build_provider(name)
    if primary is None:
        if name != "stub":
            logger.warning("AI_PROVIDER=%s but its API key is empty; using stub", name)
        return StubProvider()
    secondary_name = (settings.AI_SECONDARY_PROVIDER or "").lower()
    if secondary_name and secondary_name != name:
        # A model name set for the primary is ignored by the other providers' constructors.
        secondary = _build_provider(secondary_name)
        if secondary is not None:
            return FailoverProvider(primary, secondary)
    return primary
