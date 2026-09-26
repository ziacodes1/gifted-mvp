"""Django settings for the Gifted MVP (modular monolith)."""
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    return env(key, str(default)).lower() in ("1", "true", "yes", "on")


# --- Core ---------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

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
    "corsheaders",
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
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
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
    }
}

# --- Auth ---------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 6}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
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
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_ACCESS_MIN", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(env("JWT_REFRESH_DAYS", "7"))),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# --- I18N / TZ ----------------------------------------------------------
LANGUAGE_CODE = "en"
LANGUAGES = [("en", "English"), ("uz", "O‘zbekcha"), ("ru", "Русский")]
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static & Media -----------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024  # 2MB, per spec
# Private learner uploads (diary photos). Deliberately outside MEDIA_ROOT, so they are never
# served by the public /media/ route — only through owner-checked API views.
PRIVATE_MEDIA_ROOT = Path(env("PRIVATE_MEDIA_ROOT", str(BASE_DIR / "private_media")))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- CORS (local frontend) ---------------------------------------------
CORS_ALLOWED_ORIGINS = env(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")
CORS_ALLOW_CREDENTIALS = True

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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"apps.ai": {"handlers": ["console"], "level": "INFO"}},
}
