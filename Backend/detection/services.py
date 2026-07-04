from __future__ import annotations

from typing import Any

from events.models import TrafficEvent
from incidents.services import upsert_detection_incident

from .model_service import DetectionModelNotReady, predict
from .models import DetectionResult


def build_detection_payload(request_data: dict, event: TrafficEvent | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}

    if event is not None:
        payload.update(
            {
                "source_ip": event.source_ip,
                "destination_ip": event.destination_ip,
                "protocol": event.protocol,
                "destination_port": event.destination_port,
                "payload": event.payload,
                "metadata": event.metadata or {},
            }
        )

    request_payload = request_data.get("payload")
    if isinstance(request_payload, dict):
        payload.update(request_payload)

    if not payload:
        payload = {
            key: value
            for key, value in request_data.items()
            if key not in {"event_id", "payload"}
        }

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        payload["metadata"] = {}

    return payload


def simulate_detection(payload: dict) -> dict:
    return predict(payload)


def process_traffic_event_detection(event: TrafficEvent | None, request_data: dict | None = None) -> dict[str, Any]:
    payload = build_detection_payload(request_data or {}, event)

    try:
        result_data = simulate_detection(payload)
    except DetectionModelNotReady as exc:
        return {
            "status": "pending",
            "reason": str(exc),
            "payload": payload,
            "detection": None,
            "incident": None,
        }

    detection = DetectionResult.objects.create(
        event=event,
        payload_snapshot=payload,
        score=result_data["score"],
        label=result_data["label"],
        reason=result_data["reason"],
        is_high_risk=result_data["is_high_risk"],
        engine_version=result_data["engine_version"],
    )

    incident = upsert_detection_incident(
        detection=detection,
        risk_level=result_data["risk_level"],
        anomaly_family=result_data["anomaly_family"],
        reason=result_data["reason"],
    )

    return {
        "status": "created",
        "reason": result_data["reason"],
        "payload": payload,
        "detection": detection,
        "incident": incident,
        "result": result_data,
    }
