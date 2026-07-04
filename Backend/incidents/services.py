from __future__ import annotations

from django.db import transaction

from detection.models import DetectionResult

from .models import Evidence, Incident, IncidentTimelineEntry


SEVERITY_ORDER = {
    Incident.Severity.LOW: 0,
    Incident.Severity.MEDIUM: 1,
    Incident.Severity.HIGH: 2,
    Incident.Severity.CRITICAL: 3,
}


def _incident_title(risk_level: str, anomaly_family: str) -> str:
    family = anomaly_family.replace("_", " ").title() if anomaly_family else "Network Anomaly"
    return f"{risk_level.title()} Risk: {family}"


def _max_severity(existing: str, candidate: str) -> str:
    if SEVERITY_ORDER.get(candidate, 0) > SEVERITY_ORDER.get(existing, 0):
        return candidate
    return existing


def record_incident_evidence(*, incident: Incident, evidence_type: str, description: str, source_ref: str = "", payload: dict | None = None) -> Evidence:
    return Evidence.objects.create(
        incident=incident,
        evidence_type=evidence_type,
        description=description,
        source_ref=source_ref,
        payload=payload or {},
    )


def record_incident_timeline(*, incident: Incident, event_type: str, message: str, source_ref: str = "", payload: dict | None = None) -> IncidentTimelineEntry:
    return IncidentTimelineEntry.objects.create(
        incident=incident,
        event_type=event_type,
        message=message,
        source_ref=source_ref,
        payload=payload or {},
    )


def record_response_action_audit(*, action, decision: dict, risk_level: str) -> tuple[Evidence, IncidentTimelineEntry]:
    evidence = record_incident_evidence(
        incident=action.incident,
        evidence_type="response_action",
        description=f"Simulated {action.action_type} action for {action.target_value or 'the affected asset'}.",
        source_ref=f"response_action:{action.id}",
        payload={
            "response_action_id": action.id,
            "action_type": action.action_type,
            "target_value": action.target_value,
            "notes": action.notes,
            "policy_rule": action.policy_rule,
            "decision_context": action.decision_context,
            "risk_level": risk_level,
        },
    )
    timeline = record_incident_timeline(
        incident=action.incident,
        event_type=IncidentTimelineEntry.EventType.RESPONSE_ACTION,
        message=f"Recorded simulated {action.action_type} for {action.target_value or 'the affected asset'}.",
        source_ref=f"response_action:{action.id}",
        payload={
            "response_action_id": action.id,
            "policy_rule": action.policy_rule,
            "decision_context": action.decision_context,
            "decision": decision,
        },
    )
    return evidence, timeline


@transaction.atomic
def upsert_detection_incident(*, detection: DetectionResult, risk_level: str, anomaly_family: str, reason: str):
    if risk_level not in {Incident.Severity.HIGH, Incident.Severity.CRITICAL}:
        return None

    lookup = {"source_event": detection.event} if detection.event_id else {"detection": detection}
    incident, created = Incident.objects.select_for_update().get_or_create(
        **lookup,
        defaults={
            "title": _incident_title(risk_level, anomaly_family),
            "summary": reason,
            "severity": risk_level,
            "status": Incident.Status.OPEN,
            "source_event": detection.event,
            "detection": detection,
        },
    )

    if not created:
        incident.title = _incident_title(risk_level, anomaly_family)
        incident.summary = reason
        incident.severity = _max_severity(incident.severity, risk_level)
        incident.detection = detection
        if detection.event_id:
            incident.source_event = detection.event
        incident.save(update_fields=["title", "summary", "severity", "detection", "source_event", "updated_at"])

    from response_engine.services import apply_controlled_response_policy

    apply_controlled_response_policy(
        incident=incident,
        detection=detection,
        risk_level=risk_level,
        anomaly_family=anomaly_family,
        reason=reason,
    )

    return incident
