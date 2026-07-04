from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

from events.models import TrafficEvent
from core.views import build_api_contract
from incidents.models import Incident

from .model_service import ENGINE_VERSION, MIN_TRAINING_ROWS, MODEL_PATH
from .risk import classify_detection_risk


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
        self.assertIn(simulate_response.json()["label"], {"low", "medium", "high", "critical"})
        self.assertIn("family=", simulate_response.json()["reason"])

    def test_risk_mapping_uses_score_and_event_characteristics(self):
        self.assertEqual(
            classify_detection_risk(
                decision_score=0.11,
                risk_score=0.2,
                feature_summary={"protocol": "TCP", "destination_port": 9000, "payload_length": 8, "same_private_class": False, "same_subnet_24": False},
            )["risk_level"],
            "low",
        )
        self.assertEqual(
            classify_detection_risk(
                decision_score=0.21,
                risk_score=0.4,
                feature_summary={"protocol": "TCP", "destination_port": 9000, "payload_length": 18, "same_private_class": False, "same_subnet_24": False},
            )["risk_level"],
            "medium",
        )
        self.assertEqual(
            classify_detection_risk(
                decision_score=0.31,
                risk_score=0.48,
                feature_summary={"protocol": "TCP", "destination_port": 443, "payload_length": 18, "same_private_class": False, "same_subnet_24": False},
            )["risk_level"],
            "high",
        )
        self.assertEqual(
            classify_detection_risk(
                decision_score=0.41,
                risk_score=0.73,
                feature_summary={"protocol": "TCP", "destination_port": 443, "payload_length": 18, "same_private_class": True, "same_subnet_24": True},
            )["risk_level"],
            "critical",
        )

    def test_high_and_critical_results_create_and_update_incidents(self):
        event = TrafficEvent.objects.create(
            source_ip="10.0.0.1",
            destination_ip="10.0.0.2",
            protocol="tcp",
            destination_port=443,
            payload="test payload",
            metadata={"flag": True},
            ingested_by=self.user.username,
        )
        self.authenticate()

        high_result = {
            "score": 0.48,
            "label": "high",
            "risk_level": "high",
            "anomaly_family": "service_probe",
            "reason": "family=service_probe; ml_score=0.1234; normalized_risk=0.48; risk_level=high; protocol=TCP; destination_port=443; same_subnet_24=False",
            "is_high_risk": True,
            "engine_version": ENGINE_VERSION,
        }
        critical_result = {
            "score": 0.73,
            "label": "critical",
            "risk_level": "critical",
            "anomaly_family": "lateral_movement",
            "reason": "family=lateral_movement; ml_score=0.2234; normalized_risk=0.73; risk_level=critical; protocol=TCP; destination_port=443; same_subnet_24=True",
            "is_high_risk": True,
            "engine_version": ENGINE_VERSION,
        }

        with patch("detection.views.simulate_detection", return_value=high_result):
            response = self.client.post(reverse("detection-simulate"), {"event_id": event.id}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Incident.objects.count(), 1)
        incident = Incident.objects.get()
        self.assertEqual(incident.severity, Incident.Severity.HIGH)
        self.assertEqual(incident.source_event_id, event.id)
        self.assertIn("Service Probe", incident.title)

        with patch("detection.views.simulate_detection", return_value=critical_result):
            response = self.client.post(reverse("detection-simulate"), {"event_id": event.id}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Incident.objects.count(), 1)
        incident.refresh_from_db()
        self.assertEqual(incident.severity, Incident.Severity.CRITICAL)
        self.assertIn("Critical Risk", incident.title)

    def test_low_and_medium_risk_do_not_create_incidents(self):
        event = TrafficEvent.objects.create(
            source_ip="192.168.0.10",
            destination_ip="192.168.0.20",
            protocol="udp",
            destination_port=53,
            payload="dns query",
            metadata={},
            ingested_by=self.user.username,
        )
        self.authenticate()

        with patch(
            "detection.views.simulate_detection",
            return_value={
                "score": 0.2,
                "label": "low",
                "risk_level": "low",
                "anomaly_family": "network_anomaly",
                "reason": "family=network_anomaly; ml_score=0.0210; normalized_risk=0.20; risk_level=low; protocol=UDP; destination_port=53; same_subnet_24=False",
                "is_high_risk": False,
                "engine_version": ENGINE_VERSION,
            },
        ):
            low_response = self.client.post(reverse("detection-simulate"), {"event_id": event.id}, format="json")

        self.assertEqual(low_response.status_code, 201)
        self.assertEqual(Incident.objects.count(), 0)

        with patch(
            "detection.views.simulate_detection",
            return_value={
                "score": 0.4,
                "label": "medium",
                "risk_level": "medium",
                "anomaly_family": "protocol_anomaly",
                "reason": "family=protocol_anomaly; ml_score=0.0310; normalized_risk=0.40; risk_level=medium; protocol=GRE; destination_port=53; same_subnet_24=False",
                "is_high_risk": False,
                "engine_version": ENGINE_VERSION,
            },
        ):
            medium_response = self.client.post(reverse("detection-simulate"), {"event_id": event.id}, format="json")

        self.assertEqual(medium_response.status_code, 201)
        self.assertEqual(Incident.objects.count(), 0)

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
