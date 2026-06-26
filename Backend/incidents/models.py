from django.db import models

from detection.models import DetectionResult
from events.models import TrafficEvent


class Incident(models.Model):
    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        INVESTIGATING = "investigating", "Investigating"
        CONTAINED = "contained", "Contained"
        RESOLVED = "resolved", "Resolved"

    title = models.CharField(max_length=128)
    summary = models.TextField(blank=True)
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    source_event = models.ForeignKey(TrafficEvent, null=True, blank=True, on_delete=models.SET_NULL, related_name="incidents")
    detection = models.ForeignKey(DetectionResult, null=True, blank=True, on_delete=models.SET_NULL, related_name="incidents")
    assigned_to = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title


class Evidence(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="evidence_items")
    evidence_type = models.CharField(max_length=64)
    description = models.TextField()
    source_ref = models.CharField(max_length=128, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-collected_at",)

    def __str__(self) -> str:
        return f"{self.evidence_type} for incident {self.incident_id}"
