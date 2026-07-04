from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from datetime import timedelta

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
        now = timezone.now()
        event_one = TrafficEvent.objects.create(
            source_ip="10.0.0.1",
            destination_ip="10.0.0.2",
            protocol="tcp",
            destination_port=443,
            payload="alpha",
            metadata={"sample": 1},
            ingested_by=self.user.username,
        )
        TrafficEvent.objects.filter(pk=event_one.pk).update(created_at=now - timedelta(minutes=10))
        event_two = TrafficEvent.objects.create(
            source_ip="10.0.0.3",
            destination_ip="10.0.0.4",
            protocol="udp",
            destination_port=53,
            payload="beta",
            metadata={"sample": 2},
            ingested_by=self.user.username,
        )
        TrafficEvent.objects.filter(pk=event_two.pk).update(created_at=now - timedelta(minutes=20))
        detection_one = DetectionResult.objects.create(
            event=event_one,
            score=0.91,
            label="high_risk",
            reason="High-risk signal.",
            is_high_risk=True,
            payload_snapshot={"sample": 1},
            engine_version="ml-isoforest-v1",
        )
        DetectionResult.objects.filter(pk=detection_one.pk).update(created_at=now - timedelta(minutes=8))
        detection_two = DetectionResult.objects.create(
            event=event_two,
            score=0.22,
            label="low_risk",
            reason="Routine traffic.",
            is_high_risk=False,
            payload_snapshot={"sample": 2},
            engine_version="ml-isoforest-v1",
        )
        DetectionResult.objects.filter(pk=detection_two.pk).update(created_at=now - timedelta(minutes=15))
        incident_open = Incident.objects.create(
            title="Open incident",
            severity=Incident.Severity.HIGH,
            status=Incident.Status.OPEN,
            source_event=event_one,
            detection=detection_one,
        )
        Incident.objects.filter(pk=incident_open.pk).update(created_at=now - timedelta(minutes=7), updated_at=now - timedelta(minutes=5))
        incident_contained = Incident.objects.create(
            title="Contained incident",
            severity=Incident.Severity.CRITICAL,
            status=Incident.Status.CONTAINED,
            source_event=event_two,
        )
        Incident.objects.filter(pk=incident_contained.pk).update(created_at=now - timedelta(minutes=14), updated_at=now - timedelta(minutes=12))
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
        action_one = ResponseAction.objects.create(
            incident=incident_open,
            action_type=ResponseAction.ActionType.ISOLATE_HOST,
            target_value="host-a",
            notes="Isolate host A.",
        )
        ResponseAction.objects.filter(pk=action_one.pk).update(executed_at=now - timedelta(minutes=6))
        action_two = ResponseAction.objects.create(
            incident=incident_contained,
            action_type=ResponseAction.ActionType.ISOLATE_HOST,
            target_value="host-a",
            notes="Duplicate isolated host for distinct count coverage.",
        )
        ResponseAction.objects.filter(pk=action_two.pk).update(executed_at=now - timedelta(minutes=13))
        action_three = ResponseAction.objects.create(
            incident=incident_open,
            action_type=ResponseAction.ActionType.ALERT,
            target_value="",
            notes="Notify SOC.",
        )
        ResponseAction.objects.filter(pk=action_three.pk).update(executed_at=now - timedelta(minutes=4))
        self.authenticate()

        response = self.client.get(reverse("dashboard-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["events_total"], 2)
        self.assertEqual(response.json()["events_analyzed_total"], 2)
        self.assertEqual(response.json()["high_risk_detections"], 1)
        self.assertEqual(response.json()["active_alerts_total"], 1)
        self.assertEqual(response.json()["open_incidents"], 1)
        self.assertEqual(response.json()["suspicious_hosts_total"], 1)
        self.assertEqual(response.json()["isolated_hosts_total"], 1)
        self.assertEqual(response.json()["response_actions_total"], 3)
        self.assertEqual(response.json()["evidence_total"], 2)
        self.assertEqual(response.json()["high_risk_detection_rate"], 0.5)
        self.assertEqual(response.json()["detection_latency_seconds"], {"average_seconds": 210.0, "latest_seconds": 120.0, "samples": 2})
        self.assertEqual(response.json()["response_latency_seconds"], {"average_seconds": 60.0, "latest_seconds": 60.0, "samples": 2})
        self.assertEqual(
            response.json()["action_counts_by_type"],
            [
                {"action_type": ResponseAction.ActionType.ALERT, "count": 1},
                {"action_type": ResponseAction.ActionType.ISOLATE_HOST, "count": 2},
            ],
        )
        self.assertEqual(response.json()["suspicious_hosts"], [
            {"host": "10.0.0.1", "detection_count": 1, "latest_detection_at": (now - timedelta(minutes=8)).isoformat()},
        ])
        self.assertEqual(response.json()["isolated_hosts"], [
            {"host": "host-a", "action_count": 2, "latest_action_at": (now - timedelta(minutes=6)).isoformat()},
        ])
        self.assertEqual(response.json()["incident_history"][0]["id"], incident_open.id)
        self.assertEqual(response.json()["incident_history"][0]["detection_latency_seconds"], 120.0)
        self.assertEqual(response.json()["incident_history"][0]["response_latency_seconds"], 60.0)
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
        self.assertEqual(response.json()["workflow"]["analysis"]["events_analyzed_total"], 2)
        self.assertEqual(response.json()["workflow"]["response"]["isolated_hosts"][0]["host"], "host-a")
        self.assertEqual(response.json()["workflow"]["history"]["evidence_total"], 2)
        self.assertEqual(response.json()["model_quality"]["training_status"], "trained")
        self.assertEqual(response.json()["model_quality"]["training_rows"], 2)
        self.assertEqual(response.json()["model_quality"]["trained_at"], (now - timedelta(minutes=8)).isoformat())
        self.assertEqual(response.json()["model_quality"]["engine_version"], "ml-isoforest-v1")

    def test_dashboard_summary_returns_zero_metrics_when_there_is_no_data(self):
        self.authenticate()

        response = self.client.get(reverse("dashboard-summary"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "events_total": 0,
                "events_analyzed_total": 0,
                "high_risk_detections": 0,
                "high_risk_detection_rate": 0.0,
                "active_alerts_total": 0,
                "open_incidents": 0,
                "suspicious_hosts_total": 0,
                "isolated_hosts_total": 0,
                "response_actions_total": 0,
                "evidence_total": 0,
                "incident_counts_by_status": [],
                "incident_counts_by_severity": [],
                "action_counts_by_type": [],
                "detection_latency_seconds": {"average_seconds": None, "latest_seconds": None, "samples": 0},
                "response_latency_seconds": {"average_seconds": None, "latest_seconds": None, "samples": 0},
                "suspicious_hosts": [],
                "isolated_hosts": [],
                "incident_history": [],
                "model_quality": {
                    "engine_version": "ml-isoforest-v1",
                    "latest_detection_engine_version": "ml-isoforest-v1",
                    "training_status": "insufficient_rows",
                    "training_rows": 0,
                    "trained_at": None,
                    "minimum_training_rows": 20,
                    "high_risk_detection_rate": 0.0,
                },
                "workflow": {
                    "analysis": {
                        "events_total": 0,
                        "events_analyzed_total": 0,
                        "high_risk_detections": 0,
                        "high_risk_detection_rate": 0.0,
                        "suspicious_hosts": [],
                        "detection_latency_seconds": {"average_seconds": None, "latest_seconds": None, "samples": 0},
                    },
                    "response": {
                        "active_alerts_total": 0,
                        "open_incidents": 0,
                        "isolated_hosts": [],
                        "action_counts_by_type": [],
                        "response_latency_seconds": {"average_seconds": None, "latest_seconds": None, "samples": 0},
                    },
                    "history": {
                        "incident_counts_by_status": [],
                        "incident_counts_by_severity": [],
                        "incident_history": [],
                        "evidence_total": 0,
                    },
                    "model": {
                        "engine_version": "ml-isoforest-v1",
                        "latest_detection_engine_version": "ml-isoforest-v1",
                        "training_status": "insufficient_rows",
                        "training_rows": 0,
                        "trained_at": None,
                        "minimum_training_rows": 20,
                        "high_risk_detection_rate": 0.0,
                    },
                },
            },
        )
