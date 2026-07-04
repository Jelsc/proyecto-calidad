from django.db.models import Count, F, Min
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from detection.model_service import ENGINE_VERSION, MIN_TRAINING_ROWS
from detection.models import DetectionResult
from events.models import TrafficEvent
from incidents.models import Evidence, Incident
from response_engine.models import ResponseAction


def _iso(value):
    return value.isoformat() if value else None


def _seconds_between(start, end):
    if not start or not end:
        return None

    return round(max((end - start).total_seconds(), 0.0), 2)


def _average_seconds(values):
    if not values:
        return None

    return round(sum(values) / len(values), 2)


def build_dashboard_contract() -> dict[str, object]:
    return {
        "routes": {"summary": "/api/dashboard/summary/"},
        "workflow": {
            "sections": ["analysis", "response", "history", "model"],
            "summary_fields": [
                "events_analyzed_total",
                "active_alerts_total",
                "open_incidents",
                "suspicious_hosts_total",
                "isolated_hosts_total",
                "action_counts_by_type",
                "detection_latency_seconds",
                "response_latency_seconds",
                "incident_history",
                "model_quality",
            ],
        },
    }


class DashboardSummaryView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated()]

    def get(self, request):
        events_total = TrafficEvent.objects.count()
        events_analyzed_total = DetectionResult.objects.count()
        high_risk_detections = DetectionResult.objects.filter(is_high_risk=True).count()
        open_incidents = Incident.objects.filter(status=Incident.Status.OPEN).count()
        active_alerts_total = Incident.objects.filter(status__in=[Incident.Status.OPEN, Incident.Status.INVESTIGATING]).count()
        response_actions_total = ResponseAction.objects.count()
        evidence_total = Evidence.objects.count()

        suspicious_host_map: dict[str, dict[str, object]] = {}
        for detection in DetectionResult.objects.select_related("event").filter(is_high_risk=True).order_by("-created_at", "-id"):
            source_ip = detection.event.source_ip if detection.event else ""
            if not source_ip:
                continue

            entry = suspicious_host_map.setdefault(source_ip, {"count": 0, "latest_detection_at": None})
            entry["count"] = int(entry["count"]) + 1
            if entry["latest_detection_at"] is None:
                entry["latest_detection_at"] = detection.created_at

        suspicious_hosts = [
            {
                "host": host,
                "detection_count": data["count"],
                "latest_detection_at": _iso(data["latest_detection_at"]),
            }
            for host, data in sorted(suspicious_host_map.items(), key=lambda item: (-int(item[1]["count"]), item[0]))
        ]

        isolated_host_map: dict[str, dict[str, object]] = {}
        for action in ResponseAction.objects.filter(action_type=ResponseAction.ActionType.ISOLATE_HOST).exclude(target_value="").order_by("-executed_at", "-id"):
            entry = isolated_host_map.setdefault(action.target_value, {"count": 0, "latest_action_at": None})
            entry["count"] = int(entry["count"]) + 1
            if entry["latest_action_at"] is None:
                entry["latest_action_at"] = action.executed_at

        isolated_hosts = [
            {
                "host": host,
                "action_count": data["count"],
                "latest_action_at": _iso(data["latest_action_at"]),
            }
            for host, data in sorted(isolated_host_map.items(), key=lambda item: (-int(item[1]["count"]), item[0]))
        ]

        action_counts_by_type = list(
            ResponseAction.objects.values("action_type").annotate(count=Count("id")).order_by("action_type")
        )

        incident_counts_by_status = list(
            Incident.objects.values("status").annotate(count=Count("id")).order_by("status")
        )
        incident_counts_by_severity = list(
            Incident.objects.values("severity").annotate(count=Count("id")).order_by("severity")
        )

        detection_latencies = [
            _seconds_between(detection.event.created_at, detection.created_at)
            for detection in DetectionResult.objects.select_related("event").filter(event__isnull=False).order_by("-created_at", "-id")
            if detection.event and detection.created_at and detection.event.created_at
        ]
        detection_latencies = [item for item in detection_latencies if item is not None]

        incidents = (
            Incident.objects.select_related("detection", "source_event")
            .annotate(
                evidence_count=Count("evidence_items", distinct=True),
                timeline_count=Count("timeline_entries", distinct=True),
                response_action_count=Count("response_actions", distinct=True),
                first_response_at=Min("response_actions__executed_at"),
                detection_created_at=F("detection__created_at"),
                source_event_created_at=F("source_event__created_at"),
            )
            .order_by("-created_at", "-id")
        )

        response_latencies = []
        incident_history = []
        for incident in incidents[:6]:
            detection_latency = _seconds_between(incident.source_event_created_at, incident.detection_created_at)
            response_latency = _seconds_between(incident.created_at, incident.first_response_at)
            if response_latency is not None:
                response_latencies.append(response_latency)

            incident_history.append(
                {
                    "id": incident.id,
                    "title": incident.title,
                    "severity": incident.severity,
                    "status": incident.status,
                    "summary": incident.summary,
                    "created_at": _iso(incident.created_at),
                    "updated_at": _iso(incident.updated_at),
                    "evidence_total": incident.evidence_count,
                    "timeline_total": incident.timeline_count,
                    "response_actions_total": incident.response_action_count,
                    "detection_latency_seconds": detection_latency,
                    "response_latency_seconds": response_latency,
                }
            )

        detection_latency_seconds = {
            "average_seconds": _average_seconds(detection_latencies),
            "latest_seconds": detection_latencies[0] if detection_latencies else None,
            "samples": len(detection_latencies),
        }
        response_latency_seconds = {
            "average_seconds": _average_seconds(response_latencies),
            "latest_seconds": response_latencies[0] if response_latencies else None,
            "samples": len(response_latencies),
        }

        latest_detection = DetectionResult.objects.select_related("event").order_by("-created_at", "-id").first()
        engine_version = latest_detection.engine_version if latest_detection else ENGINE_VERSION
        training_status = "trained" if latest_detection else "ready_to_train" if events_total >= MIN_TRAINING_ROWS else "insufficient_rows"
        training_rows = events_analyzed_total if latest_detection else 0
        trained_at = _iso(latest_detection.created_at) if latest_detection else None

        model_quality = {
            "engine_version": engine_version,
            "latest_detection_engine_version": latest_detection.engine_version if latest_detection else ENGINE_VERSION,
            "training_status": training_status,
            "training_rows": training_rows,
            "trained_at": trained_at,
            "minimum_training_rows": MIN_TRAINING_ROWS,
            "high_risk_detection_rate": round(high_risk_detections / events_analyzed_total, 2) if events_analyzed_total else 0.0,
        }

        summary = {
            "events_total": events_total,
            "events_analyzed_total": events_analyzed_total,
            "high_risk_detections": high_risk_detections,
            "high_risk_detection_rate": model_quality["high_risk_detection_rate"],
            "active_alerts_total": active_alerts_total,
            "open_incidents": open_incidents,
            "suspicious_hosts_total": len(suspicious_hosts),
            "isolated_hosts_total": len(isolated_hosts),
            "response_actions_total": response_actions_total,
            "evidence_total": evidence_total,
            "incident_counts_by_status": incident_counts_by_status,
            "incident_counts_by_severity": incident_counts_by_severity,
            "action_counts_by_type": action_counts_by_type,
            "detection_latency_seconds": detection_latency_seconds,
            "response_latency_seconds": response_latency_seconds,
            "suspicious_hosts": suspicious_hosts,
            "isolated_hosts": isolated_hosts,
            "incident_history": incident_history,
            "model_quality": model_quality,
        }

        summary["workflow"] = {
            "analysis": {
                "events_total": events_total,
                "events_analyzed_total": events_analyzed_total,
                "high_risk_detections": high_risk_detections,
                "high_risk_detection_rate": summary["high_risk_detection_rate"],
                "suspicious_hosts": suspicious_hosts,
                "detection_latency_seconds": detection_latency_seconds,
            },
            "response": {
                "active_alerts_total": active_alerts_total,
                "open_incidents": open_incidents,
                "isolated_hosts": isolated_hosts,
                "action_counts_by_type": action_counts_by_type,
                "response_latency_seconds": response_latency_seconds,
            },
            "history": {
                "incident_counts_by_status": incident_counts_by_status,
                "incident_counts_by_severity": incident_counts_by_severity,
                "incident_history": incident_history,
                "evidence_total": evidence_total,
            },
            "model": model_quality,
        }

        return Response(summary)
