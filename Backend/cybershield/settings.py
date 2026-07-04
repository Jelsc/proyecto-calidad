"""Django settings for CyberShield AI."""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()

SECRET_KEY = _env("DJANGO_SECRET_KEY", "django-insecure-change-me")
DEBUG = _env("DJANGO_DEBUG", "1") == "1"

allowed_hosts = _env("DJANGO_ALLOWED_HOSTS", "*")
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts.split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "accounts.apps.AccountsConfig",
    "events.apps.EventsConfig",
    "detection.apps.DetectionConfig",
    "ai.apps.AiConfig",
    "incidents.apps.IncidentsConfig",
    "response_engine.apps.ResponseEngineConfig",
    "reports.apps.ReportsConfig",
    "core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cybershield.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cybershield.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _env("DB_NAME", "cybershield"),
        "USER": _env("DB_USER", "cybershield"),
        "PASSWORD": _env("DB_PASSWORD", "cybershield"),
        "HOST": _env("DB_HOST", "db"),
        "PORT": _env("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AI_PROVIDER = _env("AI_PROVIDER", "local").lower() or "local"
AZURE_OPENAI_ENDPOINT = _env("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
AZURE_AI_PROJECT_ENDPOINT = _env("AZURE_AI_PROJECT_ENDPOINT", "").rstrip("/")
AZURE_OPENAI_PROJECT = _env("AZURE_OPENAI_PROJECT", "")
AZURE_OPENAI_DEPLOYMENT = _env("AZURE_OPENAI_DEPLOYMENT", "")
AZURE_OPENAI_API_VERSION = _env("AZURE_OPENAI_API_VERSION", "2024-02-15-preview") or "2024-02-15-preview"
AZURE_OPENAI_HAS_API_KEY = bool(_env("AZURE_OPENAI_API_KEY", ""))

AI_PROVIDER_CONFIG = {
    "provider": AI_PROVIDER,
    "fallback_provider": "local",
    "azure_openai": {
        "endpoint": AZURE_OPENAI_ENDPOINT,
        "project_endpoint": AZURE_AI_PROJECT_ENDPOINT,
        "project": AZURE_OPENAI_PROJECT,
        "deployment": AZURE_OPENAI_DEPLOYMENT,
        "api_version": AZURE_OPENAI_API_VERSION,
        "has_api_key": AZURE_OPENAI_HAS_API_KEY,
    },
}

CORS_ALLOW_ALL_ORIGINS = DEBUG

if not DEBUG:
    _cors_origins = _env("CORS_ALLOWED_ORIGINS", "")
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(",") if o.strip()]

_csrf_origins = _env("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(",") if o.strip()]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
}
