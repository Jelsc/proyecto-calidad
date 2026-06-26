from django.db import models

from incidents.models import Incident


class ResponseAction(models.Model):
    class ActionType(models.TextChoices):
        ALERT = "alert", "Alert"
        ISOLATE_HOST = "isolate_host", "Isolate Host"
        BLOCK_IP = "block_ip", "Block IP"
        SUSPEND_USER = "suspend_user", "Suspend User"

    class Status(models.TextChoices):
        SIMULATED = "simulated", "Simulated"
        EXECUTED = "executed", "Executed"
        FAILED = "failed", "Failed"

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="response_actions")
    action_type = models.CharField(max_length=32, choices=ActionType.choices)
    target_value = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SIMULATED)
    simulated = models.BooleanField(default=True)
    control_mode = models.CharField(max_length=32, default="controlled")
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-executed_at",)

    def __str__(self) -> str:
        return f"{self.action_type} for incident {self.incident_id}"
