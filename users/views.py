from datetime import timezone as dt_timezone

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import TokenBlacklist
from core.permissions import IsAuthenticated
from core.utils.jwt_utils import generate_access_token
from users.models import User
from users.serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class RegisterView(APIView):

    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, jti, expires_at = generate_access_token(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token,
                "expires_at": expires_at,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):

    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        password = serializer.validated_data["password"]

        try:
            user = User.objects.select_related("role").get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": True, "message": "Неверный email или пароль."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"error": True, "message": "Аккаунт деактивирован."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.check_password(password):
            return Response(
                {"error": True, "message": "Неверный email или пароль."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, jti, expires_at = generate_access_token(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token,
                "expires_at": expires_at,
            }
        )


class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        payload = request.auth or {}
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti:
            TokenBlacklist.objects.get_or_create(
                jti=jti,
                defaults={
                    "user_id": request.user.id,
                    "expires_at": timezone.datetime.fromtimestamp(exp, tz=dt_timezone.utc)
                    if exp
                    else timezone.now(),
                },
            )
        return Response({"detail": "Вы вышли из системы."})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])

        payload = request.auth or {}
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti:
            TokenBlacklist.objects.get_or_create(
                jti=jti,
                defaults={
                    "user_id": user.id,
                    "expires_at": timezone.datetime.fromtimestamp(exp, tz=dt_timezone.utc)
                    if exp
                    else timezone.now(),
                },
            )
        return Response(
            {"detail": "Аккаунт деактивирован (мягкое удаление)."},
            status=status.HTTP_200_OK,
        )
