from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from accounts.permissions import IsAnalystOrAdmin
from .models import Incident
from .serializers import IncidentSerializer


class IncidentListCreateView(generics.ListCreateAPIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        if self.request.method in {"GET", "HEAD"}:
            return [IsAuthenticated()]

        return [IsAuthenticated(), IsAnalystOrAdmin()]
