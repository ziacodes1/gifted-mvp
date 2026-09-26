"""Django settings for the Gifted MVP (modular monolith)."""
from datetime import timedelta
from pathlib import Path

import os
import sys

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    return env(key, str(default)).lower() in ("1", "true", "yes", "on")


def env_list(key: str, default: str = "") -> list[str]:
    return [v.strip() for v in env(key, default).split(",") if v.strip()]


# --- Environment ----------------------------------------------------------
# development (default): convenient local defaults.
# production: fails closed — no insecure fallbacks; see config/security.py.
DJANGO_ENV = env("DJANGO_ENV", "development").lower()
IS_PRODUCTION = DJANGO_ENV == "production"
INSECURE_DEV_SECRET = "dev-insecure-change-me"

# --- Core ---------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", "" if IS_PRODUCTION else INSECURE_DEV_SECRET)
DEBUG = env_bool("DJANGO_DEBUG", not IS_PRODUCTION)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "" if IS_PRODUCTION else "localhost,127.0.0.1")

# --- Applications -------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",  # refresh-token revocation (logout, rotation)
    "corsheaders",
    "drf_spectacular",
]

# Business domains (modular monolith). Only apps with real work live here now;
# add new domains as they are implemented, preserving these boundaries.
LOCAL_APPS = [
    "apps.accounts",
    "apps.questions",
    "apps.assessments",
    "apps.signals",
    "apps.ai",
    "apps.passports",
    "apps.evidence",
    "apps.missions",
    "apps.parents",
    "apps.companion",
    "apps.diary",
    "apps.engagement",
    "apps.today",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "common.logs.RequestIdMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves collected static (Django admin) under gunicorn
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "common.i18n.LanguageMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database -----------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "gifted_mvp"),
        "USER": env("POSTGRES_USER", os.environ.get("USER", "postgres")),
        "PASSWORD": env("POSTGRES_PASSWORD", ""),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(env("DB_CONN_MAX_AGE", "60")),
        "CONN_HEALTH_CHECKS": True,
    }
}

# --- Auth ---------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": int(env("PASSWORD_MIN_LENGTH", "10"))}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- DRF ----------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "common.pagination.default.DefaultPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "common.exceptions.handlers.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "common.openapi.GiftedAutoSchema",
    # Throttling: a global per-IP/per-user ceiling plus scoped limits on sensitive or costly
    # endpoints (views set `throttle_scope`). Rates are env-tunable; see common/throttling.py.
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON", "120/min"),
        "user": env("THROTTLE_USER", "600/min"),
        "auth": env("THROTTLE_AUTH", "10/min"),  # login, register, refresh
        "parent_connect": env("THROTTLE_PARENT_CONNECT", "10/hour"),
        "ai_generation": env("THROTTLE_AI_GENERATION", "30/hour"),  # profile synthesis, parent insight
        "companion": env("THROTTLE_COMPANION", "40/hour"),
        "redeem": env("THROTTLE_REDEEM", "20/hour"),
        "account_delete": env("THROTTLE_ACCOUNT_DELETE", "5/hour"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_ACCESS_MIN", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(env("JWT_REFRESH_DAYS", "7"))),
    # Each refresh returns a new refresh token and blacklists the old one; logout blacklists
    # the current one. Changing the password invalidates every existing token.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "CHECK_REVOKE_TOKEN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# Throttle counters live in the default cache. LocMem is per process: fine for one worker
# in a controlled pilot; use a shared cache (e.g. the DB cache or Redis) when scaling out.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "gifted"}}
# The test suite makes hundreds of requests from one "client"; throttling has its own tests
# (which switch a real cache back on), so counters are disabled for the rest of the suite.
TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"
if TESTING:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}

# --- I18N / TZ ----------------------------------------------------------
LANGUAGE_CODE = "en"
LANGUAGES = [("en", "English"), ("uz", "O‘zbekcha"), ("ru", "Русский")]
TIME_ZONE = "UTC"
# Learners' local day for streaks/weekly points (the server stores UTC).
ACTIVITY_TIME_ZONE = env("ACTIVITY_TIME_ZONE", "Asia/Tashkent")
USE_I18N = True
USE_TZ = True

