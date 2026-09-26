"""Request ids + structured log formatting (stdlib only: loaded while logging is configured,
before Django apps are ready).

- Every request gets an id (incoming `X-Request-ID` if sane, else a new one). It is returned
  in the response header and attached to every log line of that request.
- Log lines never contain secrets, prompts or learner-written text.
"""
from __future__ import annotations

import contextvars
import json
import logging
import re
import time
import uuid

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
_SAFE_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
access_log = logging.getLogger("gifted.request")


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.META.get("HTTP_X_REQUEST_ID", "")
        rid = incoming if _SAFE_ID.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(rid)
        request.request_id = rid
        started = time.monotonic()
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = rid
            if request.path.startswith("/api/") and not request.path.startswith("/api/v1/health/"):
                # Path + status + timing only: no query strings, bodies or user content.
                access_log.info(
                    "request method=%s path=%s status=%s duration_ms=%d",
                    request.method,
                    request.path,
                    response.status_code,
                    (time.monotonic() - started) * 1000,
                )
            return response
        finally:
            request_id_var.reset(token)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        return json.dumps(payload, ensure_ascii=False)
