from django.db import models

from incidents.models import Incident


class ResponseAction(models.Model):
    class ActionType(models.TextChoices):
        ALERT = "alert", "Alert"
        NOTIFY_ADMIN = "notify_admin", "Notify Admin"
        ISOLATE_HOST = "isolate_host", "Isolate Host"
        BLOCK_IP = "block_ip", "Block IP"
        LIMIT_TRAFFIC = "limit_traffic", "Limit Traffic"
        CUT_LATERAL_COMMUNICATION = "cut_lateral_communication", "Cut Lateral Communication"
        MARK_HOST_COMPROMISED = "mark_host_compromised", "Mark Host Compromised"
        SUSPEND_USER = "suspend_user", "Suspend User"

    class Status(models.TextChoices):
        SIMULATED = "simulated", "Simulated"
        EXECUTED = "executed", "Executed"
        FAILED = "failed", "Failed"

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="response_actions")
    action_type = models.CharField(max_length=32, choices=ActionType.choices)
    target_value = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    policy_rule = models.CharField(max_length=64, default="manual_controlled_policy")
    decision_context = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SIMULATED)
    simulated = models.BooleanField(default=True)
    control_mode = models.CharField(max_length=32, default="controlled")
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-executed_at",)

    def __str__(self) -> str:
        return f"{self.action_type} for incident {self.incident_id}"
