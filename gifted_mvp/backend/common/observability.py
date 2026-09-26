"""Health probes and optional Sentry. Request ids + log formatting live in common.logs."""
from __future__ import annotations

import logging

from django.conf import settings
from django.db import connection
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# --- Health probes ----------------------------------------------------------------------


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([])
def health_live(request):
    """Liveness: the process is up and serving requests. Checks nothing external."""
    return Response({"status": "ok", "service": "gifted-api", "version": "v1"})


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([])
def health_ready(request):
    """Readiness: the database answers. The AI provider is deliberately NOT checked — every
    AI feature has a deterministic fallback, so a provider outage must not take Gifted down."""
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception:  # noqa: BLE001 — any DB failure means not ready
        return Response({"status": "unavailable", "checks": {"database": "error"}}, status=503)
    return Response({"status": "ok", "checks": {"database": "ok", "ai_provider": settings.AI_PROVIDER}})


def init_sentry() -> None:
    """Optional: only when SENTRY_DSN is set and sentry-sdk is installed. PII is not sent."""
    if not settings.SENTRY_DSN:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
    except ImportError:
        logging.getLogger("apps").warning("SENTRY_DSN is set but sentry-sdk is not installed; skipping")
        return
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[DjangoIntegration()],
        send_default_pii=False,  # minors' data: never attach user details or request bodies
        environment=settings.DJANGO_ENV,
        traces_sample_rate=0.0,
    )
