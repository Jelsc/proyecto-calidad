from detection.views import build_detection_contract
from ai.views import build_ai_contract


API_SERVICE_NAME = "CyberShield AI API"
API_STATUS = "running"
API_VERSION = "0.1.0"

API_ENDPOINTS = {
    "health": "/api/health/",
    "auth": "/api/auth/",
    "auth_login": "/api/auth/login/",
    "auth_refresh": "/api/auth/refresh/",
    "auth_me": "/api/auth/me/",
    "events": "/api/events/",
    "detection_simulation": "/api/detection/simulate/",
    "detection_train": "/api/detection/train/",
    "ai": "/api/ai/",
    "ai_classify": "/api/ai/classify/",
    "ai_explain": "/api/ai/explain/",
    "ai_summarize": "/api/ai/summarize/",
    "ai_report": "/api/ai/report/",
    "incidents": "/api/incidents/",
    "response_actions": "/api/responses/",
    "dashboard_summary": "/api/dashboard/summary/",
}

AUTH_CURRENT_USER_FIELDS = [
    "id",
    "username",
    "first_name",
    "last_name",
    "email",
    "is_staff",
    "is_superuser",
    "roles",
]

EVENTS_CONTRACT = {
    "routes": {
        "list_create": "/api/events/",
    },
    "permissions": {
        "list": "authenticated",
        "create": "operator_or_admin",
    },
    "ingested_by": "request.user.username",
}


def build_auth_contract() -> dict[str, object]:
    return {
        "routes": {
            "login": "/api/auth/login/",
            "refresh": "/api/auth/refresh/",
            "current_user": "/api/auth/me/",
        },
        "current_user": {
            "authentication": "jwt",
            "fields": AUTH_CURRENT_USER_FIELDS,
        },
    }


def build_events_contract() -> dict[str, object]:
    return EVENTS_CONTRACT


def build_api_contract() -> dict[str, object]:
    return {
        "service": API_SERVICE_NAME,
        "status": API_STATUS,
        "version": API_VERSION,
        "endpoints": API_ENDPOINTS,
        "auth": build_auth_contract(),
        "events": build_events_contract(),
        "ai": build_ai_contract(),
        "detection": build_detection_contract(),
    }
