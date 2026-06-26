from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from accounts.permissions import IsOperatorOrAdmin
from .models import ResponseAction
from .serializers import ResponseActionSerializer


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
        serializer.save(
            status=ResponseAction.Status.SIMULATED,
            simulated=True,
            control_mode="controlled",
        )
