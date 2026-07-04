from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from accounts.permissions import IsOperatorOrAdmin
from .models import ResponseAction
from .serializers import ResponseActionSerializer
from .services import RESPONSE_POLICY_RULE


def build_response_contract() -> dict[str, object]:
    return {
        "routes": {
            "list_create": "/api/responses/",
        },
        "policy": {
            "rule": RESPONSE_POLICY_RULE,
            "trigger_levels": ["high", "critical"],
            "simulation_only": True,
            "destructive_operations": False,
            "action_types": [
                ResponseAction.ActionType.ALERT,
                ResponseAction.ActionType.NOTIFY_ADMIN,
                ResponseAction.ActionType.ISOLATE_HOST,
                ResponseAction.ActionType.BLOCK_IP,
                ResponseAction.ActionType.LIMIT_TRAFFIC,
                ResponseAction.ActionType.CUT_LATERAL_COMMUNICATION,
                ResponseAction.ActionType.MARK_HOST_COMPROMISED,
                ResponseAction.ActionType.SUSPEND_USER,
            ],
        },
        "audit": {
            "evidence_model": "Evidence",
            "timeline_model": "IncidentTimelineEntry",
            "recording": "automatic",
        },
    }


class ResponseActionListCreateView(generics.ListCreateAPIView):
    queryset = ResponseAction.objects.all()
    serializer_class = ResponseActionSerializer

    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        if self.request.method in {"GET", "HEAD"}:
            return [IsAuthenticated()]

        return [IsAuthenticated(), IsOperatorOrAdmin()]

    def perform_create(self, serializer):
        action = serializer.save(
            status=ResponseAction.Status.SIMULATED,
            simulated=True,
            control_mode="controlled",
            policy_rule="manual_controlled_policy",
            decision_context={"source": "response_engine_api", "simulation_only": True},
        )

        from incidents.services import record_response_action_audit

        record_response_action_audit(
            action=action,
            decision={
                "policy_rule": action.policy_rule,
                "context": action.decision_context,
                "actions": [
                    {
                        "action_type": action.action_type,
                        "target_value": action.target_value,
                        "notes": action.notes,
                    }
                ],
            },
            risk_level="manual",
        )
