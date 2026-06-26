import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


User = get_user_model()


class Command(BaseCommand):
    help = "Create or update the local CyberShield demo user."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=os.getenv("DEMO_USERNAME", "demo"))
        parser.add_argument("--password", default=os.getenv("DEMO_PASSWORD", "CyberShield123!"))
        parser.add_argument("--email", default=os.getenv("DEMO_EMAIL", "demo@cybershield.local"))
        parser.add_argument("--group", default=os.getenv("DEMO_GROUP", "analyst"))
        parser.add_argument("--first-name", default=os.getenv("DEMO_FIRST_NAME", "Demo"))
        parser.add_argument("--last-name", default=os.getenv("DEMO_LAST_NAME", "Analyst"))
        parser.add_argument("--staff", action="store_true", default=os.getenv("DEMO_IS_STAFF", "1") == "1")
        parser.add_argument(
            "--superuser",
            action="store_true",
            default=os.getenv("DEMO_IS_SUPERUSER", "0") == "1",
        )

    def handle(self, *args, **options):
        username = options["username"].strip()
        password = options["password"]
        email = options["email"].strip()
        group_name = options["group"].strip()

        group, _ = Group.objects.get_or_create(name=group_name)

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": options["first_name"].strip(),
                "last_name": options["last_name"].strip(),
                "is_staff": bool(options["staff"]),
                "is_superuser": bool(options["superuser"]),
                "is_active": True,
            },
        )

        if user.email != email:
            user.email = email
        if user.first_name != options["first_name"]:
            user.first_name = options["first_name"]
        if user.last_name != options["last_name"]:
            user.last_name = options["last_name"]
        if user.is_staff != bool(options["staff"]):
            user.is_staff = bool(options["staff"])
        if user.is_superuser != bool(options["superuser"]):
            user.is_superuser = bool(options["superuser"])
        if not user.is_active:
            user.is_active = True

        user.set_password(password)
        user.save()
        user.groups.add(group)

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created demo user '{username}' in group '{group_name}'."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated demo user '{username}' in group '{group_name}'."))
