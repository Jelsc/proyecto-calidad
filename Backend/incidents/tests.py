from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from detection.models import DetectionResult
from events.models import TrafficEvent

from .models import Incident


User = get_user_model()


class IncidentRuntimeTests(TestCase):
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

    def authenticate(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": self.user.username, "password": "CyberShield123!"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.json()['access']}")

    def test_incidents_list_returns_persisted_incidents_for_authenticated_users(self):
        event = TrafficEvent.objects.create(
            source_ip="10.0.0.1",
            destination_ip="10.0.0.2",
            protocol="tcp",
            destination_port=443,
            payload="hello",
            metadata={"sample": True},
            ingested_by=self.user.username,
        )
        detection = DetectionResult.objects.create(
            event=event,
            score=0.93,
            label="high_risk",
            reason="Anomalous traffic burst.",
            is_high_risk=True,
            payload_snapshot={"sample": True},
            engine_version="ml-isoforest-v1",
        )
        Incident.objects.create(
            title="Suspicious traffic burst",
            summary="Detected a burst of unusual traffic.",
            severity=Incident.Severity.HIGH,
            status=Incident.Status.INVESTIGATING,
            source_event=event,
            detection=detection,
            assigned_to="analyst-demo",
        )
        self.authenticate()

        response = self.client.get(reverse("incident-list-create"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], "Suspicious traffic burst")
        self.assertEqual(response.json()[0]["severity"], Incident.Severity.HIGH)
        self.assertEqual(response.json()[0]["status"], Incident.Status.INVESTIGATING)
        self.assertEqual(response.json()[0]["assigned_to"], "analyst-demo")

    def test_incident_create_persists_optional_source_links(self):
        event = TrafficEvent.objects.create(
            source_ip="192.168.0.10",
            destination_ip="192.168.0.20",
            protocol="udp",
            destination_port=53,
            payload="dns query",
            metadata={"tag": "test"},
            ingested_by=self.user.username,
        )
        detection = DetectionResult.objects.create(
            event=event,
            score=0.77,
            label="medium_risk",
            reason="Suspicious DNS volume.",
            is_high_risk=False,
            payload_snapshot={"tag": "test"},
            engine_version="ml-isoforest-v1",
        )
        self.authenticate()

        response = self.client.post(
            reverse("incident-list-create"),
            {
                "title": "Suspicious DNS activity",
                "summary": "Create an incident from the incoming telemetry.",
                "severity": Incident.Severity.CRITICAL,
                "source_event": event.id,
                "detection": detection.id,
                "assigned_to": "analyst-demo",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Incident.objects.count(), 1)
        incident = Incident.objects.get()
        self.assertEqual(incident.title, "Suspicious DNS activity")
        self.assertEqual(incident.source_event_id, event.id)
        self.assertEqual(incident.detection_id, detection.id)
        self.assertEqual(incident.severity, Incident.Severity.CRITICAL)
        self.assertEqual(incident.status, Incident.Status.OPEN)
