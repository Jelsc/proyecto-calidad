from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsOperatorOrAdmin
from .models import TrafficEvent
from .serializers import TrafficEventSerializer
from .services import ingest_traffic_events_with_detection


class TrafficEventListCreateView(generics.ListCreateAPIView):
    queryset = TrafficEvent.objects.all()
    serializer_class = TrafficEventSerializer

    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        if self.request.method in {"GET", "HEAD"}:
            return [IsAuthenticated()]

        return [IsAuthenticated(), IsOperatorOrAdmin()]

    def perform_create(self, serializer):
        serializer.save(ingested_by=self.request.user.username)


class TrafficEventIntakeView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated(), IsOperatorOrAdmin()]

    def post(self, request):
        try:
            ingestion_result = ingest_traffic_events_with_detection(request.data, request.user.username)
        except serializers.ValidationError as exc:
            detail = exc.detail
            if isinstance(detail, dict) and "rows" in detail:
                rows = []
                for item in detail["rows"]:
                    index = item.get("index")
                    if isinstance(index, str) and index.isdigit():
                        index = int(index)
                    rows.append({"index": index, "errors": item.get("errors", {})})

                return Response(
                    {
                        "detail": "One or more dataset rows are invalid.",
                        "rows": rows,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "ingested_count": ingestion_result["ingested_count"],
                "detections_created_count": ingestion_result["detections_created_count"],
                "incidents_triggered_count": ingestion_result["incidents_triggered_count"],
                "incident_ids": ingestion_result["incident_ids"],
                "detection_status": ingestion_result["detection_status"],
                "detection_message": ingestion_result["detection_message"],
                "rows": TrafficEventSerializer(ingestion_result["events"], many=True).data,
            },
            status=status.HTTP_201_CREATED,
        )
