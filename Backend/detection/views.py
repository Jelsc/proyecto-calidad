from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAnalystOrAdmin
from events.models import TrafficEvent
from incidents.services import upsert_detection_incident

from .models import DetectionResult
from .serializers import DetectionResultSerializer
from .model_service import ENGINE_VERSION, DetectionModelNotReady, MIN_TRAINING_ROWS, train_from_events
from .risk import RISK_SCALE
from .services import build_detection_payload, simulate_detection


def build_detection_contract() -> dict:
    return {
        "routes": {
            "train": "/api/detection/train/",
            "simulate": "/api/detection/simulate/",
            "incidents": "/api/incidents/",
        },
        "model": {
            "engine": ENGINE_VERSION,
            "minimum_training_rows": MIN_TRAINING_ROWS,
            "heuristics": False,
        },
        "risk_scale": RISK_SCALE,
        "alerting": {
            "container": "Incident",
            "trigger_levels": ["high", "critical"],
            "update_strategy": "upsert_by_source_event_or_detection",
        },
        "readiness": {
            "insufficient_rows_status": status.HTTP_409_CONFLICT,
            "fallback": "none",
        },
    }


class DetectionSimulationView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated(), IsAnalystOrAdmin()]

    def post(self, request):
        event = None

        event_id = request.data.get("event_id")
        if event_id:
            event = TrafficEvent.objects.filter(pk=event_id).first()
            if event is None:
                return Response({"detail": "Event not found."}, status=status.HTTP_404_NOT_FOUND)

        payload = build_detection_payload(request.data, event)

        try:
            result_data = simulate_detection(payload)
        except DetectionModelNotReady as exc:
            return Response(
                {
                    "detail": str(exc),
                    "required_rows": MIN_TRAINING_ROWS,
                    "available_rows": TrafficEvent.objects.count(),
                    "train_endpoint": "/api/detection/train/",
                },
                status=status.HTTP_409_CONFLICT,
            )

        result = DetectionResult.objects.create(
            event=event,
            payload_snapshot=payload,
            score=result_data["score"],
            label=result_data["label"],
            reason=result_data["reason"],
            is_high_risk=result_data["is_high_risk"],
            engine_version=result_data["engine_version"],
        )

        upsert_detection_incident(
            detection=result,
            risk_level=result_data["risk_level"],
            anomaly_family=result_data["anomaly_family"],
            reason=result_data["reason"],
        )

        serializer = DetectionResultSerializer(result)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DetectionTrainView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated(), IsAnalystOrAdmin()]

    def post(self, request):
        try:
            bundle = train_from_events()
        except DetectionModelNotReady as exc:
            return Response(
                {
                    "detail": str(exc),
                    "required_rows": MIN_TRAINING_ROWS,
                    "available_rows": TrafficEvent.objects.count(),
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "detail": "Detection model trained successfully.",
                "engine_version": bundle["engine_version"],
                "training_rows": bundle["training_rows"],
                "score_threshold": bundle["score_threshold"],
                "model_path": str(bundle.get("model_path", "")) or None,
            },
            status=status.HTTP_200_OK,
        )
