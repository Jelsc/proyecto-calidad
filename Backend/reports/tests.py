from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from detection.models import DetectionResult
from events.models import TrafficEvent
from incidents.models import Evidence, Incident
from response_engine.models import ResponseAction


User = get_user_model()


class DashboardSummaryRuntimeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.group, _ = Group.objects.get_or_create(name="analyst")
        self.user = User.objects.create_user(
            username="report-demo",
            email="report@cybershield.local",
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

    def test_dashboard_summary_aggregates_counts_and_high_risk_rate(self):
        event_one = TrafficEvent.objects.create(
            source_ip="10.0.0.1",
            destination_ip="10.0.0.2",
            protocol="tcp",
            destination_port=443,
            payload="alpha",
            metadata={"sample": 1},
            ingested_by=self.user.username,
        )
        event_two = TrafficEvent.objects.create(
            source_ip="10.0.0.3",
            destination_ip="10.0.0.4",
            protocol="udp",
            destination_port=53,
            payload="beta",
            metadata={"sample": 2},
            ingested_by=self.user.username,
        )
        detection_one = DetectionResult.objects.create(
            event=event_one,
            score=0.91,
            label="high_risk",
            reason="High-risk signal.",
            is_high_risk=True,
            payload_snapshot={"sample": 1},
            engine_version="ml-isoforest-v1",
        )
        DetectionResult.objects.create(
            event=event_two,
            score=0.22,
            label="low_risk",
            reason="Routine traffic.",
            is_high_risk=False,
            payload_snapshot={"sample": 2},
            engine_version="ml-isoforest-v1",
        )
        incident_open = Incident.objects.create(
            title="Open incident",
            severity=Incident.Severity.HIGH,
            status=Incident.Status.OPEN,
            source_event=event_one,
            detection=detection_one,
        )
        incident_contained = Incident.objects.create(
            title="Contained incident",
            severity=Incident.Severity.CRITICAL,
            status=Incident.Status.CONTAINED,
            source_event=event_two,
        )
        Evidence.objects.create(
            incident=incident_open,
            evidence_type="log",
            description="Firewall log entry.",
            source_ref="fw-1",
            payload={"evidence": True},
        )
        Evidence.objects.create(
            incident=incident_contained,
            evidence_type="packet",
            description="Packet capture.",
            source_ref="pcap-1",
            payload={"evidence": True},
        )
        ResponseAction.objects.create(
            incident=incident_open,
            action_type=ResponseAction.ActionType.ISOLATE_HOST,
            target_value="host-a",
            notes="Isolate host A.",
        )
        ResponseAction.objects.create(
            incident=incident_contained,
            action_type=ResponseAction.ActionType.ISOLATE_HOST,
            target_value="host-a",
            notes="Duplicate isolated host for distinct count coverage.",
        )
        ResponseAction.objects.create(
            incident=incident_open,
            action_type=ResponseAction.ActionType.ALERT,
            target_value="",
            notes="Notify SOC.",
        )
        self.authenticate()

        response = self.client.get(reverse("dashboard-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["events_total"], 2)
        self.assertEqual(response.json()["high_risk_detections"], 1)
        self.assertEqual(response.json()["open_incidents"], 1)
        self.assertEqual(response.json()["isolated_hosts"], 1)
        self.assertEqual(response.json()["response_actions_total"], 3)
        self.assertEqual(response.json()["evidence_total"], 2)
        self.assertEqual(response.json()["high_risk_detection_rate"], 0.5)
        self.assertEqual(
            response.json()["incident_counts_by_status"],
            [
                {"status": Incident.Status.CONTAINED, "count": 1},
                {"status": Incident.Status.OPEN, "count": 1},
            ],
        )
        self.assertEqual(
            response.json()["incident_counts_by_severity"],
            [
                {"severity": Incident.Severity.CRITICAL, "count": 1},
                {"severity": Incident.Severity.HIGH, "count": 1},
            ],
        )

    def test_dashboard_summary_returns_zero_metrics_when_there_is_no_data(self):
        self.authenticate()

        response = self.client.get(reverse("dashboard-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "events_total": 0,
                "high_risk_detections": 0,
                "open_incidents": 0,
                "isolated_hosts": 0,
                "response_actions_total": 0,
                "evidence_total": 0,
                "incident_counts_by_status": [],
                "incident_counts_by_severity": [],
                "high_risk_detection_rate": 0.0,
            },
        )
