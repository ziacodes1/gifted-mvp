"""Production hardening. Development keeps convenient defaults; DJANGO_ENV=production
fails closed: the process refuses to start with an insecure configuration instead of
silently running with development behaviour.
"""
from __future__ import annotations

import os

from django.core.exceptions import ImproperlyConfigured

MIN_SECRET_LENGTH = 50


def _bool(key: str, default: bool) -> bool:
    return os.environ.get(key, str(default)).lower() in ("1", "true", "yes", "on")


def production_problems(conf: dict) -> list[str]:
    """Everything that makes a production configuration unsafe (empty = OK)."""
    problems = []
    secret = conf.get("SECRET_KEY") or ""
    if not secret or secret == conf.get("INSECURE_DEV_SECRET") or len(secret) < MIN_SECRET_LENGTH:
        problems.append(f"DJANGO_SECRET_KEY must be set to a random value of at least {MIN_SECRET_LENGTH} characters")
    if conf.get("DEBUG"):
        problems.append("DJANGO_DEBUG must be false")
    hosts = conf.get("ALLOWED_HOSTS") or []
    if not hosts or "*" in hosts:
        problems.append("DJANGO_ALLOWED_HOSTS must list the real host names (no '*')")
    if conf.get("AI_PROVIDER") not in ("stub", "anthropic", "gemini", "groq"):
        problems.append("AI_PROVIDER must be one of stub|anthropic|gemini|groq")
    return problems


def apply_production_security(conf: dict) -> None:
    """Called at the end of settings.py with its globals()."""
    if not conf.get("IS_PRODUCTION"):
        return
    problems = production_problems(conf)
    if problems:
        raise ImproperlyConfigured("Unsafe production configuration: " + "; ".join(problems))

    # HTTPS is terminated by the reverse proxy / platform in a typical POC deployment.
    if _bool("SECURE_PROXY_SSL_HEADER", True):
        conf["SECURE_PROXY_SSL_HEADER"] = ("HTTP_X_FORWARDED_PROTO", "https")
    conf["SECURE_SSL_REDIRECT"] = _bool("SECURE_SSL_REDIRECT", True)
    conf["SECURE_REDIRECT_EXEMPT"] = [r"^api/v1/health/"]  # platform probes may use plain HTTP
    # Only set SECURE_COOKIES=false for a local plain-HTTP stack (docker compose on localhost).
    secure_cookies = _bool("SECURE_COOKIES", True)
    conf["SESSION_COOKIE_SECURE"] = secure_cookies
    conf["CSRF_COOKIE_SECURE"] = secure_cookies
    conf["SESSION_COOKIE_HTTPONLY"] = True
    # Start HSTS modestly; raise to 31536000 once HTTPS is confirmed stable.
    conf["SECURE_HSTS_SECONDS"] = int(os.environ.get("SECURE_HSTS_SECONDS", "3600"))
    conf["SECURE_HSTS_INCLUDE_SUBDOMAINS"] = _bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
    conf["SECURE_HSTS_PRELOAD"] = False
    conf["SECURE_CONTENT_TYPE_NOSNIFF"] = True
    conf["SECURE_REFERRER_POLICY"] = "same-origin"
    conf["SECURE_CROSS_ORIGIN_OPENER_POLICY"] = "same-origin"
    conf["X_FRAME_OPTIONS"] = "DENY"
