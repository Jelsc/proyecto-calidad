from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from pathlib import Path
from typing import Any

from django.conf import settings
from django.utils import timezone

from events.models import TrafficEvent


ENGINE_VERSION = "ml-isoforest-v1"
MIN_TRAINING_ROWS = 20
MODEL_DIR = Path(settings.BASE_DIR) / "detection" / "artifacts"
MODEL_PATH = MODEL_DIR / "anomaly_model.joblib"

SENSITIVE_PORTS = {22, 23, 25, 53, 80, 110, 143, 389, 443, 445, 587, 993, 995, 1433, 3306, 3389, 5432, 8080, 8443, 4444}
COMMON_PROTOCOLS = ("TCP", "UDP", "ICMP")
FEATURE_NAMES = (
    "source_ip_octet_1",
    "source_ip_octet_2",
    "source_ip_octet_3",
    "source_ip_octet_4",
    "destination_ip_octet_1",
    "destination_ip_octet_2",
    "destination_ip_octet_3",
    "destination_ip_octet_4",
    "source_is_private",
    "destination_is_private",
    "same_private_class",
    "same_subnet_24",
    "protocol_tcp",
    "protocol_udp",
    "protocol_icmp",
    "protocol_other",
    "destination_port",
    "destination_port_is_sensitive",
    "payload_length",
    "payload_word_count",
    "payload_digit_count",
    "payload_uppercase_ratio",
    "payload_whitespace_ratio",
    "metadata_key_count",
    "metadata_numeric_value_count",
    "metadata_string_value_count",
    "metadata_boolean_value_count",
)


class DetectionModelNotReady(RuntimeError):
    pass


@dataclass(frozen=True)
class TrainingSummary:
    rows: int
    score_floor: float
    score_ceiling: float
    score_threshold: float
    trained_at: str


def _joblib():
    import joblib

    return joblib


def _numpy():
    import numpy as np

    return np


def _IsolationForest():
    from sklearn.ensemble import IsolationForest

    return IsolationForest


def _Pipeline():
    from sklearn.pipeline import Pipeline

    return Pipeline


def _StandardScaler():
    from sklearn.preprocessing import StandardScaler

    return StandardScaler


def ensure_model_dir() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _parse_ip(value: Any) -> tuple[list[float], bool, bool, int, int, int, int]:
    try:
        ip = ipaddress.ip_address(str(value))
        if ip.version == 6:
            octets = [float(part) for part in ip.packed[:4]]
        else:
            octets = [float(part) for part in str(ip).split(".")]
        while len(octets) < 4:
            octets.append(0.0)
        return octets[:4], ip.is_private, ip.is_loopback, ip.version, int(ip.packed[0]), int(ip.packed[-1]), int(ip.is_multicast)
    except (ValueError, TypeError):
        return [0.0, 0.0, 0.0, 0.0], False, False, 0, 0, 0, 0


def _coerce_metadata(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _payload_text(payload: dict[str, Any]) -> str:
    return str(payload.get("payload", "") or "")


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload or {})
    metadata = normalized.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    normalized["metadata"] = metadata
    return normalized


def extract_feature_vector(payload: dict[str, Any]) -> tuple[list[float], dict[str, Any]]:
    normalized = _normalize_payload(payload)
    source_octets, source_private, _, _, _, _, _ = _parse_ip(normalized.get("source_ip"))
    destination_octets, destination_private, _, _, _, _, _ = _parse_ip(normalized.get("destination_ip"))

    source_octet_values = [int(part) for part in source_octets]
    destination_octet_values = [int(part) for part in destination_octets]

    protocol = str(normalized.get("protocol", "") or "").upper()
    protocol_flags = [float(protocol == item) for item in COMMON_PROTOCOLS]
    protocol_other = float(bool(protocol) and protocol not in COMMON_PROTOCOLS)

    port = _safe_int(normalized.get("destination_port") or normalized.get("port"))
    payload_text = _payload_text(normalized)
    metadata = _coerce_metadata(normalized.get("metadata"))

    digit_count = sum(char.isdigit() for char in payload_text)
    whitespace_count = sum(char.isspace() for char in payload_text)
    uppercase_count = sum(char.isupper() for char in payload_text)
    text_length = len(payload_text)
    uppercase_ratio = uppercase_count / text_length if text_length else 0.0
    whitespace_ratio = whitespace_count / text_length if text_length else 0.0

    metadata_values = list(metadata.values())
    metadata_numeric_value_count = sum(isinstance(item, (int, float)) and not isinstance(item, bool) for item in metadata_values)
    metadata_string_value_count = sum(isinstance(item, str) for item in metadata_values)
    metadata_boolean_value_count = sum(isinstance(item, bool) for item in metadata_values)

    same_private_class = float(source_private and destination_private)
    same_subnet_24 = 0.0
    try:
        source_ip = ipaddress.ip_address(str(normalized.get("source_ip")))
        destination_ip = ipaddress.ip_address(str(normalized.get("destination_ip")))
        same_subnet_24 = float(
            source_ip.version == destination_ip.version
            and source_ip.version == 4
            and str(source_ip).split(".")[:3] == str(destination_ip).split(".")[:3]
        )
    except ValueError:
        same_subnet_24 = 0.0

    features = [
        *map(float, source_octet_values),
        *map(float, destination_octet_values),
        float(source_private),
        float(destination_private),
        same_private_class,
        same_subnet_24,
        *protocol_flags,
        protocol_other,
        float(port),
        float(port in SENSITIVE_PORTS),
        float(text_length),
        float(len(payload_text.split())),
        float(digit_count),
        float(uppercase_ratio),
        float(whitespace_ratio),
        float(len(metadata)),
        float(metadata_numeric_value_count),
        float(metadata_string_value_count),
        float(metadata_boolean_value_count),
    ]

    feature_summary = {
        "protocol": protocol or "unknown",
        "destination_port": port or None,
        "payload_length": text_length,
        "metadata_key_count": len(metadata),
        "source_private": bool(source_private),
        "destination_private": bool(destination_private),
        "same_subnet_24": bool(same_subnet_24),
    }
    return features, feature_summary


