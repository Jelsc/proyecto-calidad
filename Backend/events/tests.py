from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch
from types import SimpleNamespace

from .models import TrafficEvent
from detection.model_service import DetectionModelNotReady
from .services import normalize_traffic_event_row


User = get_user_model()


class EventRuntimeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.group, _ = Group.objects.get_or_create(name="operator")
        self.user = User.objects.create_user(
            username="operator-demo",
            email="operator@cybershield.local",
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

    def test_events_list_is_accessible_to_authenticated_users(self):
        TrafficEvent.objects.create(
            source_ip="10.0.0.1",
            destination_ip="10.0.0.2",
            protocol="tcp",
            destination_port=443,
            payload="hello",
            metadata={"sample": True},
            ingested_by="operator-demo",
        )
        self.authenticate()

        response = self.client.get(reverse("event-list-create"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["ingested_by"], "operator-demo")

    def test_events_create_persists_payload_and_ingested_by(self):
        self.authenticate()

        response = self.client.post(
            reverse("event-list-create"),
            {
                "source_ip": "192.168.1.10",
                "destination_ip": "192.168.1.11",
                "protocol": "udp",
                "destination_port": 53,
                "payload": "dns-query",
                "metadata": {"severity": "low"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(TrafficEvent.objects.count(), 1)
        event = TrafficEvent.objects.get()
        self.assertEqual(event.source_ip, "192.168.1.10")
        self.assertEqual(event.ingested_by, "operator-demo")


class EventIntakeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.group, _ = Group.objects.get_or_create(name="operator")
        self.user = User.objects.create_user(
            username="operator-batch",
            email="operator-batch@cybershield.local",
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

    def test_dataset_row_normalization_coerces_common_forms(self):
        normalized = normalize_traffic_event_row(
            {
                "source_ip": " 10.0.0.1 ",
                "destination_ip": " 10.0.0.2 ",
                "protocol": " tcp ",
                "destination_port": " 443 ",
                "payload": "  hello world  ",
                "metadata": "",
            }
        )

        self.assertEqual(
            normalized,
            {
                "source_ip": "10.0.0.1",
                "destination_ip": "10.0.0.2",
                "protocol": "TCP",
                "destination_port": 443,
                "payload": "hello world",
                "metadata": {},
            },
        )

    def test_dataset_intake_rejects_invalid_rows_without_persisting(self):
        self.authenticate()

        response = self.client.post(
            reverse("event-intake"),
            {
                "rows": [
                    {
                        "source_ip": "192.168.1.20",
                        "destination_ip": "192.168.1.21",
                        "protocol": "udp",
                        "destination_port": "53",
                        "payload": "dns",
                        "metadata": {},
                    },
                    {
                        "source_ip": "invalid-ip",
                        "destination_ip": "192.168.1.22",
                        "protocol": "tcp",
                        "destination_port": "abc",
                        "payload": "bad-row",
                        "metadata": {},
                    },
                ]
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(TrafficEvent.objects.count(), 0)
        self.assertEqual(response.json()["rows"][0]["index"], 1)

    def test_dataset_intake_creates_multiple_events_detects_and_reports_counts(self):
        self.authenticate()

        with patch("events.services.ensure_bundle", return_value={"model": object()}), patch(
            "events.services.process_traffic_event_detection",
            side_effect=[
                {
                    "status": "created",
                    "detection": object(),
                    "incident": SimpleNamespace(id=17),
                    "reason": "family=service_probe",
                },
                {
                    "status": "created",
                    "detection": object(),
                    "incident": None,
                    "reason": "family=network_anomaly",
                },
            ],
        ):
            response = self.client.post(
                reverse("event-intake"),
                {
                    "rows": [
                        {
                            "source_ip": "192.168.1.30",
                            "destination_ip": "192.168.1.31",
                            "protocol": "tcp",
                            "destination_port": "443",
                            "payload": "  tls handshake  ",
                            "metadata": {"severity": "high"},
                        },
                        {
                            "source_ip": "192.168.1.32",
                            "destination_ip": "192.168.1.33",
                            "protocol": "udp",
                            "destination_port": 53,
                            "payload": "dns-query",
                            "metadata": {},
                        },
                    ]
                },
                format="json",
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["ingested_count"], 2)
        self.assertEqual(response.json()["detections_created_count"], 2)
        self.assertEqual(response.json()["incidents_triggered_count"], 1)
        self.assertEqual(response.json()["incident_ids"], [17])
        self.assertEqual(TrafficEvent.objects.count(), 2)
        created = TrafficEvent.objects.order_by("source_ip")
        self.assertEqual(created[0].protocol, "TCP")
        self.assertEqual(created[0].destination_port, 443)
        self.assertEqual(created[0].payload, "tls handshake")
        self.assertEqual(created[0].ingested_by, "operator-batch")

    def test_dataset_intake_reports_pending_when_detection_is_unavailable(self):
        self.authenticate()

        with patch("events.services.ensure_bundle", side_effect=DetectionModelNotReady("model is not ready")):
            response = self.client.post(
                reverse("event-intake"),
                {
                    "source_ip": "192.168.1.40",
                    "destination_ip": "192.168.1.41",
                    "protocol": "tcp",
                    "destination_port": 443,
                    "payload": "tls handshake",
                    "metadata": {"severity": "high"},
                },
                format="json",
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["ingested_count"], 1)
        self.assertEqual(response.json()["detections_created_count"], 0)
        self.assertEqual(response.json()["incidents_triggered_count"], 0)
        self.assertEqual(response.json()["detection_status"], "pending")
        self.assertEqual(response.json()["detection_message"], "model is not ready")
