from django.urls import include, path

from .views import health_check, api_root

urlpatterns = [
    path("", api_root, name="api-root"),
    path("health/", health_check, name="health-check"),
    path("auth/", include("accounts.urls")),
    path("", include("events.urls")),
    path("ai/", include("ai.urls")),
    path("", include("detection.urls")),
    path("", include("incidents.urls")),
    path("", include("response_engine.urls")),
    path("", include("reports.urls")),
]
