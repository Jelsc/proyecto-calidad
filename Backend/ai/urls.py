from django.urls import path

from .views import AiClassificationView, AiRootView, AlertExplanationView, IncidentSummaryView, TechnicalReportView


urlpatterns = [
    path("", AiRootView.as_view(), name="ai-root"),
    path("classify/", AiClassificationView.as_view(), name="ai-classify"),
    path("explain/", AlertExplanationView.as_view(), name="ai-explain"),
    path("summarize/", IncidentSummaryView.as_view(), name="ai-summarize"),
    path("report/", TechnicalReportView.as_view(), name="ai-report"),
]
