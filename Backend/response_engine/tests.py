from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import Mock

from detection.models import DetectionResult
from events.models import TrafficEvent
from incidents.models import Evidence, Incident, IncidentTimelineEntry

from .models import ResponseAction
from .services import apply_controlled_response_policy, select_response_actions


User = get_user_model()


class ResponseActionRuntimeTests(TestCase):
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
        self.incident = Incident.objects.create(title="Suspicious login")

    def authenticate(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": self.user.username, "password": "CyberShield123!"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.json()['access']}")

    def test_response_actions_list_returns_simulated_actions_for_authenticated_users(self):
        ResponseAction.objects.create(
            incident=self.incident,
            action_type=ResponseAction.ActionType.ISOLATE_HOST,
            target_value="host-1",
            notes="Isolate the affected workstation.",
        )
        self.authenticate()

        response = self.client.get(reverse("response-action-list-create"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["incident"], self.incident.id)
        self.assertEqual(response.json()[0]["status"], ResponseAction.Status.SIMULATED)
        self.assertTrue(response.json()[0]["simulated"])
        self.assertEqual(response.json()[0]["control_mode"], "controlled")

    def test_response_actions_create_forces_simulated_controlled_defaults(self):
        self.authenticate()

        response = self.client.post(
            reverse("response-action-list-create"),
            {
                "incident": self.incident.id,
                "action_type": ResponseAction.ActionType.BLOCK_IP,
                "target_value": "203.0.113.10",
                "notes": "Block the hostile address.",
                "status": ResponseAction.Status.EXECUTED,
                "simulated": False,
                "control_mode": "manual",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ResponseAction.objects.count(), 1)
        action = ResponseAction.objects.get()
        self.assertEqual(action.status, ResponseAction.Status.SIMULATED)
        self.assertTrue(action.simulated)
        self.assertEqual(action.control_mode, "controlled")
        self.assertEqual(response.json()["status"], ResponseAction.Status.SIMULATED)
        self.assertTrue(response.json()["simulated"])
        self.assertEqual(response.json()["control_mode"], "controlled")

    def test_policy_selection_uses_risk_and_anomaly_context(self):
        context = {
            "source_ip": "10.0.0.10",
            "destination_ip": "10.0.0.11",
            "destination_port": 445,
            "source_private": True,
            "destination_private": True,
            "same_subnet_24": True,
        }

        actions = select_response_actions(risk_level=Incident.Severity.CRITICAL, anomaly_family="lateral_movement", context=context)

        self.assertEqual(
            [action.action_type for action in actions],
            [
                ResponseAction.ActionType.ISOLATE_HOST,
                ResponseAction.ActionType.MARK_HOST_COMPROMISED,
                ResponseAction.ActionType.CUT_LATERAL_COMMUNICATION,
                ResponseAction.ActionType.LIMIT_TRAFFIC,
                ResponseAction.ActionType.BLOCK_IP,
                ResponseAction.ActionType.NOTIFY_ADMIN,
            ],
        )

    def test_policy_execution_records_audit_and_stays_simulated(self):
        event = TrafficEvent.objects.create(
            source_ip="10.0.0.50",
            destination_ip="10.0.0.51",
            protocol="tcp",
            destination_port=445,
            payload="lateral traffic",
            metadata={"flag": True},
            ingested_by=self.user.username,
        )
        detection = DetectionResult.objects.create(
            event=event,
            score=0.96,
            label="critical",
            reason="family=lateral_movement; ml_score=0.9900; normalized_risk=0.96; risk_level=critical; protocol=TCP; destination_port=445; same_subnet_24=True",
            is_high_risk=True,
            payload_snapshot={"flag": True},
            engine_version="ml-isoforest-v1",
        )

        result = apply_controlled_response_policy(
            incident=self.incident,
            detection=detection,
            risk_level=Incident.Severity.CRITICAL,
            anomaly_family="lateral_movement",
            reason=detection.reason,
            network_executor=Mock(),
        )

        self.assertEqual(ResponseAction.objects.count(), 6)
        self.assertEqual(Evidence.objects.count(), 7)
        self.assertEqual(IncidentTimelineEntry.objects.count(), 7)
        self.assertEqual(len(result["actions"]), 6)
        self.assertTrue(all(action.simulated for action in result["actions"]))
        self.assertTrue(all(action.status == ResponseAction.Status.SIMULATED for action in result["actions"]))
        self.assertEqual(result["actions"][0].policy_rule, "risk-context-containment-v1")
        result_executor = Mock()
        apply_controlled_response_policy(
            incident=self.incident,
            detection=detection,
            risk_level=Incident.Severity.CRITICAL,
            anomaly_family="lateral_movement",
            reason=detection.reason,
            network_executor=result_executor,
        )
        result_executor.assert_not_called()
