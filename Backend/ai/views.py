from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAnalystOrAdmin

from .services import FAMILIES, ENGINE_VERSION, classify_threat_family, explain_alert, generate_report, get_ai_provider_config, summarize_incident


def build_ai_contract() -> dict[str, object]:
    provider_config = get_ai_provider_config()
    azure_config = provider_config["azure_openai"]
    model_engine = ENGINE_VERSION
    if provider_config["active_provider"] == "azure_openai":
        model_engine = f"azure-openai:{azure_config['deployment']}" if azure_config["deployment"] else "azure-openai"

    return {
        "routes": {
            "root": "/api/ai/",
            "classify_threat_family": "/api/ai/classify/",
            "explain_alert": "/api/ai/explain/",
            "summarize_incident": "/api/ai/summarize/",
            "generate_report": "/api/ai/report/",
        },
        "model": {
            "engine": model_engine,
            "fallback": "deterministic_templates",
            "heuristics": False,
            "families": FAMILIES,
        },
        "provider": {
            "requested": provider_config["provider"],
            "active": provider_config["active_provider"],
            "fallback": provider_config["fallback_provider"],
            "azure_openai": azure_config,
        },
    }


def _extract_text(payload: dict, *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    return ""


def _compose_contextual_text(payload: dict, *, context_keys: tuple[str, ...], prompt_keys: tuple[str, ...]) -> str:
    incident_context = _extract_text(payload, *context_keys)
    prompt = _extract_text(payload, *prompt_keys)

    if incident_context and prompt:
        return f"Contexto del incidente:\n{incident_context}\n\nPregunta o instrucción:\n{prompt}"

    return incident_context or prompt


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
        text = _compose_contextual_text(
            request.data,
            context_keys=("alert_text", "incident_text", "incident_context", "text"),
            prompt_keys=("prompt", "question", "instruction"),
        )
        if not text:
            return Response({"detail": "alert_text is required."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"explanation": explain_alert(text)}, status=status.HTTP_200_OK)


class IncidentSummaryView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated(), IsAnalystOrAdmin()]

    def post(self, request):
        text = _compose_contextual_text(
            request.data,
            context_keys=("incident_text", "incident_context", "text"),
            prompt_keys=("prompt", "question", "instruction"),
        )
        if not text:
            return Response({"detail": "incident_text is required."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"summary": summarize_incident(text)}, status=status.HTTP_200_OK)


class TechnicalReportView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated(), IsAnalystOrAdmin()]

    def post(self, request):
        text = _compose_contextual_text(
            request.data,
            context_keys=("incident_text", "incident_context", "text"),
            prompt_keys=("prompt", "question", "instruction"),
        )
        if not text:
            return Response({"detail": "incident_text is required."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"report": generate_report(text)}, status=status.HTTP_200_OK)