def _build_training_payload(event: TrafficEvent) -> dict[str, Any]:
    return {
        "source_ip": event.source_ip,
        "destination_ip": event.destination_ip,
        "protocol": event.protocol,
        "destination_port": event.destination_port,
        "payload": event.payload,
        "metadata": event.metadata or {},
    }


def _bundle_payload(model, summary: TrainingSummary) -> dict[str, Any]:
    return {
        "engine_version": ENGINE_VERSION,
        "feature_names": FEATURE_NAMES,
        "model": model,
        "score_floor": summary.score_floor,
        "score_ceiling": summary.score_ceiling,
        "score_threshold": summary.score_threshold,
        "training_rows": summary.rows,
        "trained_at": summary.trained_at,
    }


def _load_bundle() -> dict[str, Any] | None:
    if not MODEL_PATH.exists():
        return None
    try:
        bundle = _joblib().load(MODEL_PATH)
        if isinstance(bundle, dict):
            bundle.setdefault("model_path", str(MODEL_PATH))
        return bundle
    except Exception:
        return None


def load_or_train_bundle(force_refresh: bool = False) -> dict[str, Any]:
    if not force_refresh:
        bundle = _load_bundle()
        if bundle is not None:
            return bundle

    return train_from_events()


def train_from_events() -> dict[str, Any]:
    events = list(TrafficEvent.objects.all().only("source_ip", "destination_ip", "protocol", "destination_port", "payload", "metadata"))
    if len(events) < MIN_TRAINING_ROWS:
        raise DetectionModelNotReady(
            f"Anomaly model is not trained yet. Store at least {MIN_TRAINING_ROWS} TrafficEvent rows or POST to /api/detection/train/ after seeding data."
        )

    feature_rows = []
    for event in events:
        features, _ = extract_feature_vector(_build_training_payload(event))
        feature_rows.append(features)

    np = _numpy()
    X = np.asarray(feature_rows, dtype=float)
    pipeline = _Pipeline()(
        [
            ("scaler", _StandardScaler()()),
            (
                "model",
                _IsolationForest()(
                    n_estimators=200,
                    contamination=0.1,
                    random_state=42,
                ),
            ),
        ]
    )
    pipeline.fit(X)

    decision_scores = pipeline.decision_function(X)
    summary = TrainingSummary(
        rows=len(events),
        score_floor=float(np.percentile(decision_scores, 5)),
        score_ceiling=float(np.percentile(decision_scores, 95)),
        score_threshold=float(np.percentile(decision_scores, 10)),
        trained_at=timezone.now().isoformat(),
    )

    bundle = _bundle_payload(pipeline, summary)
    bundle["model_path"] = str(MODEL_PATH)
    ensure_model_dir()
    _joblib().dump(bundle, MODEL_PATH)
    return bundle


def ensure_bundle() -> dict[str, Any]:
    return load_or_train_bundle(force_refresh=False)


def predict(payload: dict[str, Any]) -> dict[str, Any]:
    np = _numpy()
    bundle = ensure_bundle()
    features, feature_summary = extract_feature_vector(payload)
    X = np.asarray([features], dtype=float)
    decision_score = float(bundle["model"].decision_function(X)[0])
    floor = float(bundle.get("score_floor", decision_score - 1.0))
    ceiling = float(bundle.get("score_ceiling", decision_score + 1.0))
    span = max(abs(ceiling - floor), 1e-6)
    risk_score = 1.0 - ((decision_score - floor) / span)
    risk_score = float(np.clip(risk_score, 0.0, 1.0))
    threshold = float(bundle.get("score_threshold", floor))
    is_high_risk = bool(decision_score <= threshold or risk_score >= 0.7)

    if risk_score >= 0.7:
        label = "high_risk"
    elif risk_score >= 0.4:
        label = "medium_risk"
    else:
        label = "low_risk"

    reason = (
        f"IsolationForest anomaly score={decision_score:.4f}; threshold={threshold:.4f}; "
        f"payload_length={feature_summary['payload_length']}; protocol={feature_summary['protocol']}; "
        f"destination_port={feature_summary['destination_port'] or 'n/a'}; metadata_keys={feature_summary['metadata_key_count']}"
    )

    return {
        "score": round(risk_score, 2),
        "label": label,
        "reason": reason,
        "is_high_risk": is_high_risk,
        "engine_version": bundle.get("engine_version", ENGINE_VERSION),
        "model_decision_score": round(decision_score, 4),
        "training_rows": bundle.get("training_rows", 0),
    }
