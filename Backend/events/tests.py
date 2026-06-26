from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APIClient

from .models import TrafficEvent


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
