from django.db import models

from events.models import TrafficEvent


class DetectionResult(models.Model):
    event = models.ForeignKey(TrafficEvent, null=True, blank=True, on_delete=models.SET_NULL, related_name="detections")
    score = models.FloatField(default=0.0)
    label = models.CharField(max_length=32)
    reason = models.TextField()
    is_high_risk = models.BooleanField(default=False)
    payload_snapshot = models.JSONField(default=dict, blank=True)
    engine_version = models.CharField(max_length=32, default="ml-isoforest-v1")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.label} ({self.score:.2f})"
