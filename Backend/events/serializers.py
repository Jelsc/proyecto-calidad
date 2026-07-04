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


class TrafficEventIngestionRowSerializer(serializers.Serializer):
    source_ip = serializers.CharField(max_length=45)
    destination_ip = serializers.CharField(max_length=45)
    protocol = serializers.CharField(max_length=16)
    destination_port = serializers.IntegerField(required=False, allow_null=True)
    payload = serializers.CharField(required=False, allow_blank=True, allow_null=True, default="")
    metadata = serializers.DictField(required=False, default=dict)

    def validate_source_ip(self, value: str) -> str:
        return value.strip()

    def validate_destination_ip(self, value: str) -> str:
        return value.strip()

    def validate_protocol(self, value: str) -> str:
        return value.strip().upper()

    def validate_destination_port(self, value: int | None) -> int | None:
        if value is None:
            return None

        if value <= 0:
            raise serializers.ValidationError("Destination port must be a positive integer.")

        return value

    def validate_payload(self, value: str | None) -> str:
        if value is None:
            return ""

        return value.strip()

    def validate_metadata(self, value: dict) -> dict:
        if value in (None, ""):
            return {}

        return value
