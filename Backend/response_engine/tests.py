from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from incidents.models import Incident

from .models import ResponseAction


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
