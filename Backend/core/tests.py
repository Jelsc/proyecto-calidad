from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from detection.model_service import ENGINE_VERSION, MIN_TRAINING_ROWS
from detection.risk import RISK_SCALE

from .contracts import (
    build_ai_contract,
    build_api_contract,
    build_auth_contract,
    build_dashboard_contract,
    build_events_contract,
)


class CoreContractTests(SimpleTestCase):
    def test_auth_contract_exposes_current_user_identity_route(self):
        self.assertEqual(
            build_auth_contract(),
            {
                "routes": {
                    "login": "/api/auth/login/",
                    "refresh": "/api/auth/refresh/",
                    "current_user": "/api/auth/me/",
                },
                "current_user": {
                    "authentication": "jwt",
                    "fields": [
                        "id",
                        "username",
                        "first_name",
                        "last_name",
                        "email",
                        "is_staff",
                        "is_superuser",
                        "roles",
                    ],
                },
            },
        )

    def test_api_contract_exposes_core_discovery_endpoints(self):
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
            contract = build_api_contract()
            self.assertEqual(contract["service"], "CyberShield AI API")
            self.assertEqual(contract["status"], "running")
            self.assertEqual(contract["version"], "0.1.0")
            self.assertEqual(
                contract["endpoints"],
                {
                    "health": "/api/health/",
                    "auth": "/api/auth/",
                    "auth_login": "/api/auth/login/",
                    "auth_refresh": "/api/auth/refresh/",
                    "auth_me": "/api/auth/me/",
                    "events": "/api/events/",
                    "events_intake": "/api/events/intake/",
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
                },
            )
            self.assertEqual(contract["auth"], build_auth_contract())
            self.assertEqual(contract["events"], build_events_contract())
            self.assertEqual(contract["ai"], build_ai_contract())
            self.assertEqual(contract["dashboard"], build_dashboard_contract())
            self.assertEqual(
                contract["response_engine"],
                {
                    "routes": {"list_create": "/api/responses/"},
                    "policy": {
                        "rule": "risk-context-containment-v1",
                        "trigger_levels": ["high", "critical"],
                        "simulation_only": True,
                        "destructive_operations": False,
                        "action_types": [
                            "alert",
                            "notify_admin",
                            "isolate_host",
                            "block_ip",
                            "limit_traffic",
                            "cut_lateral_communication",
                            "mark_host_compromised",
                            "suspend_user",
                        ],
                    },
                    "audit": {
                        "evidence_model": "Evidence",
                        "timeline_model": "IncidentTimelineEntry",
                        "recording": "automatic",
                    },
                },
            )

    def test_events_contract_exposes_ingestion_route_and_permissions(self):
        self.assertEqual(
            build_events_contract(),
            {
                "routes": {
                    "list_create": "/api/events/",
                    "intake": "/api/events/intake/",
                },
                "permissions": {
                    "list": "authenticated",
                    "create": "operator_or_admin",
                },
                "ingested_by": "request.user.username",
                "intake": {
                    "payloads": ["single_row", "rows_list"],
                    "row_fields": [
                        "source_ip",
                        "destination_ip",
                        "protocol",
                        "destination_port",
                        "payload",
                        "metadata",
                    ],
                    "normalization": {
                        "protocol": "trimmed_and_uppercased",
                        "destination_port": "coerced_from_string_or_int",
                        "payload": "trimmed",
                        "metadata": "blank_to_empty_object",
                    },
                },
            },
        )

    def test_detection_contract_exposes_ml_only_training_and_simulation_surface(self):
        self.assertEqual(
            build_api_contract()["detection"],
            {
                "routes": {
                    "train": "/api/detection/train/",
                    "simulate": "/api/detection/simulate/",
                    "incidents": "/api/incidents/",
                },
                "model": {
                    "engine": ENGINE_VERSION,
                    "minimum_training_rows": MIN_TRAINING_ROWS,
                    "heuristics": False,
                },
                "risk_scale": RISK_SCALE,
                "alerting": {
                    "container": "Incident",
                    "trigger_levels": ["high", "critical"],
                    "update_strategy": "upsert_by_source_event_or_detection",
                },
                "readiness": {
                    "insufficient_rows_status": 409,
                    "fallback": "none",
                },
            },
        )

    def test_ai_contract_exposes_local_first_threat_family_and_text_generation_routes(self):
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
            self.assertEqual(
                build_ai_contract(),
                {
                    "routes": {
                        "root": "/api/ai/",
                        "classify_threat_family": "/api/ai/classify/",
                        "explain_alert": "/api/ai/explain/",
                        "summarize_incident": "/api/ai/summarize/",
                        "generate_report": "/api/ai/report/",
                    },
                    "model": {
                        "engine": "local-tfidf-logreg-v1",
                        "fallback": "deterministic_templates",
                        "heuristics": False,
                        "families": [
                            "ddos",
                            "worms",
                            "trojans",
                            "ransomware",
                            "exfiltration",
                            "lateral_movement",
                        ],
                    },
                    "provider": {
                        "requested": "local",
                        "active": "local",
                        "fallback": "local",
                        "azure_openai": {
                            "endpoint": "",
                            "project_endpoint": "",
                            "project": "",
                            "deployment": "",
                            "api_version": "2024-02-15-preview",
                            "has_credentials": False,
                            "ready": False,
                        },
                    },
                },
            )

    def test_api_root_returns_the_shared_contract(self):
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
            response = self.client.get(reverse("api-root"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), build_api_contract())

    def test_health_check_returns_ok_status(self):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
