from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework.test import APIClient


User = get_user_model()


class AuthRuntimeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.group, _ = Group.objects.get_or_create(name="analyst")
        self.user = User.objects.create_user(
            username="demo",
            email="demo@cybershield.local",
            password="CyberShield123!",
            first_name="Demo",
            last_name="Analyst",
            is_staff=True,
        )
        self.user.groups.add(self.group)

    def test_login_returns_tokens_for_valid_credentials(self):
        response = self.client.post(
            reverse("auth-login"),
            {"username": "demo", "password": "CyberShield123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_me_returns_current_user_identity_contract(self):
        login_response = self.client.post(
            reverse("auth-login"),
            {"username": "demo", "password": "CyberShield123!"},
            format="json",
        )
        access_token = login_response.json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        response = self.client.get(reverse("auth-me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "id": self.user.id,
                "username": "demo",
                "first_name": "Demo",
                "last_name": "Analyst",
                "email": "demo@cybershield.local",
                "is_staff": True,
                "is_superuser": False,
                "roles": ["analyst"],
            },
        )
