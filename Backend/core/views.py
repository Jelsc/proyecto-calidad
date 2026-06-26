from django.http import JsonResponse


def api_root(request):
    return JsonResponse(
        {
            "service": "CyberShield AI API",
                "status": "running",
                "version": "0.1.0",
                "endpoints": {
                    "health": "/api/health/",
                    "auth": "/api/auth/",
                    "auth_login": "/api/auth/login/",
                    "auth_refresh": "/api/auth/refresh/",
                    "auth_me": "/api/auth/me/",
                "events": "/api/events/",
                "detection_simulation": "/api/detection/simulate/",
                "detection_train": "/api/detection/train/",
                "incidents": "/api/incidents/",
                "response_actions": "/api/responses/",
                "dashboard_summary": "/api/dashboard/summary/",
            },
        }
    )


def health_check(request):
    return JsonResponse({"status": "ok"})
