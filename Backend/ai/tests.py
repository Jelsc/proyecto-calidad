from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

from ai.services import AiService, classify_threat_family, explain_alert, generate_report, get_ai_provider_config, summarize_incident


User = get_user_model()


class AiServiceTests(TestCase):
    def test_ai_provider_config_reads_azure_settings_without_secret_leakage(self):
        with override_settings(
            AI_PROVIDER="azure_openai",
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com",
            AZURE_OPENAI_PROJECT="project-alpha",
            AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini",
            AZURE_OPENAI_API_VERSION="2024-06-01",
            AZURE_OPENAI_HAS_API_KEY=True,
        ):
            config = get_ai_provider_config()

        self.assertEqual(config["provider"], "azure_openai")
        self.assertEqual(config["active_provider"], "azure_openai")
        self.assertEqual(config["azure_openai"]["endpoint"], "https://example.openai.azure.com")
        self.assertEqual(config["azure_openai"]["project"], "project-alpha")
        self.assertEqual(config["azure_openai"]["deployment"], "gpt-4o-mini")
        self.assertTrue(config["azure_openai"]["ready"])
        self.assertNotIn("api_key", config["azure_openai"])

    def test_classify_threat_family_identifies_ransomware_language(self):
        result = classify_threat_family("Encryption activity spread across file shares and ransom notes appeared.")

        self.assertEqual(result["family"], "ransomware")
        self.assertGreater(result["confidence"], 0.5)

    def test_classify_threat_family_identifies_lateral_movement_language(self):
        result = classify_threat_family("The attacker reused credentials to pivot between hosts and remote services.")

        self.assertEqual(result["family"], "lateral_movement")
        self.assertGreater(result["confidence"], 0.5)

    def test_explain_alert_returns_a_deterministic_response(self):
        explanation = explain_alert("Unexpected outbound tunneling observed after privileged login.")

        self.assertEqual(
            explanation,
            "Alert explanation: Unexpected outbound tunneling observed after privileged login. Recommended action: preserve evidence, confirm the affected host, and escalate if activity continues.",
        )

    def test_explain_alert_handles_blank_text_without_guessing(self):
        explanation = explain_alert("")

        self.assertEqual(
            explanation,
            "Alert explanation: No alert text was provided. Recommended action: preserve evidence, confirm the affected host, and escalate if activity continues.",
        )

    def test_summarize_incident_returns_short_operational_summary(self):
        summary = summarize_incident("Multiple hosts were contacted, logs were collected, and containment is underway.")

        self.assertEqual(
            summary,
            "Incident summary: Multiple hosts were contacted, logs were collected, and containment is underway.",
        )

    def test_generate_report_returns_structured_technical_text(self):
        report = generate_report("A suspicious executable encrypted shared files and attempted to contact a command server.")

        self.assertIn("Technical report", report)
        self.assertIn("Summary:", report)
        self.assertIn("Recommended actions:", report)

    def test_classify_threat_family_uses_azure_when_configured(self):
        with override_settings(
            AI_PROVIDER="azure_openai",
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com",
            AZURE_OPENAI_PROJECT="project-alpha",
            AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini",
            AZURE_OPENAI_API_KEY="secret-value",
            AZURE_OPENAI_API_VERSION="2024-06-01",
        ):
            service = AiService()
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
            AZURE_OPENAI_ENDPOINT="https://example.openai.azure.com",
            AZURE_OPENAI_PROJECT="project-alpha",
            AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini",
            AZURE_OPENAI_HAS_API_KEY=False,
        ):
            service = AiService()
            with patch.object(AiService, "_call_azure_chat_completion") as azure_call:
                result = service.explain_alert("Unexpected outbound tunneling observed after privileged login.")

        self.assertEqual(
            result,
            "Alert explanation: Unexpected outbound tunneling observed after privileged login. Recommended action: preserve evidence, confirm the affected host, and escalate if activity continues.",
        )
        azure_call.assert_not_called()


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
        self.authenticate()

        response = self.client.get(reverse("ai-root"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["routes"]["classify_threat_family"], "/api/ai/classify/")

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
        self.assertIn("Alert explanation:", explanation_response.json()["explanation"])
        self.assertEqual(summary_response.status_code, 200)
        self.assertIn("Incident summary:", summary_response.json()["summary"])
        self.assertEqual(report_response.status_code, 200)
        self.assertIn("Technical report", report_response.json()["report"])
