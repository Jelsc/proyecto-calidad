from __future__ import annotations

import json
from functools import lru_cache
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline


ENGINE_VERSION = "local-tfidf-logreg-v1"
AZURE_PROVIDER_NAMES = {"azure", "azure_openai"}
AZURE_DEFAULT_API_VERSION = "2024-02-15-preview"
FAMILIES = [
    "ddos",
    "worms",
    "trojans",
    "ransomware",
    "exfiltration",
    "lateral_movement",
]

_CLASSIFIER_TRAINING_DATA = [
    ("massive connection flood from many sources overwhelmed the edge service", "ddos"),
    ("volumetric traffic surge and syn flood exhausted the application gateway", "ddos"),
    ("the worm scanned hosts and replicated itself across network shares", "worms"),
    ("self-spreading malware moved through internal machines without user action", "worms"),
    ("a trojan disguised as a utility opened a backdoor and ran payloads", "trojans"),
    ("dropper installed a malicious backdoor after the user launched the fake update", "trojans"),
    ("shared files were encrypted and a ransom note demanded payment", "ransomware"),
    ("the malware encrypted backups and asked for bitcoin to restore access", "ransomware"),
    ("data was staged and uploaded to an external destination", "exfiltration"),
    ("large outbound transfer and archive staging indicated a leak", "exfiltration"),
    ("the attacker reused credentials to pivot between hosts and remote services", "lateral_movement"),
    ("privileged access was used to move laterally across internal systems", "lateral_movement"),
]


def _normalize_text(text: str) -> str:
    return " ".join(text.split()).strip()


def _fallback_excerpt(text: str, limit: int = 120, empty_message: str = "No text was provided.") -> str:
    clean_text = _normalize_text(text)
    if not clean_text:
        return empty_message

    return clean_text[:limit].rstrip()


def _split_contextual_payload(text: str) -> tuple[str, str]:
    clean_text = _normalize_text(text)
    if not clean_text:
        return "", ""

    context_marker = "Contexto del incidente:"
    prompt_marker = "Pregunta o instrucción:"

    context_text = clean_text
    prompt_text = ""

    if context_marker in clean_text and prompt_marker in clean_text:
        after_context = clean_text.split(context_marker, 1)[1].strip()
        context_text, prompt_text = after_context.split(prompt_marker, 1)
        context_text = context_text.strip()
        prompt_text = prompt_text.strip()
    elif prompt_marker in clean_text:
        before_prompt, prompt_text = clean_text.split(prompt_marker, 1)
        context_text = before_prompt.strip()
        prompt_text = prompt_text.strip()

    return context_text, prompt_text


def _build_classifier() -> Pipeline:
    texts = [item[0] for item in _CLASSIFIER_TRAINING_DATA]
    labels = [item[1] for item in _CLASSIFIER_TRAINING_DATA]
    classifier = Pipeline(
            [
                ("vectorizer", TfidfVectorizer(ngram_range=(1, 2))),
                (
                    "classifier",
                    KNeighborsClassifier(n_neighbors=1, weights="distance", algorithm="brute", metric="cosine"),
                ),
            ]
    )
    classifier.fit(texts, labels)
    return classifier


def get_ai_provider_config() -> dict[str, Any]:
    raw_config = getattr(settings, "AI_PROVIDER_CONFIG", {})
    raw_azure_config = raw_config.get("azure_openai", {}) if isinstance(raw_config, dict) else {}

    provider = str(getattr(settings, "AI_PROVIDER", "") or raw_config.get("provider", "local")).strip().lower() or "local"
    fallback_provider = str(getattr(settings, "AI_PROVIDER_FALLBACK", "") or raw_config.get("fallback_provider", "local")).strip().lower() or "local"
    endpoint = str(getattr(settings, "AZURE_OPENAI_ENDPOINT", "") or raw_azure_config.get("endpoint", "")).strip().rstrip("/")
    project_endpoint = str(getattr(settings, "AZURE_AI_PROJECT_ENDPOINT", "") or raw_azure_config.get("project_endpoint", "")).strip().rstrip("/")

    project = str(getattr(settings, "AZURE_OPENAI_PROJECT", "") or raw_azure_config.get("project", "")).strip()
    deployment = str(getattr(settings, "AZURE_OPENAI_DEPLOYMENT", "") or raw_azure_config.get("deployment", "")).strip()
    api_version = (
        str(getattr(settings, "AZURE_OPENAI_API_VERSION", "") or raw_azure_config.get("api_version", AZURE_DEFAULT_API_VERSION)).strip()
        or AZURE_DEFAULT_API_VERSION
    )
    api_key = str(getattr(settings, "AZURE_OPENAI_API_KEY", "")).strip()
    has_api_key = bool(api_key or getattr(settings, "AZURE_OPENAI_HAS_API_KEY", False) or raw_azure_config.get("has_api_key", False))

    ready = provider in AZURE_PROVIDER_NAMES and bool(endpoint and project and deployment and has_api_key)

    return {
        "provider": provider,
        "active_provider": "azure_openai" if ready else fallback_provider,
        "fallback_provider": fallback_provider,
        "azure_openai": {
            "endpoint": endpoint,
            "project_endpoint": project_endpoint,
            "project": project,
            "deployment": deployment,
            "api_version": api_version,
            "has_credentials": has_api_key,
            "ready": ready,
        },
    }


