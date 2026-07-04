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
            "policy_rule",
            "decision_context",
            "status",
            "simulated",
            "control_mode",
            "executed_at",
        ]
        read_only_fields = ["id", "policy_rule", "decision_context", "status", "simulated", "control_mode", "executed_at"]
