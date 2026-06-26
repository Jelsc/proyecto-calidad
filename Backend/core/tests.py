from django.test import SimpleTestCase
from django.urls import reverse

from detection.model_service import ENGINE_VERSION, MIN_TRAINING_ROWS

from .contracts import build_ai_contract, build_api_contract, build_auth_contract, build_events_contract


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

    def test_events_contract_exposes_ingestion_route_and_permissions(self):
        self.assertEqual(
            build_events_contract(),
            {
                "routes": {
                    "list_create": "/api/events/",
                },
                "permissions": {
                    "list": "authenticated",
                    "create": "operator_or_admin",
                },
                "ingested_by": "request.user.username",
            },
        )

    def test_detection_contract_exposes_ml_only_training_and_simulation_surface(self):
        self.assertEqual(
            build_api_contract()["detection"],
            {
                "routes": {
                    "train": "/api/detection/train/",
                    "simulate": "/api/detection/simulate/",
                },
                "model": {
                    "engine": ENGINE_VERSION,
                    "minimum_training_rows": MIN_TRAINING_ROWS,
                    "heuristics": False,
                },
                "readiness": {
                    "insufficient_rows_status": 409,
                    "fallback": "none",
                },
            },
        )

    def test_ai_contract_exposes_local_first_threat_family_and_text_generation_routes(self):
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
            },
        )

    def test_api_root_returns_the_shared_contract(self):
        response = self.client.get(reverse("api-root"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), build_api_contract())

    def test_health_check_returns_ok_status(self):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
