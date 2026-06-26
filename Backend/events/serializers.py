from rest_framework import serializers

from .models import TrafficEvent


class TrafficEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficEvent
        fields = [
            "id",
            "source_ip",
            "destination_ip",
            "protocol",
            "destination_port",
            "payload",
            "metadata",
            "ingested_by",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "ingested_by"]
