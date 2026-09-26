from django.db import transaction
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    EmailTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .services import delete_account


class RegisterView(generics.CreateAPIView):
    """Self-registration as STUDENT or PARENT (ADMIN can never be self-assigned).
    No email verification yet — that needs an email provider (see POC_READINESS.md)."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"


class RefreshView(TokenRefreshView):
    """Rotates: returns a new access *and* refresh token; the old refresh token is blacklisted."""

    throttle_scope = "auth"


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutView(APIView):
    """POST {refresh}: revokes that refresh token (the short-lived access token simply expires).
    Holding a valid refresh token is the authority to revoke it, so no access token is required —
    the SPA may already have discarded it when it logs out."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "auth"
    serializer_class = LogoutSerializer

    def post(self, request):
        data = LogoutSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            RefreshToken(data.validated_data["refresh"]).blacklist()
        except TokenError:
            pass  # already expired/blacklisted: logging out is still a success
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField()


class MeView(APIView):
    """GET: the signed-in user. DELETE {password}: permanently delete the account and all of the
    learner's data (diary incl. photos, Companion chats, assessments, evidence, engagement)."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "account_delete"
    serializer_class = UserSerializer

    def get_throttles(self):
        # Only deletion is scope-limited; reading /me stays under the global limits.
        return super().get_throttles() if self.request.method == "DELETE" else []

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def delete(self, request):
        data = DeleteAccountSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        if not request.user.check_password(data.validated_data["password"]):
            raise serializers.ValidationError({"password": "Incorrect password."})
        with transaction.atomic():
            delete_account(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
