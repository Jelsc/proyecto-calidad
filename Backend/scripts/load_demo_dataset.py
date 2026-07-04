from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import django


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cybershield.settings")
    django.setup()

    from detection.model_service import train_from_events
    from detection.models import DetectionResult
    from detection.services import build_detection_payload, simulate_detection
    from events.models import TrafficEvent
    from events.services import ingest_traffic_events
    from incidents.models import Evidence, Incident, IncidentTimelineEntry
    from incidents.services import upsert_detection_incident
    from response_engine.models import ResponseAction

    dataset_path = Path(__file__).resolve().parents[1] / "demo-network-dataset.json"
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))

    ResponseAction.objects.all().delete()
    IncidentTimelineEntry.objects.all().delete()
    Evidence.objects.all().delete()
    Incident.objects.all().delete()
    DetectionResult.objects.all().delete()
    TrafficEvent.objects.all().delete()

    ingest_traffic_events(payload, "demo-seed")
    bundle = train_from_events()

    for event in TrafficEvent.objects.order_by("id"):
        payload = build_detection_payload({}, event)
        result = simulate_detection(payload)
        detection = DetectionResult.objects.create(
            event=event,
            payload_snapshot=payload,
            score=result["score"],
            label=result["label"],
            reason=result["reason"],
            is_high_risk=result["is_high_risk"],
            engine_version=result["engine_version"],
        )
        upsert_detection_incident(
            detection=detection,
            risk_level=result["risk_level"],
            anomaly_family=result["anomaly_family"],
            reason=result["reason"],
        )

    print(f"loaded_events={TrafficEvent.objects.count()}")
    print(f"detections={DetectionResult.objects.count()}")
    print(f"incidents={Incident.objects.count()}")
    print(f"evidence={Evidence.objects.count()}")
    print(f"timeline={IncidentTimelineEntry.objects.count()}")
    print(f"responses={ResponseAction.objects.count()}")
    print(f"trained_rows={bundle['training_rows']}")


if __name__ == "__main__":
    main()
