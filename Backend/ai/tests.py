from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch
from urllib import error as urllib_error

from ai.services import AiService, classify_threat_family, explain_alert, generate_report, get_ai_provider_config, summarize_incident
from ai.views import build_ai_contract


User = get_user_model()


class AiServiceTests(TestCase):
    def test_ai_provider_config_reads_azure_settings_without_secret_leakage(self):
        with override_settings(
            AI_PROVIDER="azure_openai",
            AI_PROVIDER_CONFIG={
                "provider": "azure_openai",
                "fallback_provider": "local",
                "azure_openai": {
                    "endpoint": "https://example.openai.azure.com",
                    "project_endpoint": "https://project.example.azure.com/projects/project-alpha",
                    "project": "project-alpha",
                    "deployment": "gpt-4o-mini",
                    "api_version": "2024-06-01",
                    "has_api_key": True,
                },
            },
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com",
            AZURE_AI_PROJECT_ENDPOINT="https://project.example.azure.com/projects/project-alpha",
            AZURE_OPENAI_PROJECT="project-alpha",
            AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini",
            AZURE_OPENAI_API_VERSION="2024-06-01",
            AZURE_OPENAI_HAS_API_KEY=True,
        ):
            config = get_ai_provider_config()

        self.assertEqual(config["provider"], "azure_openai")
        self.assertEqual(config["active_provider"], "azure_openai")
        self.assertEqual(config["azure_openai"]["endpoint"], "https://example.openai.azure.com")
        self.assertEqual(config["azure_openai"]["project_endpoint"], "https://project.example.azure.com/projects/project-alpha")
        self.assertEqual(config["azure_openai"]["project"], "project-alpha")
        self.assertEqual(config["azure_openai"]["deployment"], "gpt-4o-mini")
        self.assertTrue(config["azure_openai"]["ready"])
        self.assertNotIn("api_key", config["azure_openai"])

    def test_build_ai_contract_reports_provider_readiness_and_fallback_mode(self):
        with override_settings(
            AI_PROVIDER="azure_openai",
            AI_PROVIDER_CONFIG={
                "provider": "azure_openai",
                "fallback_provider": "local",
                "azure_openai": {
                    "endpoint": "https://example.openai.azure.com",
                    "project_endpoint": "https://project.example.azure.com/projects/project-alpha",
                    "project": "project-alpha",
                    "deployment": "gpt-4o-mini",
                    "api_version": "2024-06-01",
                    "has_api_key": True,
                },
            },
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com",
            AZURE_AI_PROJECT_ENDPOINT="https://project.example.azure.com/projects/project-alpha",
            AZURE_OPENAI_PROJECT="project-alpha",
            AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini",
            AZURE_OPENAI_API_KEY="secret-value",
            AZURE_OPENAI_API_VERSION="2024-06-01",
        ):
            contract = build_ai_contract()

        self.assertEqual(contract["model"]["engine"], "azure-openai:gpt-4o-mini")
        self.assertEqual(
            contract["provider"],
            {
                "requested": "azure_openai",
                "active": "azure_openai",
                "fallback": "local",
                "azure_openai": {
                    "endpoint": "https://example.openai.azure.com",
                    "project_endpoint": "https://project.example.azure.com/projects/project-alpha",
                    "project": "project-alpha",
                    "deployment": "gpt-4o-mini",
                    "api_version": "2024-06-01",
                    "has_credentials": True,
                    "ready": True,
                },
            },
        )

    def test_classify_threat_family_identifies_ransomware_language(self):
        result = classify_threat_family("Encryption activity spread across file shares and ransom notes appeared.")

        self.assertEqual(result["family"], "ransomware")
        self.assertGreater(result["confidence"], 0.5)

    def test_classify_threat_family_identifies_lateral_movement_language(self):
        result = classify_threat_family("The attacker reused credentials to pivot between hosts and remote services.")

        self.assertEqual(result["family"], "lateral_movement")
        self.assertGreater(result["confidence"], 0.5)

    def test_explain_alert_returns_a_deterministic_response(self):
        explanation = explain_alert(
            "Contexto del incidente: Unexpected outbound tunneling observed after privileged login.\n\nPregunta o instrucción: ¿Qué causó esta alerta?"
        )

        self.assertEqual(
            explanation,
            "Explicación de alerta: ¿Qué causó esta alerta?\nContexto relevante: Unexpected outbound tunneling observed after privileged login.\nAcción recomendada: preservar evidencia, confirmar el host afectado y escalar si la actividad continúa.",
        )

    def test_explain_alert_handles_blank_text_without_guessing(self):
        explanation = explain_alert("")

        self.assertEqual(
            explanation,
            "Explicación de alerta: No alert text was provided. Acción recomendada: preservar evidencia, confirmar el host afectado y escalar si la actividad continúa.",
        )

    def test_summarize_incident_returns_short_operational_summary(self):
        summary = summarize_incident(
            "Contexto del incidente: Multiple hosts were contacted, logs were collected, and containment is underway.\n\nPregunta o instrucción: Resume este incidente en lenguaje simple."
        )

        self.assertEqual(
            summary,
            "Resumen de incidente: Multiple hosts were contacted, logs were collected, and containment is underway.\nEnfoque: Resume este incidente en lenguaje simple.",
        )

    def test_generate_report_returns_structured_technical_text(self):
        report = generate_report(
            "Contexto del incidente: A suspicious executable encrypted shared files and attempted to contact a command server.\n\nPregunta o instrucción: Redacta un reporte técnico breve."
        )

        self.assertIn("Reporte técnico", report)
        self.assertIn("Solicitud:", report)
        self.assertIn("Resumen:", report)
        self.assertIn("Acciones recomendadas:", report)

    def test_classify_threat_family_uses_azure_when_configured(self):
        with override_settings(
            AI_PROVIDER="azure_openai",
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com",
            AZURE_AI_PROJECT_ENDPOINT="https://project.example.azure.com/projects/project-alpha",
            AZURE_OPENAI_PROJECT="project-alpha",
            AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini",
            AZURE_OPENAI_API_KEY="secret-value",
            AZURE_OPENAI_API_VERSION="2024-06-01",
        ):
            service = AiService()
            self.assertEqual(
                service.provider_config["azure_openai"]["endpoint"],
                "https://example.openai.azure.com",
            )
            with patch.object(
                AiService,
                "_call_azure_chat_completion",
                return_value='{"family": "worms", "confidence": 0.91}',
            ) as azure_call:
                result = service.classify_threat_family("Self-spreading malware moved through internal machines.")

        self.assertEqual(result["family"], "worms")
        self.assertEqual(result["engine"], "azure-openai:gpt-4o-mini")
        self.assertEqual(result["confidence"], 0.91)
        azure_call.assert_called_once()

    def test_ai_service_falls_back_to_local_when_azure_is_missing_credentials(self):
        with override_settings(
            AI_PROVIDER="azure_openai",
            AI_PROVIDER_CONFIG={
                "provider": "azure_openai",
                "fallback_provider": "local",
                "azure_openai": {
                    "endpoint": "https://example.openai.azure.com",
                    "project_endpoint": "",
                    "project": "project-alpha",
                    "deployment": "gpt-4o-mini",
                    "api_version": "2024-06-01",
                    "has_api_key": False,
                },
            },
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com",
            AZURE_OPENAI_PROJECT="project-alpha",
            AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini",
            AZURE_OPENAI_API_KEY="",
            AZURE_OPENAI_HAS_API_KEY=False,
        ):
            service = AiService()
            with patch.object(AiService, "_call_azure_chat_completion") as azure_call:
                result = service.explain_alert("Unexpected outbound tunneling observed after privileged login.")

        self.assertEqual(
            result,
            "Explicación de alerta: Unexpected outbound tunneling observed after privileged login. Acción recomendada: preservar evidencia, confirmar el host afectado y escalar si la actividad continúa.",
        )
        azure_call.assert_not_called()

    def test_ai_service_falls_back_to_local_when_azure_call_fails(self):
        with override_settings(
            AI_PROVIDER="azure_openai",
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com",
            AZURE_AI_PROJECT_ENDPOINT="https://project.example.azure.com/projects/project-alpha",
            AZURE_OPENAI_PROJECT="project-alpha",
            AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini",
            AZURE_OPENAI_API_KEY="secret-value",
        ):
            service = AiService()
            with patch.object(AiService, "_call_azure_chat_completion", side_effect=urllib_error.URLError("offline")) as azure_call:
                result = service.summarize_incident("The host was isolated and artifacts were preserved.")

        self.assertEqual(result, "Resumen de incidente: The host was isolated and artifacts were preserved.")
        azure_call.assert_called_once()


class AiEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.group, _ = Group.objects.get_or_create(name="analyst")
        self.user = User.objects.create_user(
            username="ai-demo",
            email="ai@cybershield.local",
            password="CyberShield123!",
            is_staff=True,
        )
        self.user.groups.add(self.group)

    def authenticate(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": self.user.username, "password": "CyberShield123!"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.json()['access']}")

    def test_ai_root_returns_the_ai_contract(self):
        with override_settings(
            AI_PROVIDER="local",
            AI_PROVIDER_CONFIG={
                "provider": "local",
                "fallback_provider": "local",
                "azure_openai": {
                    "endpoint": "",
                    "project_endpoint": "",
                    "project": "",
                    "deployment": "",
                    "api_version": "2024-02-15-preview",
                    "has_api_key": False,
                },
            },
            AZURE_OPENAI_ENDPOINT="",
            AZURE_AI_PROJECT_ENDPOINT="",
            AZURE_OPENAI_PROJECT="",
            AZURE_OPENAI_DEPLOYMENT="",
            AZURE_OPENAI_API_VERSION="2024-02-15-preview",
            AZURE_OPENAI_API_KEY="",
            AZURE_OPENAI_HAS_API_KEY=False,
        ):
            self.authenticate()

            response = self.client.get(reverse("ai-root"))

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), build_ai_contract())

    def test_classify_endpoint_returns_a_family_and_confidence(self):
        self.authenticate()

        response = self.client.post(
            reverse("ai-classify"),
            {"text": "Mass connection flood overloaded the edge service from many sources."},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["family"], "ddos")
        self.assertGreater(response.json()["confidence"], 0.5)

    def test_text_generation_endpoints_return_expected_shapes(self):
        self.authenticate()

        explanation_response = self.client.post(
            reverse("ai-explain"),
            {"alert_text": "Outbound traffic began tunneling through an unusual domain."},
            format="json",
        )
        summary_response = self.client.post(
            reverse("ai-summarize"),
            {"incident_text": "The host was isolated, artifacts were preserved, and the scope is still expanding."},
            format="json",
        )
        report_response = self.client.post(
            reverse("ai-report"),
            {"incident_text": "The host was isolated, artifacts were preserved, and the scope is still expanding."},
            format="json",
        )

        self.assertEqual(explanation_response.status_code, 200)
        self.assertIn("Explicación de alerta:", explanation_response.json()["explanation"])
        self.assertEqual(summary_response.status_code, 200)
        self.assertIn("Resumen de incidente:", summary_response.json()["summary"])
        self.assertEqual(report_response.status_code, 200)
        self.assertIn("Reporte técnico", report_response.json()["report"])

    def test_text_generation_endpoints_merge_context_and_prompt(self):
        self.authenticate()

        cases = [
            (
                reverse("ai-explain"),
                "alert_text",
                "explanation",
                "ai.views.explain_alert",
                "Alerta en el perímetro con conexiones salientes anómalas.",
            ),
            (
                reverse("ai-summarize"),
                "incident_text",
                "summary",
                "ai.views.summarize_incident",
                "Se aislaron hosts y se preservaron evidencias.",
            ),
            (
                reverse("ai-report"),
                "incident_text",
                "report",
                "ai.views.generate_report",
                "Se aisló el host, se preservaron artefactos y el alcance sigue creciendo.",
            ),
        ]

        for path, payload_key, response_key, mock_path, incident_text in cases:
            with patch(mock_path, return_value=f"mocked-{response_key}") as mocked_service:
                response = self.client.post(
                    path,
                    {
                        payload_key: incident_text,
                        "prompt": "¿Qué recomiendas hacer ahora?",
                    },
                    format="json",
                )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()[response_key], f"mocked-{response_key}")
            mocked_service.assert_called_once()
            composed_text = mocked_service.call_args.args[0]
            self.assertIn(incident_text, composed_text)
            self.assertIn("¿Qué recomiendas hacer ahora?", composed_text)
            self.assertIn("Contexto del incidente:", composed_text)
            self.assertIn("Pregunta o instrucción:", composed_text)