# --- Static & Media -----------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if IS_PRODUCTION
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024  # 2MB, per spec
# Private learner uploads (diary photos). Deliberately outside MEDIA_ROOT, so they are never
# served by the public /media/ route — only through owner-checked API views.
PRIVATE_MEDIA_ROOT = Path(env("PRIVATE_MEDIA_ROOT", str(BASE_DIR / "private_media")))
# filesystem (default) | s3 — any S3-compatible bucket, private objects, owner-checked views only.
# s3 needs `pip install -r requirements-optional.txt` and the PRIVATE_S3_* variables.
PRIVATE_STORAGE_BACKEND = env("PRIVATE_STORAGE_BACKEND", "filesystem").lower()
PRIVATE_S3_BUCKET = env("PRIVATE_S3_BUCKET", "")
PRIVATE_S3_ENDPOINT_URL = env("PRIVATE_S3_ENDPOINT_URL", "")  # empty = AWS; set for R2/MinIO/etc.
PRIVATE_S3_REGION = env("PRIVATE_S3_REGION", "")
PRIVATE_S3_ACCESS_KEY_ID = env("PRIVATE_S3_ACCESS_KEY_ID", "")
PRIVATE_S3_SECRET_ACCESS_KEY = env("PRIVATE_S3_SECRET_ACCESS_KEY", "")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- CORS (local frontend) ---------------------------------------------
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", "" if IS_PRODUCTION else "http://localhost:5173,http://127.0.0.1:5173"
)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")  # e.g. https://pilot.example.org (Django admin behind a proxy)

# --- AI (provider-agnostic; key only on backend) ------------------------
AI_PROVIDER = env("AI_PROVIDER", "stub")  # stub | anthropic | gemini | groq
AI_SECONDARY_PROVIDER = env("AI_SECONDARY_PROVIDER", "")  # optional failover on transient errors
AI_API_KEY = env("AI_API_KEY", "")  # Anthropic
GEMINI_API_KEY = env("GEMINI_API_KEY", "")
GROQ_API_KEY = env("GROQ_API_KEY", "")
# gpt-oss reasoning depth for Groq (low = fastest; measured no accuracy gain from medium).
GROQ_REASONING_EFFORT = env("GROQ_REASONING_EFFORT", "low")
AI_MODEL = env("AI_MODEL", "")  # empty -> provider default
AI_EFFORT = env("AI_EFFORT", "low")  # short structured output; low is enough
AI_TIMEOUT_SECONDS = float(env("AI_TIMEOUT_SECONDS", "30"))

# --- Parent connection codes -------------------------------------------
PARENT_CODE_TTL_HOURS = int(env("PARENT_CODE_TTL_HOURS", "72"))

# --- API docs -----------------------------------------------------------
API_DOCS_ENABLED = env_bool("API_DOCS_ENABLED", not IS_PRODUCTION)
SPECTACULAR_SETTINGS = {
    "TITLE": "Gifted API",
    "DESCRIPTION": (
        "Gifted POC API. Roles: STUDENT (own data only), PARENT (connected learners' parent-safe "
        "read model only — never diary, Companion chats, mood or private reflections), ADMIN (Django admin). "
        "Auth: `Authorization: Bearer <access JWT>` from `/api/v1/auth/login/`."
    ),
    "VERSION": "v1",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "COMPONENT_SPLIT_REQUEST": True,
}

# --- Observability --------------------------------------------------------
# LOG_FORMAT=json → one JSON object per line (for a log collector); text otherwise.
# Every line carries the request id (X-Request-ID). No secrets, prompts or learner text.
LOG_LEVEL = env("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "common.logs.RequestIdFilter"}},
    "formatters": {
        "json": {"()": "common.logs.JsonFormatter"},
        "text": {"format": "%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "json" if env("LOG_FORMAT", "text") == "json" else "text",
        }
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "apps": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "gifted.request": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

# Optional error reporting: set SENTRY_DSN (and `pip install -r requirements-optional.txt`).
SENTRY_DSN = env("SENTRY_DSN", "")

# --- Production hardening (fails closed) -----------------------------------
from config.security import apply_production_security  # noqa: E402

apply_production_security(globals())
