from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any

from django.db import transaction

from detection.models import DetectionResult
from incidents.models import Incident

from .models import ResponseAction


RESPONSE_POLICY_RULE = "risk-context-containment-v1"
HIGH_RISK_LEVELS = {Incident.Severity.HIGH, Incident.Severity.CRITICAL}
SENSITIVE_PORTS = {22, 23, 25, 53, 80, 110, 143, 389, 443, 445, 587, 993, 995, 1433, 3306, 3389, 5432, 8080, 8443, 4444}


@dataclass(frozen=True)
class PlannedResponseAction:
    action_type: str
    target_value: str
    notes: str


def _safe_ip_private(value: Any) -> bool:
    try:
        return ip_address(str(value)).is_private
    except ValueError:
        return False


def _safe_same_subnet_24(source_ip: Any, destination_ip: Any) -> bool:
    try:
        source = ip_address(str(source_ip))
        destination = ip_address(str(destination_ip))
    except ValueError:
        return False

    return source.version == destination.version == 4 and str(source).split(".")[:3] == str(destination).split(".")[:3]


def build_response_context(*, incident: Incident, detection: DetectionResult, risk_level: str, anomaly_family: str, reason: str) -> dict[str, Any]:
    event = detection.event
    source_ip = event.source_ip if event else ""
    destination_ip = event.destination_ip if event else ""
    destination_port = event.destination_port if event else None
    context = {
        "incident_id": incident.id,
        "detection_id": detection.id,
        "risk_level": risk_level,
        "anomaly_family": anomaly_family,
        "reason": reason,
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "destination_port": destination_port,
        "source_private": _safe_ip_private(source_ip),
        "destination_private": _safe_ip_private(destination_ip),
        "same_subnet_24": _safe_same_subnet_24(source_ip, destination_ip),
        "protocol": event.protocol if event else "",
        "control_mode": "controlled",
        "simulation_only": True,
    }
    return context


def _action(action_type: str, target_value: str, notes: str) -> PlannedResponseAction:
    return PlannedResponseAction(action_type=action_type, target_value=target_value, notes=notes)


def select_response_actions(*, risk_level: str, anomaly_family: str, context: dict[str, Any]) -> list[PlannedResponseAction]:
    if risk_level not in HIGH_RISK_LEVELS:
        return []

    source_ip = str(context.get("source_ip") or "")
    destination_ip = str(context.get("destination_ip") or "")
    destination_port = context.get("destination_port")
    source_private = bool(context.get("source_private"))
    destination_private = bool(context.get("destination_private"))
    same_subnet_24 = bool(context.get("same_subnet_24"))

    plan: list[PlannedResponseAction] = []

    if risk_level == Incident.Severity.CRITICAL:
        plan.append(
            _action(
                ResponseAction.ActionType.ISOLATE_HOST,
                source_ip,
                f"Isolate {source_ip or 'the affected host'} because {risk_level} risk was detected.",
            )
        )
        plan.append(
            _action(
                ResponseAction.ActionType.MARK_HOST_COMPROMISED,
                source_ip,
                f"Mark {source_ip or 'the affected host'} as compromised pending analyst review.",
            )
        )

    if anomaly_family == "lateral_movement" or (source_private and destination_private and same_subnet_24):
        plan.append(
            _action(
                ResponseAction.ActionType.CUT_LATERAL_COMMUNICATION,
                source_ip,
                f"Cut lateral communication for {source_ip or 'the internal host'} to prevent spread.",
            )
        )
        plan.append(
            _action(
                ResponseAction.ActionType.LIMIT_TRAFFIC,
                f"{source_ip}->{destination_ip}",
                f"Limit internal traffic between {source_ip or 'source'} and {destination_ip or 'destination'}.",
            )
        )

    if anomaly_family in {"service_probe", "privileged_service_abuse", "dns_tunneling", "exfiltration", "protocol_anomaly"} or int(destination_port or 0) in SENSITIVE_PORTS:
        plan.append(
            _action(
                ResponseAction.ActionType.BLOCK_IP,
                destination_ip,
                f"Block {destination_ip or 'the destination IP'} to stop suspicious external or service traffic.",
            )
        )
        plan.append(
            _action(
                ResponseAction.ActionType.LIMIT_TRAFFIC,
                f"{source_ip}->{destination_ip}",
                f"Limit traffic for the suspicious path {source_ip or 'source'} to {destination_ip or 'destination'}.",
            )
        )

    plan.append(
        _action(
            ResponseAction.ActionType.NOTIFY_ADMIN,
            f"incident:{context.get('incident_id')}",
            f"Notify admin for {risk_level} risk {anomaly_family}.",
        )
    )

    deduped: list[PlannedResponseAction] = []
    seen: set[tuple[str, str]] = set()
    for item in plan:
        marker = (item.action_type, item.target_value)
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(item)

    return deduped


def build_response_decision(*, incident: Incident, detection: DetectionResult, risk_level: str, anomaly_family: str, reason: str) -> dict[str, Any]:
    context = build_response_context(
        incident=incident,
        detection=detection,
        risk_level=risk_level,
        anomaly_family=anomaly_family,
        reason=reason,
    )
    actions = select_response_actions(risk_level=risk_level, anomaly_family=anomaly_family, context=context)

    return {
        "policy_rule": RESPONSE_POLICY_RULE,
        "context": context,
        "actions": [action.__dict__ for action in actions],
    }


@transaction.atomic
def apply_controlled_response_policy(
    *,
    incident: Incident,
    detection: DetectionResult,
    risk_level: str,
    anomaly_family: str,
    reason: str,
    network_executor: Any | None = None,
) -> dict[str, Any]:
    decision = build_response_decision(
        incident=incident,
        detection=detection,
        risk_level=risk_level,
        anomaly_family=anomaly_family,
        reason=reason,
    )

    from incidents.services import record_incident_evidence, record_incident_timeline

    record_incident_evidence(
        incident=incident,
        evidence_type="response_policy",
        description=f"Policy {decision['policy_rule']} selected {len(decision['actions'])} controlled actions for {risk_level} risk.",
        source_ref=decision["policy_rule"],
        payload=decision,
    )
    record_incident_timeline(
        incident=incident,
        event_type="response_policy",
        message=f"Selected {len(decision['actions'])} controlled response actions for {risk_level} risk.",
        source_ref=decision["policy_rule"],
        payload=decision,
    )

    created_actions: list[ResponseAction] = []
    for planned in decision["actions"]:
        action, _created = ResponseAction.objects.update_or_create(
            incident=incident,
            action_type=planned["action_type"],
            target_value=planned["target_value"],
            defaults={
                "notes": planned["notes"],
                "policy_rule": decision["policy_rule"],
                "decision_context": decision["context"],
                "status": ResponseAction.Status.SIMULATED,
                "simulated": True,
                "control_mode": "controlled",
            },
        )
        created_actions.append(action)

        from incidents.services import record_response_action_audit

        record_response_action_audit(action=action, decision=decision, risk_level=risk_level)

    return {
        "decision": decision,
        "actions": created_actions,
    }
