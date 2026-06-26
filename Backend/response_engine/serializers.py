from rest_framework import serializers

from .models import ResponseAction


class ResponseActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseAction
        fields = [
            "id",
            "incident",
            "action_type",
            "target_value",
            "notes",
            "status",
            "simulated",
            "control_mode",
            "executed_at",
        ]
        read_only_fields = ["id", "status", "simulated", "control_mode", "executed_at"]
