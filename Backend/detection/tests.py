from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from events.models import TrafficEvent
from core.views import build_api_contract

from .model_service import ENGINE_VERSION, MIN_TRAINING_ROWS, MODEL_PATH


User = get_user_model()


class DetectionRuntimeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.group, _ = Group.objects.get_or_create(name="analyst")
        self.user = User.objects.create_user(
            username="analyst-demo",
            email="analyst@cybershield.local",
            password="CyberShield123!",
            is_staff=True,
        )
        self.user.groups.add(self.group)
        MODEL_PATH.unlink(missing_ok=True)

    def tearDown(self):
        MODEL_PATH.unlink(missing_ok=True)

    def authenticate(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": self.user.username, "password": "CyberShield123!"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.json()['access']}")

    def test_core_discovery_exposes_the_detection_ml_only_contract(self):
        response = self.client.get(reverse("api-root"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["detection"], build_api_contract()["detection"])

    def test_train_and_simulate_follow_the_ml_contract_without_heuristics(self):
        for index in range(MIN_TRAINING_ROWS):
            TrafficEvent.objects.create(
                source_ip=f"10.0.0.{index + 1}",
                destination_ip=f"10.0.1.{index + 1}",
                protocol="tcp" if index % 2 else "udp",
                destination_port=443 if index % 2 else 53,
                payload=f"sample payload {index}",
                metadata={"index": index},
                ingested_by=self.user.username,
            )

        self.authenticate()

        train_response = self.client.post(reverse("detection-train"), {}, format="json")

        self.assertEqual(train_response.status_code, 200)
        self.assertEqual(train_response.json()["engine_version"], ENGINE_VERSION)
        self.assertEqual(train_response.json()["training_rows"], MIN_TRAINING_ROWS)
        self.assertTrue(train_response.json()["model_path"].endswith("anomaly_model.joblib"))

        simulate_response = self.client.post(
            reverse("detection-simulate"),
            {
                "payload": {
                    "source_ip": "10.0.0.50",
                    "destination_ip": "10.0.1.50",
                    "protocol": "tcp",
                    "destination_port": 443,
                    "payload": "ALERT 4242 payload",
                    "metadata": {"flag": True},
                }
            },
            format="json",
        )

        self.assertEqual(simulate_response.status_code, 201)
        self.assertEqual(simulate_response.json()["engine_version"], ENGINE_VERSION)
        self.assertIn(simulate_response.json()["label"], {"low_risk", "medium_risk", "high_risk"})
        self.assertIn("IsolationForest", simulate_response.json()["reason"])

    def test_simulate_returns_readiness_details_when_model_is_not_trained(self):
        self.authenticate()

        response = self.client.post(
            reverse("detection-simulate"),
            {
                "payload": {
                    "source_ip": "192.168.0.10",
                    "destination_ip": "192.168.0.20",
                    "protocol": "udp",
                    "destination_port": 53,
                    "payload": "dns query",
                    "metadata": {},
                }
            },
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json(),
            {
                "detail": response.json()["detail"],
                "required_rows": MIN_TRAINING_ROWS,
                "available_rows": 0,
                "train_endpoint": "/api/detection/train/",
            },
        )
