from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from accounts.permissions import IsOperatorOrAdmin
from .models import TrafficEvent
from .serializers import TrafficEventSerializer


class TrafficEventListCreateView(generics.ListCreateAPIView):
    queryset = TrafficEvent.objects.all()
    serializer_class = TrafficEventSerializer

    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        if self.request.method in {"GET", "HEAD"}:
            return [IsAuthenticated()]

        return [IsAuthenticated(), IsOperatorOrAdmin()]

    def perform_create(self, serializer):
        serializer.save(ingested_by=self.request.user.username)
