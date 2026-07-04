from __future__ import annotations

from typing import Any

from django.db import transaction
from rest_framework import serializers

from detection.model_service import DetectionModelNotReady, ensure_bundle
from detection.services import process_traffic_event_detection

from .models import TrafficEvent
from .serializers import TrafficEventIngestionRowSerializer


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def extract_dataset_rows(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        if "rows" in payload:
            rows = payload["rows"]
            if not isinstance(rows, list):
                raise serializers.ValidationError({"rows": "Rows must be a list of objects."})

            return rows

        return [payload]

    raise serializers.ValidationError("Dataset payload must be a JSON object or a list of rows.")


def normalize_traffic_event_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise serializers.ValidationError("Each dataset row must be a JSON object.")

    normalized = dict(row)

    for key in ("source_ip", "destination_ip", "protocol"):
        value = normalized.get(key)
        if isinstance(value, str):
            normalized[key] = value.strip().upper() if key == "protocol" else value.strip()

    destination_port = normalized.get("destination_port")
    if _is_blank(destination_port):
        normalized["destination_port"] = None
    elif isinstance(destination_port, str):
        stripped_port = destination_port.strip()
        try:
            normalized["destination_port"] = int(stripped_port)
        except ValueError:
            normalized["destination_port"] = stripped_port

    payload = normalized.get("payload")
    if payload is None:
        normalized["payload"] = ""
    elif isinstance(payload, str):
        normalized["payload"] = payload.strip()
    else:
        normalized["payload"] = str(payload).strip()

    metadata = normalized.get("metadata")
    if _is_blank(metadata):
        normalized["metadata"] = {}

    return normalized


def ingest_traffic_events(payload: Any, ingested_by: str) -> list[TrafficEvent]:
    rows = extract_dataset_rows(payload)
    created_events: list[TrafficEvent] = []
    errors: list[dict[str, Any]] = []

    with transaction.atomic():
        for index, row in enumerate(rows):
            normalized_row = normalize_traffic_event_row(row)
            serializer = TrafficEventIngestionRowSerializer(data=normalized_row)
            if not serializer.is_valid():
                errors.append({"index": index, "errors": serializer.errors})
                continue

            created_events.append(TrafficEvent.objects.create(ingested_by=ingested_by, **serializer.validated_data))

        if errors:
            raise serializers.ValidationError({"rows": errors})

    return created_events


def ingest_traffic_events_with_detection(payload: Any, ingested_by: str) -> dict[str, Any]:
    created_events = ingest_traffic_events(payload, ingested_by)
    detection_results: list[dict[str, Any]] = []
    incident_ids: list[int] = []
    detection_status = "created"
    detection_message = None

    try:
        ensure_bundle()
    except DetectionModelNotReady as exc:
        detection_status = "pending"
        detection_message = str(exc)
        return {
            "events": created_events,
            "ingested_count": len(created_events),
            "detections_created_count": 0,
            "incidents_triggered_count": 0,
            "incident_ids": [],
            "detection_status": detection_status,
            "detection_message": detection_message,
        }

    with transaction.atomic():
        for event in created_events:
            outcome = process_traffic_event_detection(event)
            if outcome["status"] == "pending":
                detection_status = "pending"
                detection_message = outcome["reason"]
                continue

            detection_results.append(outcome)
            incident = outcome.get("incident")
            if incident is not None:
                incident_ids.append(incident.id)

    return {
        "events": created_events,
        "ingested_count": len(created_events),
        "detections_created_count": len(detection_results),
        "incidents_triggered_count": len(incident_ids),
        "incident_ids": incident_ids,
        "detection_status": detection_status,
        "detection_message": detection_message,
    }
