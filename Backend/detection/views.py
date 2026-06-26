from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAnalystOrAdmin
from events.models import TrafficEvent

from .models import DetectionResult
from .serializers import DetectionResultSerializer
from .model_service import DetectionModelNotReady, MIN_TRAINING_ROWS, predict, train_from_events


def build_detection_payload(request_data: dict, event: TrafficEvent | None = None) -> dict:
    payload: dict = {}

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
