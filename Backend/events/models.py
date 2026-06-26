from django.db import models


class TrafficEvent(models.Model):
    source_ip = models.GenericIPAddressField()
    destination_ip = models.GenericIPAddressField()
    protocol = models.CharField(max_length=16)
    destination_port = models.PositiveIntegerField(null=True, blank=True)
    payload = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ingested_by = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.source_ip} -> {self.destination_ip} ({self.protocol})"