@lru_cache(maxsize=1)
def _classifier() -> Pipeline:
    return _build_classifier()


class AiService:
    def __init__(self) -> None:
        self.provider_config = get_ai_provider_config()

    def _azure_openai_config(self) -> dict[str, Any]:
        return self.provider_config["azure_openai"]

    def _azure_ready(self) -> bool:
        return self.provider_config["active_provider"] == "azure_openai"

    def _azure_engine_version(self) -> str:
        deployment = self._azure_openai_config()["deployment"]
        return f"azure-openai:{deployment}" if deployment else "azure-openai"

    def _call_azure_chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        azure_config = self._azure_openai_config()
        endpoint = azure_config["endpoint"]
        deployment = azure_config["deployment"]
        api_version = azure_config["api_version"]
        api_key = str(getattr(settings, "AZURE_OPENAI_API_KEY", "")).strip()

        if not (endpoint and deployment and api_key):
            raise RuntimeError("Azure OpenAI is not fully configured.")

        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
        }
        request = urllib_request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "api-key": api_key,
            },
            method="POST",
        )

        with urllib_request.urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))

        return str(body["choices"][0]["message"]["content"]).strip()

    def _local_classify_threat_family(self, text: str) -> dict[str, Any]:
        try:
            classifier = _classifier()
            probabilities = classifier.predict_proba([text])[0]
            best_index = int(probabilities.argmax())
            return {
                "family": str(classifier.classes_[best_index]),
                "confidence": round(float(probabilities[best_index]), 3),
                "engine": ENGINE_VERSION,
            }
        except Exception:
            return {"family": "unknown", "confidence": 0.0, "engine": "fallback-unknown"}

    def _local_explain_alert(self, text: str) -> str:
        context, prompt = _split_contextual_payload(text)
        prompt_excerpt = _fallback_excerpt(prompt, limit=90, empty_message="¿Qué causó esta alerta?")
        context_excerpt = _fallback_excerpt(context, limit=160, empty_message="No alert text was provided.")
        if not prompt.strip():
            return (
                f"Explicación de alerta: {context_excerpt} "
                "Acción recomendada: preservar evidencia, confirmar el host afectado y escalar si la actividad continúa."
            )

        return "\n".join(
            [
                f"Explicación de alerta: {prompt_excerpt}",
                f"Contexto relevante: {context_excerpt}",
                "Acción recomendada: preservar evidencia, confirmar el host afectado y escalar si la actividad continúa.",
            ]
        )

    def _local_summarize_incident(self, text: str) -> str:
        context, prompt = _split_contextual_payload(text)
        context_excerpt = _fallback_excerpt(context, empty_message="No text was provided.")
        prompt_excerpt = _fallback_excerpt(prompt, limit=90, empty_message="Resumen operativo del incidente")
        if not prompt.strip():
            return f"Resumen de incidente: {context_excerpt}"

        return "\n".join(
            [
                f"Resumen de incidente: {context_excerpt}",
                f"Enfoque: {prompt_excerpt}",
            ]
        )

    def _local_generate_report(self, text: str) -> str:
        context, prompt = _split_contextual_payload(text)
        context_excerpt = _fallback_excerpt(context, limit=180, empty_message="No text was provided.")
        prompt_excerpt = _fallback_excerpt(prompt, limit=90, empty_message="Generar reporte técnico")
        return "\n".join(
            [
                "Reporte técnico",
                f"Solicitud: {prompt_excerpt}",
                f"Resumen: {context_excerpt}",
                f"Indicadores observados: {context_excerpt}",
                "Acciones recomendadas: preservar evidencia, aislar los activos afectados, revisar registros y continuar el análisis.",
            ]
        )

    def _azure_classify_threat_family(self, text: str) -> dict[str, Any] | None:
        system_prompt = (
            "Return only a JSON object with the keys family and confidence. "
            f"family must be one of: {', '.join(FAMILIES)}. "
            "confidence must be a number from 0 to 1. No extra text."
        )
        content = self._call_azure_chat_completion(system_prompt, text)
        parsed = json.loads(content)
        family = str(parsed.get("family", "")).strip().lower()
        if family not in FAMILIES:
            return None

        confidence = parsed.get("confidence", 0.0)
        try:
            confidence_value = max(0.0, min(1.0, float(confidence)))
        except (TypeError, ValueError):
            confidence_value = 0.0

        return {
            "family": family,
            "confidence": round(confidence_value, 3),
            "engine": self._azure_engine_version(),
        }

    def _azure_explain_alert(self, text: str) -> str:
        system_prompt = "Escribe una explicación breve de la alerta en español, con una sola acción recomendada."
        return self._call_azure_chat_completion(system_prompt, text)

    def _azure_summarize_incident(self, text: str) -> str:
        system_prompt = "Escribe un resumen breve del incidente en español, sin viñetas."
        return self._call_azure_chat_completion(system_prompt, text)

    def _azure_generate_report(self, text: str) -> str:
        system_prompt = "Escribe un reporte técnico breve en español con resumen, indicadores observados y acciones recomendadas."
        return self._call_azure_chat_completion(system_prompt, text)

    def classify_threat_family(self, text: str) -> dict[str, Any]:
        clean_text = _normalize_text(text)
        if not clean_text:
            return {"family": "unknown", "confidence": 0.0, "engine": ENGINE_VERSION}

        if self._azure_ready():
            try:
                azure_result = self._azure_classify_threat_family(clean_text)
                if azure_result is not None:
                    return azure_result
            except (json.JSONDecodeError, KeyError, TypeError, ValueError, RuntimeError, urllib_error.URLError, urllib_error.HTTPError, OSError):
                pass

        return self._local_classify_threat_family(clean_text)

    def explain_alert(self, text: str) -> str:
        clean_text = _normalize_text(text)
        if not clean_text:
            return self._local_explain_alert(text)

        if self._azure_ready():
            try:
                azure_text = self._azure_explain_alert(clean_text)
                if azure_text:
                    return azure_text
            except (json.JSONDecodeError, KeyError, TypeError, ValueError, RuntimeError, urllib_error.URLError, urllib_error.HTTPError, OSError):
                pass

        return self._local_explain_alert(clean_text)

    def summarize_incident(self, text: str) -> str:
        clean_text = _normalize_text(text)
        if not clean_text:
            return self._local_summarize_incident(text)

        if self._azure_ready():
            try:
                azure_text = self._azure_summarize_incident(clean_text)
                if azure_text:
                    return azure_text
            except (json.JSONDecodeError, KeyError, TypeError, ValueError, RuntimeError, urllib_error.URLError, urllib_error.HTTPError, OSError):
                pass

        return self._local_summarize_incident(clean_text)

    def generate_report(self, text: str) -> str:
        clean_text = _normalize_text(text)
        if not clean_text:
            return self._local_generate_report(text)

        if self._azure_ready():
            try:
                azure_text = self._azure_generate_report(clean_text)
                if azure_text:
                    return azure_text
            except (json.JSONDecodeError, KeyError, TypeError, ValueError, RuntimeError, urllib_error.URLError, urllib_error.HTTPError, OSError):
                pass

        return self._local_generate_report(clean_text)


_SERVICE = AiService()


def get_ai_service() -> AiService:
    return AiService()


def classify_threat_family(text: str) -> dict[str, Any]:
    return get_ai_service().classify_threat_family(text)


def explain_alert(text: str) -> str:
    return get_ai_service().explain_alert(text)


def summarize_incident(text: str) -> str:
    return get_ai_service().summarize_incident(text)


def generate_report(text: str) -> str:
    return get_ai_service().generate_report(text)
