from __future__ import annotations

from typing import Any


RISK_SCALE = {
    "low": [0.0, 0.24],
    "medium": [0.25, 0.49],
    "high": [0.5, 0.74],
    "critical": [0.75, 1.0],
}

RISK_LEVELS = tuple(RISK_SCALE.keys())
SENSITIVE_PORTS = {22, 23, 25, 53, 80, 110, 143, 389, 443, 445, 587, 993, 995, 1433, 3306, 3389, 5432, 8080, 8443, 4444}
COMMON_PROTOCOLS = {"TCP", "UDP", "ICMP"}


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value in {None, ""}:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _level_index(level: str) -> int:
    try:
        return RISK_LEVELS.index(level)
    except ValueError:
        return 0


def _infer_family(feature_summary: dict[str, Any]) -> str:
    protocol = str(feature_summary.get("protocol") or "").upper()
    port = _coerce_int(feature_summary.get("destination_port"), default=0)
    source_private = bool(feature_summary.get("source_private"))
    destination_private = bool(feature_summary.get("destination_private"))
    same_subnet_24 = bool(feature_summary.get("same_subnet_24"))

    if protocol == "UDP" and port == 53:
        return "dns_tunneling"

    if source_private and destination_private and same_subnet_24:
        return "lateral_movement"

    if port in {22, 23, 445, 3389, 1433, 3306, 5432}:
        return "privileged_service_abuse"

    if protocol and protocol not in COMMON_PROTOCOLS:
        return "protocol_anomaly"

    if port in SENSITIVE_PORTS:
        return "service_probe"

    return "network_anomaly"


def _base_level(risk_score: float) -> str:
    if risk_score >= 0.75:
        return "critical"
    if risk_score >= 0.5:
        return "high"
    if risk_score >= 0.25:
        return "medium"
    return "low"


def _context_boost(feature_summary: dict[str, Any]) -> int:
    boost = 0
    port = _coerce_int(feature_summary.get("destination_port"), default=0)
    protocol = str(feature_summary.get("protocol") or "").upper()
    same_private_class = bool(feature_summary.get("same_private_class"))
    same_subnet_24 = bool(feature_summary.get("same_subnet_24"))
    payload_length = _coerce_int(feature_summary.get("payload_length"), default=0)

    if port in SENSITIVE_PORTS:
        boost += 1

    if protocol and protocol not in COMMON_PROTOCOLS and payload_length > 0:
        boost += 1

    if same_private_class and same_subnet_24:
        boost += 1

    return boost


def classify_detection_risk(*, decision_score: float, risk_score: float, feature_summary: dict[str, Any]) -> dict[str, Any]:
    normalized_score = max(0.0, min(1.0, float(risk_score)))
    base_level = _base_level(normalized_score)
    boosted_index = min(len(RISK_LEVELS) - 1, _level_index(base_level) + _context_boost(feature_summary))
    risk_level = RISK_LEVELS[boosted_index]
    anomaly_family = _infer_family(feature_summary)
    should_alert = risk_level in {"high", "critical"}

    port = _coerce_int(feature_summary.get("destination_port"), default=0)
    protocol = str(feature_summary.get("protocol") or "unknown").upper()
    reason = (
        f"family={anomaly_family}; ml_score={decision_score:.4f}; normalized_risk={normalized_score:.2f}; "
        f"risk_level={risk_level}; protocol={protocol}; destination_port={port or 'n/a'}; "
        f"same_subnet_24={bool(feature_summary.get('same_subnet_24'))}"
    )

    return {
        "risk_level": risk_level,
        "anomaly_family": anomaly_family,
        "reason": reason,
        "should_alert": should_alert,
    }
