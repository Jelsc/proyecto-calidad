from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CurrentUserSerializer


User = get_user_model()


class LoginView(TokenObtainPairView):
    pass


class CurrentUserView(APIView):
    def get_permissions(self):
        if self.request.method == "OPTIONS":
            return [AllowAny()]

        return [IsAuthenticated()]

    def get(self, request):
        user = User.objects.select_related().prefetch_related("groups").get(pk=request.user.pk)
        return Response(CurrentUserSerializer(user).data)
