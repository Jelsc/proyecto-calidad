from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class CurrentUserSerializer(serializers.ModelSerializer):
    roles = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name", source="groups")

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_superuser",
            "roles",
        ]
