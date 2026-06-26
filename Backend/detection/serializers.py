from rest_framework import serializers

from .models import DetectionResult


class DetectionResultSerializer(serializers.ModelSerializer):
    event_id = serializers.SerializerMethodField()

    def get_event_id(self, obj):
        return obj.event_id

    class Meta:
        model = DetectionResult
        fields = [
            "id",
            "event_id",
            "score",
            "label",
            "reason",
            "is_high_risk",
            "payload_snapshot",
            "engine_version",
            "created_at",
        ]
