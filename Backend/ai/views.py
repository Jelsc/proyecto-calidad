from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAnalystOrAdmin

from .services import FAMILIES, ENGINE_VERSION, classify_threat_family, explain_alert, generate_report, summarize_incident


def build_ai_contract() -> dict[str, object]:
    return {
        "routes": {
            "root": "/api/ai/",
            "classify_threat_family": "/api/ai/classify/",
            "explain_alert": "/api/ai/explain/",
            "summarize_incident": "/api/ai/summarize/",
            "generate_report": "/api/ai/report/",
        },
        "model": {
            "engine": ENGINE_VERSION,
            "fallback": "deterministic_templates",
            "heuristics": False,
            "families": FAMILIES,
        },
    }


def _extract_text(payload: dict, *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    return ""


class AiRootView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated()]

    def get(self, request):
        return Response(build_ai_contract())


class AiClassificationView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated(), IsAnalystOrAdmin()]

    def post(self, request):
        text = _extract_text(request.data, "text", "alert_text", "incident_text")
        if not text:
            return Response({"detail": "text is required."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(classify_threat_family(text), status=status.HTTP_200_OK)


class AlertExplanationView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated(), IsAnalystOrAdmin()]

    def post(self, request):
        text = _extract_text(request.data, "alert_text", "text")
        if not text:
            return Response({"detail": "alert_text is required."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"explanation": explain_alert(text)}, status=status.HTTP_200_OK)


class IncidentSummaryView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated(), IsAnalystOrAdmin()]

    def post(self, request):
        text = _extract_text(request.data, "incident_text", "text")
        if not text:
            return Response({"detail": "incident_text is required."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"summary": summarize_incident(text)}, status=status.HTTP_200_OK)


class TechnicalReportView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated(), IsAnalystOrAdmin()]

    def post(self, request):
        text = _extract_text(request.data, "incident_text", "text")
        if not text:
            return Response({"detail": "incident_text is required."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"report": generate_report(text)}, status=status.HTTP_200_OK)
