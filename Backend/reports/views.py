from django.db.models import Count
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from detection.models import DetectionResult
from events.models import TrafficEvent
from incidents.models import Evidence, Incident
from response_engine.models import ResponseAction


class DashboardSummaryView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated()]

    def get(self, request):
        summary = {
            "events_total": TrafficEvent.objects.count(),
            "high_risk_detections": DetectionResult.objects.filter(is_high_risk=True).count(),
            "open_incidents": Incident.objects.filter(status=Incident.Status.OPEN).count(),
            "isolated_hosts": ResponseAction.objects.filter(action_type=ResponseAction.ActionType.ISOLATE_HOST).values("target_value").exclude(target_value="").distinct().count(),
            "response_actions_total": ResponseAction.objects.count(),
            "evidence_total": Evidence.objects.count(),
        }

        summary["incident_counts_by_status"] = list(
            Incident.objects.values("status").annotate(count=Count("id")).order_by("status")
        )
        summary["incident_counts_by_severity"] = list(
            Incident.objects.values("severity").annotate(count=Count("id")).order_by("severity")
        )
        summary["high_risk_detection_rate"] = round(
            summary["high_risk_detections"] / summary["events_total"], 2
        ) if summary["events_total"] else 0.0

        return Response(summary)
