from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver


ROLE_NAMES = ("admin", "analyst", "operator", "viewer")


@receiver(post_migrate)
def ensure_cybershield_roles(sender, **kwargs):
    for role_name in ROLE_NAMES:
        Group.objects.get_or_create(name=role_name)
